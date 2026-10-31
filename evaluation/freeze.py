"""Freeze code/protocol/data hashes before evaluation; never manufactures review."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_configuration():
    from backend.config import settings
    return {name: getattr(settings, name) for name in (
        "VECTOR_COLLECTION_TEXTBOOKS", "VECTOR_COLLECTION_GUIDELINES", "VECTOR_COLLECTION_DRUG_LABELS",
        "VECTOR_RERANKER_MODEL", "VECTOR_RERANKER_REVISION",
        "VECTOR_EMBEDDER_MODEL", "VECTOR_EMBEDDER_REVISION")}


def code_hashes():
    tracked = subprocess.check_output(["git", "ls-files", "-z", "backend", "evaluation", "ingestion",
                                       "requirements.txt"], cwd=ROOT).decode().split("\0")
    return {p: digest(ROOT / p) for p in tracked if p and (ROOT / p).is_file()}


def require_reviewed_cases(cases, draft):
    review = draft.get("independent_review", {})
    if not review.get("case_author_independent") or not review.get("ratings_path"):
        raise ValueError("Independent case authorship and actual reviewer ratings are required")
    path = ROOT / review["ratings_path"]
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    index_info = None
    if review.get("private_index_path"):
        index_path = ROOT / review["private_index_path"]
        index_rows = [json.loads(line) for line in index_path.read_text().splitlines() if line.strip()]
        index = {r["review_id"]: r["case_id"] for r in index_rows}
        if len(index) != len(index_rows):
            raise ValueError("Duplicate review index identifiers")
        rows = [{**r, "case_id": index[r["review_id"]]} for r in rows]
        index_info = {"path": str(index_path), "sha256": digest(index_path)}
    qualifications = review.get("reviewer_qualifications", {})
    for case in cases:
        item_id = case.get("case_id", case.get("query_id"))
        ratings = [r for r in rows if r.get("case_id", r.get("query_id")) == item_id]
        ids = [r.get("reviewer_id") for r in ratings]
        if len(ids) < 2 or len(set(ids)) != len(ids) or any(not qualifications.get(i) for i in ids):
            raise ValueError("Two distinct reviewers with recorded qualifications are required per case")
        expected = {"expected_warning_types", "expected_supported_warning_types"}
        if "grades" in case:
            if any(r.get("grades") != case["grades"] for r in ratings):
                raise ValueError("Retrieval judgments require agreement with frozen query grades")
        elif expected <= case.keys():
            for r in ratings:
                if any(not isinstance(r.get(k), list) or sorted(r[k]) != sorted(case[k]) for k in expected):
                    raise ValueError("Safety labels require agreement with the frozen case labels")
        else:
            for r in ratings:
                if r.get("support_label") not in {"supported", "contradicted", "insufficient"} or r.get("applicability_label") not in {"applicable", "not_applicable", "unknown"}:
                    raise ValueError("Clinical support/applicability ratings are missing")
            if len({(r["support_label"], r["applicability_label"]) for r in ratings}) != 1:
                raise ValueError("Unresolved clinical review disagreement")
    return {"path": str(path), "sha256": digest(path), "rating_count": len(rows), "private_index": index_info}


def validate_protocol(path, cases_path, require_review=False):
    protocol = json.loads(path.read_text())
    if protocol.get("status") != "frozen" or protocol.get("cases_sha256") != digest(cases_path):
        raise ValueError("Frozen protocol/case hash mismatch")
    if protocol.get("code_sha256") != code_hashes():
        raise ValueError("Implementation changed since freeze; create a new protocol and independent evaluation")
    if protocol.get("runtime_configuration") != runtime_configuration():
        raise ValueError("Effective collection/reranker configuration changed since freeze")
    source = ROOT / "sources/hypertension/manifest.json"
    if protocol.get("source_manifest_sha256") != digest(source):
        raise ValueError("Source manifest changed since freeze")
    if require_review:
        review = protocol.get("verified_review")
        if not review or digest(Path(review["path"])) != review["sha256"]:
            raise ValueError("Independent review missing or changed")
        index = review.get("private_index")
        if index and digest(Path(index["path"])) != index["sha256"]:
            raise ValueError("Private review index changed since freeze")
    corpus = protocol.get("verified_corpus_audit")
    if corpus:
        if digest(Path(corpus["path"])) != corpus["sha256"]:
            raise ValueError("Corpus audit artifact changed since freeze")
        from evaluation.audit_corpus import snapshot
        dataset = json.loads(cases_path.read_text())
        current = snapshot(dataset.get("cases", []))
        frozen = json.loads(Path(corpus["path"]).read_text())
        if current["collections"] != frozen["collections"] or current["graph"] != frozen["graph"]:
            raise ValueError("Database contents/inventory changed since freeze")
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Frozen artifact already exists; use a new version")
    if subprocess.check_output(["git", "diff", "HEAD", "--", "backend", "evaluation", "ingestion", "requirements.txt"], cwd=ROOT):
        parser.error("Commit implementation changes before freezing")
    # New untracked source files must also be committed, rather than omitted from the hash list.
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "backend", "evaluation", "ingestion"], cwd=ROOT)
    if untracked:
        parser.error("Untracked evaluation/implementation files must be committed before freeze")
    draft = json.loads(args.draft.read_text())
    for key in ("research_question", "primary_metrics", "comparisons", "model", "evidence_role", "failure_policy"):
        if not draft.get(key):
            parser.error(f"Protocol field required: {key}")
    dataset = json.loads(args.cases.read_text())
    cases = dataset.get("cases", dataset.get("queries"))
    if not cases:
        parser.error("Nonempty cases or queries required")
    review = None
    corpus = None
    if draft["evidence_role"] == "held_out":
        if not draft.get("manual_exposure_audit_complete"):
            parser.error("Complete the manual exposure audit before declaring a holdout")
        if draft.get("task") != "exam_diagnosis":
            review = require_reviewed_cases(cases, draft)
        if not draft.get("corpus_audit_path"):
            parser.error("Held-out evaluation requires a read-only corpus audit for the selected cases")
        audit_path = ROOT / draft["corpus_audit_path"]
        audit = json.loads(audit_path.read_text())
        if not (audit.get("status") == "complete" and audit.get("clear_of_detected_qa_leakage") is True
                and audit.get("dimensions_match_768") is True and audit.get("cases_sha256") == digest(args.cases)):
            parser.error("Corpus audit incomplete, wrong cases, dimensional mismatch or detected leakage")
        corpus = {"path": str(audit_path), "sha256": digest(audit_path)}
    elif draft["evidence_role"] not in {"development", "regression"}:
        parser.error("Unknown evidence_role")
    result = {**draft, "status": "frozen", "created_utc": datetime.now(timezone.utc).isoformat(),
              "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "code_sha256": code_hashes(), "runtime_configuration": runtime_configuration(),
              "cases_sha256": digest(args.cases),
              "case_count": len(cases), "verified_review": review, "verified_corpus_audit": corpus,
              "source_manifest_sha256": digest(ROOT / "sources/hypertension/manifest.json"),
              "clinical_validation": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
