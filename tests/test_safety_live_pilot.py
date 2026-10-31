from types import SimpleNamespace
import pytest
from evaluation.safety_live_pilot import observe_extraction, rule_filter, summarize, extraction_checks
from backend.schemas.patient import PatientContext
from evaluation.safety_v2 import OFFLINE


def test_extraction_tap_observes_without_altering_or_leaking_state():
    raw = {'medications': ['simvastatin']}
    class LLM:
        def generate_json(self, prompt, system): return raw
        def response_trace(self): return {'returned_model_version': 'test'}
    original = LLM()
    class Clarifier:
        llm = original
        def process(self, text):
            parsed = self.llm.generate_json('unchanged prompt', 'unchanged system')
            parsed['medications'].append('mutation after observation')
            return PatientContext(raw_input=text)
    c = Clarifier()
    context, observed, trace = observe_extraction(c, 'fixture')
    assert observed == {'medications': ['simvastatin']}
    assert c.llm is original and trace['returned_model_version'] == 'test'


def test_extraction_tap_restores_on_failure():
    original = object()
    class Clarifier:
        llm = original
        def process(self, text): raise ValueError('fixture')
    c = Clarifier()
    with pytest.raises(ValueError): observe_extraction(c, 'fixture')
    assert c.llm is original


def test_rule_filter_reuses_predictions_and_never_invents_missed_warning():
    a = {'case_id': 'a', 'status': 'ok', 'actual_warning_types': ['amlodipine_allergy'],
         'actual_supported_warning_types': ['amlodipine_allergy']}
    b = {'case_id': 'a', 'status': 'ok', 'actual_warning_types': ['allergy_status_unconfirmed'],
         'actual_supported_warning_types': []}
    r = rule_filter(a,b)
    assert r['actual_warning_types'] == [] and r['actual_supported_warning_types'] == []
    assert rule_filter(a, {'status': 'error'})['status'] == 'error'


def test_raw_extraction_cannot_claim_missing_status_fields_and_checks_quotes():
    case = {'case_text': 'Simvastatin stopped.', 'structured_facts': {
        'medication_statements': [{'name': 'simvastatin', 'status': 'stopped'}],
        'allergies': [], 'allergy_status': 'unknown', 'medication_list_status': 'reported'}}
    raw = {'medication_statements': [{'name': 'simvastatin', 'status': 'current', 'source_phrase': 'takes simvastatin'}],
           'allergy_statements': []}
    r = extraction_checks(case, raw, PatientContext(raw_input=case['case_text']))
    assert not r['raw_current_medications_match'] and not r['raw_medication_name_status_match']
    assert r['raw_emitted_source_phrases'] == 1 and r['raw_exact_source_phrases'] == 0
    assert 'raw_allergy_status_match' not in r


def test_all_planned_failures_count_and_empty_support_is_not_success():
    case = {'case_id': 'a', 'expected_warning_types': ['amlodipine_allergy'],
            'expected_supported_warning_types': ['amlodipine_allergy']}
    from evaluation.safety_live_pilot import MODES
    rows = [{'case_id': 'a', 'mode': m, 'status': 'error'} for m in MODES]
    r = summarize([case], rows, [])
    assert r['modes']['llm_only']['exact_case_decisions']['value'] == 0
    assert r['modes']['llm_only']['useful_supported_warning_recall']['value'] == 0
    assert r['extraction']['merged_allergy_status_match']['planned'] == 1
    assert r['extraction']['merged_allergy_status_match']['correct'] == 0
