"""Paired all-case diagnosis analysis; no model calls or question text in exports."""

import argparse
from itertools import combinations
import json
import math
from pathlib import Path
import random

from evaluation.metrics import MODES, diagnosis_key, wilson_interval


def quantile(values, p):
    position = (len(values) - 1) * p
    lo, hi = math.floor(position), math.ceil(position)
    return round(values[lo] + (values[hi] - values[lo]) * (position - lo), 6)


def exact_mcnemar(a_only, b_only):
    if min(a_only, b_only) < 0:
        raise ValueError("Discordant counts must be nonnegative")
    n = a_only + b_only
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a_only, b_only) + 1)) / 2**n)


def holm(values):
    ordered = sorted(range(len(values)), key=lambda i: values[i])
    adjusted = [0.0] * len(values)
    previous = 0.0
    for rank, index in enumerate(ordered):
        previous = max(previous, min(1.0, values[index] * (len(values) - rank)))
        adjusted[index] = previous
    return adjusted


def summarize(cases, records, bootstrap_replicates=2000, seed=20261031):
    if not cases or len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Unique, nonempty cases required")
    if bootstrap_replicates < 100:
        raise ValueError("At least 100 bootstrap replicates required")
    by_key = {(r.get("case_id"), r.get("mode")): r for r in records}
    expected = {(c["case_id"], m) for c in cases for m in MODES}
    if len(by_key) != len(records) or set(by_key) != expected:
        raise ValueError("Exactly one record per case and arm required, including failures")
    outcomes = {mode: [] for mode in MODES}
    failures = {mode: 0 for mode in MODES}
    for case in cases:
        aliases = {diagnosis_key(a) for a in case["reference_diagnosis_aliases"]}
        for mode in MODES:
            row = by_key[(case["case_id"], mode)]
            ok = row.get("status") == "ok" and isinstance(row.get("report"), dict)
            ranked = row["report"].get("ranked_diagnoses", []) if ok else []
            # Empty/unavailable first entries never promote a later diagnosis to rank 1.
            first = ranked[0].get("diagnosis", "") if ranked else ""
            outcomes[mode].append(bool(ok and first and diagnosis_key(first) in aliases))
            failures[mode] += int(not ok)
    n = len(cases)
    comparisons = []
    for a, b in combinations(MODES, 2):
        diffs = [int(x) - int(y) for x, y in zip(outcomes[a], outcomes[b])]
        a_only, b_only = diffs.count(1), diffs.count(-1)
        rng = random.Random(seed)
        samples = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(bootstrap_replicates))
        comparisons.append({"a": a, "b": b, "case_count": n,
                            "a_only_correct": a_only, "b_only_correct": b_only,
                            "both_correct": sum(x and y for x, y in zip(outcomes[a], outcomes[b])),
                            "both_incorrect": sum(not x and not y for x, y in zip(outcomes[a], outcomes[b])),
                            "difference_a_minus_b": round(sum(diffs) / n, 6),
                            "paired_bootstrap_95": [quantile(samples, .025), quantile(samples, .975)],
                            "exact_mcnemar_two_sided_p": exact_mcnemar(a_only, b_only)})
    adjusted = holm([c["exact_mcnemar_two_sided_p"] for c in comparisons])
    for comparison, p in zip(comparisons, adjusted):
        comparison["holm_adjusted_p"] = p
    return {"clinical_validation": False,
            "denominator_policy": "All planned cases; failed and empty outputs count incorrect",
            "bootstrap": {"replicates": bootstrap_replicates, "seed": seed,
                          "unit": "case", "interval": "percentile; descriptive, unstable with few discordant pairs"},
            "per_mode": {m: {"correct": sum(outcomes[m]), "attempted": n, "failed": failures[m],
                             "accuracy": round(sum(outcomes[m]) / n, 6),
                             "wilson_95": wilson_interval(sum(outcomes[m]), n)} for m in MODES},
            "comparisons": comparisons,
            "case_scores": [{"case_id": case["case_id"],
                             **{m: outcomes[m][i] for m in MODES}} for i, case in enumerate(cases)],
            "interpretation": "No significant difference does not establish equivalence; p-values do not repair development-set reuse."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-role", choices=("development", "held_out"), default="development")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; choose a new artifact path")
    cases = json.loads(args.cases.read_text())["cases"]
    records = [json.loads(line) for line in args.records.read_text().splitlines() if line.strip()]
    result = summarize(cases, records)
    import hashlib
    result.update(evidence_role=args.evidence_role,
                  cases_sha256=hashlib.sha256(args.cases.read_bytes()).hexdigest(),
                  records_sha256=hashlib.sha256(args.records.read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
