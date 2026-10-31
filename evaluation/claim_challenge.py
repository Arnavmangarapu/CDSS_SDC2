"""Blinded claim-support review and bounded gate baselines.

Source integrity, semantic support and patient applicability are separate outcomes.
Clinical metrics remain unavailable until two reviewers agree on each item.
"""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from backend.schemas.patient import PatientContext
from backend.schemas.report import ClinicalClaim
from backend.schemas.evidence import SourcePassage
from backend.services.claim_verifier import ClaimVerifier
from evaluation.run import write_jsonl
from ingestion.authoritative_sources import build_passages, load_manifest

SUPPORT = {"supported", "contradicted", "insufficient"}
APPLICABILITY = {"applicable", "not_applicable", "unknown"}
DECISIONS = {"supported", "conflicting", "unverified"}


def load_cases(path):
    data = json.loads(path.read_text())
    cases = data.get("cases", [])
    if not cases or len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Nonempty unique cases required")
    for case in cases:
        if any(not isinstance(case.get(k), str) or not case[k].strip()
               for k in ("case_id", "family_id", "case_text", "claim_text", "claim_type")):
            raise ValueError("Each challenge needs a family, raw case and explicit claim")
        if not isinstance(case.get("cited_passages"), list):
            raise ValueError("Explicit cited_passages list required, including [] for absent evidence")
    return data, cases


def prepare(cases, output):
    # Whitelist, never copy stratum/expected labels/model decisions to the reviewer packet.
    ordered = sorted(cases, key=lambda c: hashlib.sha256(c["case_id"].encode()).hexdigest())
    packet, private = [], []
    for i, case in enumerate(ordered, 1):
        rid = f"claim_review_{i:04d}"
        packet.append({"review_id": rid, **{k: case[k] for k in ("case_text", "claim_text", "cited_passages")},
                       "support_question": "Does the cited passage support, contradict, or provide insufficient evidence for the claim?",
                       "applicability_question": "Do explicit patient facts satisfy the claim's prerequisites? Do not infer undocumented facts."})
        private.append({"review_id": rid, "case_id": case["case_id"]})
    output.mkdir(parents=True, exist_ok=False)
    write_jsonl(output / "review_packet.jsonl", packet)
    write_jsonl(output / "private_index.jsonl", private)
    write_jsonl(output / "ratings_blank.jsonl", [{"review_id": r["review_id"], "reviewer_id": None,
        "support_label": None, "applicability_label": None, "rationale": ""} for r in packet])


def adjudicate(ratings, private_index):
    mapping = {row["review_id"]: row["case_id"] for row in private_index}
    if len(mapping) != len(private_index):
        raise ValueError("Duplicate review IDs in private index")
    groups = defaultdict(list)
    for row in ratings:
        if row.get("review_id") not in mapping or not row.get("reviewer_id"):
            raise ValueError("Unknown review ID or missing reviewer identity")
        if row.get("support_label") not in SUPPORT or row.get("applicability_label") not in APPLICABILITY:
            raise ValueError("Unfilled or invalid clinical rating")
        groups[row["review_id"]].append(row)
    resolved, disagreements = {}, []
    for rid, group in groups.items():
        ids = [r["reviewer_id"] for r in group]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate reviewer for the same item")
        if len(ids) < 2:
            continue
        labels = {(r["support_label"], r["applicability_label"]) for r in group}
        if len(labels) != 1:
            disagreements.append({"review_id": rid, "ratings": group})
            continue
        support, applicability = next(iter(labels))
        resolved[mapping[rid]] = {"support_label": support, "applicability_label": applicability}
    return resolved, disagreements


