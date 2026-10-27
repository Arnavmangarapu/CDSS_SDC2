"""Bounded phenotype/disease retrieval with separate negative associations."""
from neo4j import GraphDatabase

from backend.config import settings
from backend.schemas.patient import PatientContext
from backend.schemas.retrieval import GraphPath, GraphRetrievalResult


class GraphRetriever:
    def __init__(self, kg_path: str):
        self.driver = GraphDatabase.driver(settings.NEO4J_URI,
                                          auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
        self.is_ready = True

    def retrieve(self, context: PatientContext) -> GraphRetrievalResult:
        if not self.is_ready:
            return GraphRetrievalResult(candidate_diseases=[], paths=[], limitations=['Graph unavailable'])
        names = sorted({name.strip().lower() for s in context.symptoms
                        for name in (s.normalized_name, s.text) if name})
        ids = sorted({s.ontology_id for s in context.symptoms
                      if s.ontology_source == 'HPO' and s.ontology_id})
        drugs = sorted({(d.normalized_name or d.text).strip().lower() for d in context.medications})
        candidates, paths, contraindications = [], [], []
        with self.driver.session() as session:
            if names or ids:
                records = session.run('''
                    MATCH (s:ClinicalEntity {type:'effect/phenotype'})-[r]->(d:ClinicalEntity {type:'disease'})
                    WHERE (s.ontology_id IN $ids OR s.name IN $names)
                      AND type(r) IN ['PHENOTYPE_SUPPORTS_DISEASE','PHENOTYPE_ABSENT_IN_DISEASE']
                    WITH d, collect(DISTINCT {phenotype:s.name, phenotype_id:s.ontology_id,
                                             relation:type(r)}) AS evidence
                    WITH d, evidence,
                         size([e IN evidence WHERE e.relation='PHENOTYPE_SUPPORTS_DISEASE']) AS positive,
                         size([e IN evidence WHERE e.relation='PHENOTYPE_ABSENT_IN_DISEASE']) AS negative
                    WHERE positive > 0
                    RETURN d.name AS name,d.uid AS id,positive,negative,evidence
                    ORDER BY positive-negative DESC,positive DESC,name LIMIT 10
                ''', names=names, ids=ids)
                for record in records:
                    candidates.append({'name': record['name'], 'id': record['id'],
                        'score': float(record['positive'] - record['negative']),
                        'evidence_count': record['positive'], 'contradiction_count': record['negative']})
                    for edge in record['evidence']:
                        paths.append(GraphPath(nodes=[{'name': edge['phenotype'], 'id': edge['phenotype_id'],
                                                        'type': 'effect/phenotype'},
                                                       {'name': record['name'], 'id': record['id'], 'type': 'disease'}],
                                               relationships=[edge['relation']],
                                               score=1.0 if edge['relation'] == 'PHENOTYPE_SUPPORTS_DISEASE' else -1.0))
            if drugs:
                contraindications = session.run('''
                    MATCH (drug:ClinicalEntity {type:'drug'})-[:DRUG_CONTRAINDICATED_FOR]->(d:ClinicalEntity {type:'disease'})
                    WHERE drug.name IN $drugs
                    RETURN drug.name AS drug,d.name AS disease ORDER BY drug,disease LIMIT 100
                ''', drugs=drugs).data()
        return GraphRetrievalResult(candidate_diseases=candidates, paths=paths,
            contraindications=contraindications, drug_interactions=[],
            limitations=['Graph associations are candidate signals, not diagnostic probabilities or verified claims.'])
