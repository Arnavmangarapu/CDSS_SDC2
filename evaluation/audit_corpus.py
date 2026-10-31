"""Read-only inventory, content fingerprints and obvious QA leakage checks.

Reports contain hashes/point IDs, never source text, credentials or vectors.
Exact matching does not rule out partial, paraphrased or provider-training leakage.
"""

import argparse
import hashlib
import json
from pathlib import Path

from backend.config import settings


def normalize(text):
    return " ".join(text.casefold().split())


def payload_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from payload_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from payload_strings(item)


def qa_keys(value):
    suspicious = {"question", "answer", "answer_idx", "gold", "explanation", "long_answer", "final_decision"}
    if isinstance(value, dict):
        return {k for k in value if k.casefold() in suspicious} | set().union(
            *(qa_keys(v) for v in value.values()), set())
    if isinstance(value, list):
        return set().union(*(qa_keys(v) for v in value), set())
    return set()


def snapshot(cases):
    from qdrant_client import QdrantClient
    names = [settings.VECTOR_COLLECTION_TEXTBOOKS, settings.VECTOR_COLLECTION_GUIDELINES,
             settings.VECTOR_COLLECTION_DRUG_LABELS]
    case_texts = [(c["case_id"], normalize(c["case_text"])) for c in cases if len(c.get("case_text", "")) >= 100]
    client = QdrantClient(settings.QDRANT_URL, timeout=5, check_compatibility=False)
    collections = {}
    try:
        for name in names:
            config = client.get_collection(name).config.params.vectors
            dimensions = {k: v.size for k, v in config.items()} if isinstance(config, dict) else {"default": config.size}
            point_hashes, findings = [], []
            offset = None
            while True:
                points, offset = client.scroll(name, limit=100, offset=offset, with_payload=True, with_vectors=True)
                for point in points:
                    payload = point.payload or {}
                    keys = qa_keys(payload)
                    texts = [normalize(s) for s in payload_strings(payload)]
                    leaked = [cid for cid, text in case_texts if any(text in s for s in texts)]
                    if keys or leaked:
                        findings.append({"point_id": str(point.id), "qa_payload_keys": sorted(keys),
                                         "exact_case_ids": leaked})
                    content = {"id": str(point.id), "payload": payload, "vector": point.vector}
                    point_hashes.append(hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest())
                if offset is None:
                    break
            collections[name] = {"point_count": len(point_hashes), "dimensions": dimensions,
                                 "payload_vector_sha256": hashlib.sha256("\n".join(sorted(point_hashes)).encode()).hexdigest(),
                                 "leakage_findings": findings}
    finally:
        client.close()
    from neo4j import GraphDatabase
    with GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                              connection_timeout=5) as driver:
        with driver.session() as session:
            nodes = session.execute_read(lambda tx: tx.run("MATCH (n:ClinicalEntity) RETURN count(n) AS n").single()["n"])
            relations = session.execute_read(lambda tx: tx.run(
                "MATCH (:ClinicalEntity)-[r]->(:ClinicalEntity) RETURN type(r) AS relation,count(r) AS n ORDER BY relation").data())
    return {"status": "complete", "collections": collections,
            "graph": {"clinical_nodes": nodes, "relationships": relations},
            "clear_of_detected_qa_leakage": not any(c["leakage_findings"] for c in collections.values()),
            "dimensions_match_768": all(set(c["dimensions"].values()) == {768} for c in collections.values()),
            "limitations": ["Exact long-stem and structured-QA-key checks only; partial/paraphrase leakage and model pretraining are not certified absent",
                            "Qdrant fingerprints include stored vectors and payloads; graph snapshot records inventory counts, not every edge"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; preserve previous inventory")
    cases = json.loads(args.cases.read_text())["cases"]
    result = snapshot(cases)
    result["cases_sha256"] = hashlib.sha256(args.cases.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
