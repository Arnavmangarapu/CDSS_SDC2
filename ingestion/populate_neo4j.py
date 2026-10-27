"""Stream clinical PrimeKG relations into a consistent, non-destructive schema."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

from backend.config import settings

RELATIONS = {
    'disease_phenotype_positive': 'PHENOTYPE_SUPPORTS_DISEASE',
    'disease_phenotype_negative': 'PHENOTYPE_ABSENT_IN_DISEASE',
    'contraindication': 'DRUG_CONTRAINDICATED_FOR',
    'indication': 'DRUG_INDICATED_FOR',
}


def node_record(row, side):
    index, source, raw_id = (str(row[f'{side}_{k}']) for k in ('index', 'source', 'id'))
    ontology_id = f'HP:{int(raw_id):07d}' if source == 'HPO' and raw_id.isdigit() else raw_id
    return {'uid': f'PrimeKG:{index}', 'node_index': index, 'id': raw_id,
            'ontology_id': ontology_id, 'source': source,
            'name': str(row[f'{side}_name']).strip().lower(), 'type': str(row[f'{side}_type'])}


def canonical_edge(row):
    relation = row['relation']
    if relation not in RELATIONS:
        return None
    x, y = node_record(row, 'x'), node_record(row, 'y')
    source_type = 'effect/phenotype' if relation.startswith('disease_phenotype') else 'drug'
    if x['type'] == 'disease' and y['type'] == source_type:
        x, y = y, x
    if x['type'] != source_type or y['type'] != 'disease':
        raise ValueError(f'Unexpected endpoints for {relation}')
    return RELATIONS[relation], {'x': x, 'y': y}


def populate(path, driver, *, chunk_size=100000, batch_size=2000):
    counts = {}
    columns = ['relation'] + [f'{side}_{field}' for side in ('x', 'y')
                              for field in ('index', 'id', 'type', 'name', 'source')]
    with driver.session() as session:
        session.run('CREATE CONSTRAINT clinical_entity_uid IF NOT EXISTS '
                    'FOR (n:ClinicalEntity) REQUIRE n.uid IS UNIQUE').consume()
        for field in ('name', 'ontology_id'):
            session.run(f'CREATE INDEX clinical_entity_{field} IF NOT EXISTS '
                        f'FOR (n:ClinicalEntity) ON (n.{field})').consume()
        session.run('CALL db.awaitIndexes(120)').consume()
        for chunk in pd.read_csv(path, dtype=str, usecols=columns, chunksize=chunk_size, keep_default_na=False):
            batches = {}
            for row in chunk[chunk.relation.isin(RELATIONS)].to_dict('records'):
                relation, edge = canonical_edge(row)
                batches.setdefault(relation, {})[(edge['x']['uid'], edge['y']['uid'])] = edge
            for relation, unique in batches.items():
                records = list(unique.values())
                for offset in range(0, len(records), batch_size):
                    batch = records[offset:offset + batch_size]
                    def write(tx, items=batch, edge_type=relation):
                        tx.run(f'''UNWIND $rows AS row
                            MERGE (x:ClinicalEntity {{uid:row.x.uid}}) SET x += row.x
                            MERGE (y:ClinicalEntity {{uid:row.y.uid}}) SET y += row.y
                            MERGE (x)-[:{edge_type}]->(y)''', rows=items).consume()
                    session.execute_write(write)
                counts[relation] = counts.get(relation, 0) + len(records)
            if batches:
                print(json.dumps({'processed_selected_rows': counts}), flush=True)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(settings.KG_PATH))
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    if args.manifest.exists():
        parser.error('Use a new manifest path')
    with GraphDatabase.driver(settings.NEO4J_URI,
                              auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)) as driver:
        driver.verify_connectivity()
        counts = populate(args.input, driver)
        with driver.session() as session:
            actual = session.run('MATCH (:ClinicalEntity)-[r]->(:ClinicalEntity) '
                                 'RETURN type(r) AS relation,count(*) AS count ORDER BY relation').data()
    with args.input.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps({'input_sha256': digest, 'schema': 'ClinicalEntity-v1',
                                      'processed_rows': counts, 'stored_relationships': actual}, indent=2) + '\n')
    print(json.dumps(actual), flush=True)


if __name__ == '__main__':
    main()
