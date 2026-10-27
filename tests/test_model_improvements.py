"""Regression cases for measured ingestion, linking, safety and output failures."""
import json

import pytest

from backend.agents.fusion import ClinicalFusion
from backend.schemas.patient import PatientContext
from backend.services.entity_linker import EntityLinker
from backend.services.llm_fallback import LLMFallback
from backend.services.patient_fact_extractor import extract_safety_facts
from ingestion.populate_neo4j import canonical_edge, node_record
from ingestion.populate_qdrant import chunk_text


def row():
    return {'relation':'disease_phenotype_positive',
        'x_index':'10','x_id':'9830','x_type':'disease','x_name':'Example disease','x_source':'MONDO',
        'y_index':'20','y_id':'1250','y_type':'effect/phenotype','y_name':'Seizure','y_source':'HPO'}


def test_raw_vocabulary_id_collision_does_not_merge_distinct_nodes():
    disease=row();protein={**disease,'x_index':'30','x_type':'gene/protein','x_source':'NCBI'}
    assert node_record(disease,'x')['id']==node_record(protein,'x')['id']
    assert node_record(disease,'x')['uid']!=node_record(protein,'x')['uid']
    assert node_record(disease,'y')['ontology_id']=='HP:0001250'


def test_reverse_primekg_edges_are_one_canonical_edge_and_negative_is_separate():
    direct=row()
    reverse={**direct,**{f'x_{k}':direct[f'y_{k}'] for k in ('index','id','type','name','source')},
                      **{f'y_{k}':direct[f'x_{k}'] for k in ('index','id','type','name','source')}}
    assert canonical_edge(direct)==canonical_edge(reverse)
    negative=canonical_edge({**direct,'relation':'disease_phenotype_negative'})
    assert negative[0]=='PHENOTYPE_ABSENT_IN_DISEASE'
    assert negative[0]!=canonical_edge(direct)[0]


def test_linking_resolves_homonyms_within_the_requested_entity_type():
    linker=EntityLinker({'shared name':[
        {'id':'MONDO:1','source':'MONDO','name':'A disease'},
        {'id':'HP:1','source':'HPO','name':'A phenotype'},
        {'id':'DB1','source':'DRUG','name':'A medicine'}]})
    assert linker.link('shared name','symptom').ontology_id=='HP:1'
    assert linker.link('shared name','condition').ontology_id=='MONDO:1'
    assert linker.link('shared name','medication').ontology_id=='DB1'
    assert linker.link('shared names','symptom').ontology_source=='HPO'


@pytest.mark.parametrize('text',[
    'No allergy history was recorded.', 'No allergy history is available.',
    'Unknown allergy history.', 'Uncertain allergy history.',
    'Drug allergy status is undocumented.', 'Allergy status has not been assessed.',
    'Denies penicillin allergy.', 'Not allergic to amlodipine.',
])
def test_missing_or_negated_allergy_history_does_not_create_a_substance_allergy(text):
    facts=extract_safety_facts(text,{})
    assert facts['allergy_status']=='unknown'
    assert facts['allergy_mentions']==[]
    assert 'Allergy status not supplied' in facts['missing_information']


def test_real_allergy_after_an_unknown_history_is_preserved():
    facts=extract_safety_facts('No allergy history was recorded. Allergic to amlodipine.',{})
    assert facts['allergy_status']=='allergies_reported'
    assert facts['allergy_mentions'][0][0]=='amlodipine'
    assert extract_safety_facts('No known drug allergies.',{})['allergy_status']=='no_known_allergies'


def test_gemini_schema_is_transmitted_and_does_not_leak_to_later_requests(monkeypatch):
    payloads=[]
    def post(url,headers,payload):
        payloads.append(payload)
        return {'candidates':[{'content':{'parts':[{'text':'{"ok":true}'}]}}]}
    llm=LLMFallback();monkeypatch.setattr(llm,'_post',post)
    llm.providers=(('Gemini Flash Lite','test',llm._gemini_lite),)
    schema={'type':'object','properties':{'ok':{'type':'boolean'}},'required':['ok']}
    assert llm.generate_json('p','s',response_schema=schema)=={'ok':True}
    assert payloads[-1]['generationConfig']['responseJsonSchema']==schema
    assert llm.generate_json('p','s')=={'ok':True}
    assert 'responseJsonSchema' not in payloads[-1]['generationConfig']
    assert set(ClinicalFusion.response_schema()['required'])=={
        'diagnoses','diagnostic_claims','investigations_to_consider','treatment_options_if_confirmed','missing_information'}


def test_reasoning_parts_are_not_concatenated_into_json(monkeypatch):
    llm=LLMFallback()
    monkeypatch.setattr(llm,'_post',lambda *args: {'candidates':[{'content':{'parts':[
        {'text':'Analysis which is not JSON','thought':True},{'text':'{"ok":true}'}]}}]})
    llm.providers=(('Gemini Flash Lite','test',llm._gemini_lite),)
    assert llm.generate_json('p','s')=={'ok':True}


def test_complete_text_chunking_preserves_the_end_of_a_document():
    words=[f'w{i}' for i in range(1000)]
    chunks=chunk_text(' '.join(words))
    assert chunks[-1].split()[-1]=='w999'
    assert chunks[0].split()[-20:]==chunks[1].split()[:20]
    with pytest.raises(ValueError):chunk_text('x',chunk_size=20,overlap=20)


def test_normal_bp_in_unrelated_case_does_not_pull_hypertension_sources():
    from backend.services.vector_retriever import VectorRetriever
    retriever=VectorRetriever.__new__(VectorRetriever)
    retriever.retrieve_authoritative_query=lambda *args: pytest.fail('Out-of-scope sources were requested')
    assert retriever.retrieve_authoritative(PatientContext(raw_input='Fever and cough. BP 110/70.'))==([],[])