def score(cases, predictions, labels, modes):
    by_key = {(r["case_id"], r["mode"]): r for r in predictions}
    if len(by_key) != len(predictions) or set(by_key) != {(c["case_id"], m) for c in cases for m in modes}:
        raise ValueError("Predictions must include one row per planned case/mode, including failures")
    if not set(labels) <= {c["case_id"] for c in cases}:
        raise ValueError("Labels reference unknown challenge cases")
    for row in predictions:
        if row.get("status") == "ok" and row.get("decision") not in DECISIONS:
            raise ValueError("Invalid claim decision")
    if len(labels) != len(cases):
        return {"clinical_validation": False, "metrics_available": False,
                "reviewed": len(labels), "planned": len(cases),
                "reason": "Two agreeing reviews are required for every case; no selective reviewed-subset headline metrics"}
    results = {}
    for mode in modes:
        supported = false_supported = useful = possible_useful = exact = abstention_correct = abstention_needed = failures = 0
        for case in cases:
            rating = labels[case["case_id"]]
            support, applies = rating["support_label"], rating["applicability_label"]
            expected = ("conflicting" if support == "contradicted" or applies == "not_applicable" else
                        "supported" if support == "supported" and applies == "applicable" else "unverified")
            row = by_key[(case["case_id"], mode)]
            prediction = row.get("decision") if row.get("status") == "ok" else "error"
            failures += prediction == "error"
            exact += prediction == expected
            supported += prediction == "supported"
            false_supported += prediction == "supported" and expected != "supported"
            possible_useful += expected == "supported"
            useful += prediction == expected == "supported"
            abstention_needed += expected == "unverified"
            abstention_correct += prediction == expected == "unverified"
        def fraction(a, b):
            return {"numerator": a, "denominator": b, "value": round(a / b, 6) if b else None}
        results[mode] = {"attempted": len(cases), "failed": failures,
                         "decision_accuracy": fraction(exact, len(cases)),
                         "false_supported_fraction": fraction(false_supported, supported),
                         "useful_supported_coverage": fraction(useful, possible_useful),
                         "supported_coverage": fraction(supported, len(cases)),
                         "appropriate_abstention": fraction(abstention_correct, abstention_needed),
                         "risk_coverage_point": {"coverage": supported / len(cases),
                                                 "risk": false_supported / supported if supported else None}}
    return {"clinical_validation": False, "metrics_available": True, "modes": results,
            "label_status": "Two agreeing reviewers recorded; qualifications/authenticity must be documented separately",
            "uncertainty_note": "Related cases share family_id; these fractions have no independent-claim confidence interval."}


def run(cases):
    pinned = [p for entries in build_passages(load_manifest()).values() for p, _ in entries]
    verifier = ClaimVerifier(pinned)
    records = []
    for case in cases:
        try:
            sources = [SourcePassage.model_validate(p) for p in case["cited_passages"]]
            claim = ClinicalClaim(claim_id=case["case_id"], claim_type=case["claim_type"],
                                  text=case["claim_text"], status="unverified",
                                  unverified_evidence_ids=[p.id for p in sources],
                                  unverified_reason="Pending independent support/applicability review")
            checked = verifier.verify(PatientContext(raw_input=case["case_text"]), [claim], sources)
            trusted = {p.id for p in checked.trusted_passages}
            ids = {p.id for p in sources}
            # Deliberately weak comparator: confuses valid identity with support.
            identity_decision = "supported" if ids and ids <= trusted else "unverified"
            for mode, decision in (("identity_only", identity_decision),
                                   ("production_gate", checked.claims[0].status)):
                records.append({"case_id": case["case_id"], "mode": mode, "status": "ok",
                                "decision": decision, "trusted_passage_count": len(trusted)})
        except Exception as exc:
            for mode in ("identity_only", "production_gate"):
                records.append({"case_id": case["case_id"], "mode": mode, "status": "error",
                                "error_type": type(exc).__name__})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "score"))
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--ratings", type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; use a new path")
    dataset, cases = load_cases(args.cases)
    if args.action == "prepare":
        prepare(cases, args.output)
        return
    if dataset.get("evidence_role") == "held_out" and args.action == "run":
        if not args.protocol:
            parser.error("Held-out claim runs require a frozen independently reviewed protocol")
        from evaluation.freeze import validate_protocol
        validate_protocol(args.protocol, args.cases, require_review=True)
    args.output.mkdir(parents=True)
    if args.action == "run":
        write_jsonl(args.output / "predictions.jsonl", run(cases))
        (args.output / "manifest.json").write_text(json.dumps({
            "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
            "evidence_role": dataset.get("evidence_role", "development"), "clinical_validation": False,
            "note": "No clinical metrics without independent ratings. Gate input has unknown patient facts; fixed-context component test, not /analyze."}, indent=2) + "\n")
        return
    if not all((args.predictions, args.ratings, args.index)):
        parser.error("Scoring requires predictions, ratings and private index")
    def rows(path):
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    predictions = rows(args.predictions)
    labels, disagreements = adjudicate(rows(args.ratings), rows(args.index))
    modes = sorted({r["mode"] for r in predictions})
    result = score(cases, predictions, labels, modes)
    result["evidence_role"] = dataset.get("evidence_role", "development")
    (args.output / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    write_jsonl(args.output / "disagreements.jsonl", disagreements)


if __name__ == "__main__":
    main()
