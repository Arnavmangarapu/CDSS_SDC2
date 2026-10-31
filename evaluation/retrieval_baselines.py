"""Compare BM25, dense and dense+reranker on one explicitly judged pinned corpus.

Dense models must already be cached and use commit-pinned revisions. No downloads,
database mutation, LLM calls, or independent relevance labels are performed here.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import time

from evaluation.retrieval_metrics import score_query
from ingestion.authoritative_sources import build_passages, load_manifest, DEFAULT_MANIFEST


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.casefold())


def bm25(query, corpus):
    tokens = {key: tokenize(text) for key, text in corpus.items()}
    df = Counter(term for words in tokens.values() for term in set(words))
    average = sum(map(len, tokens.values())) / len(tokens)
    scores = {}
    for key, words in tokens.items():
        tf = Counter(words)
        score = 0
        for term in set(tokenize(query)):
            frequency = tf[term]
            idf = math.log(1 + (len(tokens) - df[term] + .5) / (df[term] + .5))
            denominator = frequency + 1.2 * (1 - .75 + .75 * len(words) / (average or 1))
            score += idf * frequency * 2.2 / denominator
        scores[key] = score
    return sorted(scores, key=lambda key: (-scores[key], key))


def judged_metrics(ordered, query, ks):
    grades = query["grades"]
    complete = query.get("judgments_complete") is True
    direct = {key for key, grade in grades.items() if grade == 2}
    result = {}
    for k in ks:
        top = ordered[:k]
        unjudged = [key for key in top if key not in grades] if not complete else []
        if unjudged:
            result[str(k)] = {"precision": None, "mrr": None, "recall": None, "ndcg": None,
                              "unjudged_count": len(unjudged)}
            continue
        found = len(direct & set(top))
        first = next((i for i, key in enumerate(top, 1) if key in direct), None)
        positive = {key: g for key, g in grades.items() if g > 0}
        ndcg = None
        if direct and complete:
            ndcg = score_query(top, positive, {key: [key] for key in direct}, [k])["at_k"][str(k)]["ndcg"]
        result[str(k)] = {"precision": found / k, "mrr": 1 / first if first else 0,
                          "recall": found / len(direct) if complete and direct else None,
                          "ndcg": ndcg, "unjudged_count": 0}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--methods", nargs="+", choices=("bm25", "dense", "dense_reranked"), default=["bm25"])
    parser.add_argument("--embedder-revision", help="40-character Hugging Face commit, required for dense methods")
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; use a new version")
    dataset = json.loads(args.queries.read_text()); queries = dataset["queries"]
    if dataset.get("evidence_role") == "held_out":
        if not args.protocol:
            parser.error("Held-out retrieval requires a frozen independently reviewed protocol")
        from evaluation.freeze import validate_protocol
        protocol = validate_protocol(args.protocol, args.queries, require_review=True)
        if protocol.get("embedder_revision") != args.embedder_revision or protocol.get("methods") != args.methods:
            parser.error("Retrieval models/methods differ from the frozen protocol")
    pinned = [p for entries in build_passages(load_manifest()).values() for p, _ in entries]
    corpus = {p.id: p.passage for p in pinned}
    if not queries or len({q["query_id"] for q in queries}) != len(queries):
        parser.error("Unique nonempty queries required")
    for q in queries:
        if not q.get("query") or not isinstance(q.get("grades"), dict) or not set(q["grades"]) <= corpus.keys():
            parser.error("Queries require text and grades keyed to pinned corpus IDs")
        if any(type(g) is not int or g not in (0, 1, 2) for g in q["grades"].values()):
            parser.error("Grades must be 0, 1 or 2")
    encoder = reranker = vectors = None
    keys = sorted(corpus)
    if set(args.methods) - {"bm25"}:
        if not args.embedder_revision or not re.fullmatch(r"[0-9a-f]{40}", args.embedder_revision):
            parser.error("Commit-pin the cached embedder with --embedder-revision")
        from sentence_transformers import SentenceTransformer, CrossEncoder
        from backend.config import settings
        encoder = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO", revision=args.embedder_revision,
                                      local_files_only=True)
        vectors = encoder.encode([corpus[key] for key in keys], normalize_embeddings=True)
        if "dense_reranked" in args.methods:
            reranker = CrossEncoder(settings.VECTOR_RERANKER_MODEL, revision=settings.VECTOR_RERANKER_REVISION,
                                   local_files_only=True, max_length=512,
                                   cache_folder=str(Path(__file__).resolve().parents[1] / "datasets/models"))
    records = []
    for query in queries:
        dense = None
        for method in args.methods:
            start = time.perf_counter()
            if method == "bm25":
                ordered = bm25(query["query"], corpus)
            else:
                # Include embedding and search in each method's wall time; do not reuse
                # a cached dense ranking to make reranked retrieval appear faster.
                vector = encoder.encode(query["query"], normalize_embeddings=True)
                similarity = vectors @ vector
                dense = sorted(range(len(keys)), key=lambda i: (-float(similarity[i]), keys[i]))
                ordered = [keys[i] for i in dense]
                if method == "dense_reranked":
                    candidates = ordered[:20]
                    scores = reranker.predict([(query["query"], corpus[key]) for key in candidates], show_progress_bar=False)
                    ordered = [key for _, key in sorted(zip(scores, candidates), key=lambda pair: (-float(pair[0]), pair[1]))]
            records.append({"query_id": query["query_id"], "method": method,
                            "ordered_source_ids": ordered[:10],
                            "retrieval_wall_ms": round((time.perf_counter() - start) * 1000, 3),
                            "metrics": judged_metrics(ordered, query, [1, 5, 10])})
    result = {"clinical_validation": False, "evidence_role": dataset.get("evidence_role", "development"),
              "annotation_status": dataset.get("annotation_status", "Unverified developer labels"),
              "query_sha256": hashlib.sha256(args.queries.read_bytes()).hexdigest(),
              "source_manifest_sha256": hashlib.sha256(DEFAULT_MANIFEST.read_bytes()).hexdigest(),
              "corpus_count": len(corpus), "embedder_revision": args.embedder_revision,
              "scope": "Offline ranking over the declared pinned corpus, not end-to-end generation or clinical applicability",
              "query_count": len(queries), "per_query": records, "aggregate": {}}
    for method in args.methods:
        result["aggregate"][method] = {}
        for k in (1, 5, 10):
            metrics = {}
            for name in ("precision", "mrr", "recall", "ndcg"):
                values = [r["metrics"][str(k)][name] for r in records if r["method"] == method]
                metrics[name] = {"value": sum(values) / len(values) if all(v is not None for v in values) else None,
                                 "available_queries": sum(v is not None for v in values), "planned_queries": len(queries)}
            result["aggregate"][method][str(k)] = metrics
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
