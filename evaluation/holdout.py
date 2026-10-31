"""Build a non-content exposure registry and prepare candidates without inference.

The registry is conservative: reserved cases are excluded along with executed ones.
It cannot certify absence of manual exposure or model pretraining contamination.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def text_digest(text):
    return hashlib.sha256(" ".join(text.casefold().split()).encode()).hexdigest()


def build_registry(paths):
    case_ids, indices, text_hashes, families = set(), set(), set(), set()
    inputs = []
    def visit(value, context=""):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"case_id", "case_ids"}:
                    for cid in item if isinstance(item, list) else [item]:
                        if isinstance(cid, str):
                            case_ids.add(cid)
                            match = re.fullmatch(r"medqa-(?:us-test-)?(\d+)", cid)
                            if match:
                                indices.add(int(match[1]))
                elif key == "source_row_index_zero_based" and isinstance(item, int):
                    indices.add(item)
                elif key == "selected_zero_based_source_indices" and isinstance(item, list):
                    indices.update(item)
                elif key == "selected_ids" and context == "MedQA":
                    indices.update(int(i) for i in item)
                elif key in {"case_text", "raw_input"} and isinstance(item, str):
                    text_hashes.add(text_digest(item))
                elif key == "question" and isinstance(item, str):
                    text_hashes.add(text_digest(item))
                elif key == "family_id" and isinstance(item, str):
                    families.add(item)
                visit(item, key)
        elif isinstance(value, list):
            for item in value:
                visit(item, context)
    files = set()
    for path in paths:
        if not path.exists():
            raise ValueError(f"Exposure input missing: {path}")
        files.update([path] if path.is_file() else
                     [p for p in path.rglob("*") if p.is_file() and
                      (p.suffix == ".jsonl" or p.name.endswith("manifest.json") or
                       p.name.startswith("cases") and p.suffix == ".json")])
    for path in sorted(files):
        raw = path.read_bytes()
        try:
            values = ([json.loads(line) for line in raw.decode().splitlines() if line.strip()]
                      if path.suffix == ".jsonl" else [json.loads(raw)])
        except (UnicodeError, ValueError) as exc:
            raise ValueError(f"Unreadable exposure input: {path}; audit interrupted/partial files") from exc
        for value in values:
            visit(value)
        inputs.append({"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name,
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return {"schema_version": 1, "role": "development_or_reserved_exclusion_registry",
            "manual_exposure_audit_complete": False,
            "case_ids": sorted(case_ids), "medqa_us_test_indices": sorted(indices),
            "normalized_text_sha256": sorted(text_hashes), "family_ids": sorted(families),
            "inputs": inputs,
            "limitation": "Only supplied local artifacts were audited; manual exposure and provider pretraining remain unknown."}


def select_medqa(source, registry, count, seed):
    from evaluation.medqa_adapter import make_cases
    if count < 1 or not seed:
        raise ValueError("Positive count and fixed selection seed required")
    # Preserve the exact original diagnosis eligibility; do not broaden it silently.
    all_cases = make_cases(source, {"step1": 27, "step2&3": 62})
    excluded = set(registry["medqa_us_test_indices"])
    hashes = set(registry["normalized_text_sha256"])
    available = [c for c in all_cases["cases"] if c["source_row_index_zero_based"] not in excluded
                 and c["case_id"] not in registry["case_ids"] and text_digest(c["case_text"]) not in hashes]
    audit = {"eligible_total": len(all_cases["cases"]), "excluded": len(all_cases["cases"]) - len(available),
             "available": len(available), "by_step": dict(Counter(c["exam_step"] for c in available))}
    if count > len(available):
        raise ValueError(f"Requested {count} untouched candidates; only {len(available)} remain under this rule")
    selected = sorted(available, key=lambda c: hashlib.sha256(f"{seed}:{c['case_id']}".encode()).hexdigest())[:count]
    return {**all_cases, "dataset_id": "medqa-diagnosis-holdout-candidates-v2", "dataset_version": "2.0.0",
            "evidence_role": "reserved_candidates_pending_manual_exposure_audit",
            "selection": {**all_cases["selection"], "selection_seed": seed,
                          "selected_zero_based_source_indices": [c["source_row_index_zero_based"] for c in selected],
                          "quota_by_step": dict(Counter(c["exam_step"] for c in selected)),
                          "exposure_audit": audit}, "cases": selected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    registry_parser = sub.add_parser("registry")
    registry_parser.add_argument("--input", type=Path, action="append", required=True)
    registry_parser.add_argument("--output", type=Path, required=True)
    prepare = sub.add_parser("medqa")
    prepare.add_argument("--registry", type=Path, required=True)
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--count", type=int, required=True)
    prepare.add_argument("--seed", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; preserve the prior registry/selection")
    if args.command == "registry":
        result = build_registry(args.input)
    else:
        result = select_medqa(args.source, json.loads(args.registry.read_text()), args.count, args.seed)
        result["exclusion_registry_sha256"] = hashlib.sha256(args.registry.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "case_count": len(result.get("cases", [])),
                      "clinical_validation": False}))


if __name__ == "__main__":
    main()
