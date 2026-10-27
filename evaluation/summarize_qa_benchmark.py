"""Export aggregate QA results only after all frozen case/arm pairs are recorded."""
import argparse
from collections import Counter
import json
from pathlib import Path

from evaluation.run_qa_benchmark import summarize, digest, read_rows


def export(run, output, allow_partial=False):
    cases = json.loads((run / "cases.json").read_text())
    manifest = json.loads((run / "manifest.json").read_text())
    if digest(run / "cases.json") != manifest["cases_sha256"]:
        raise ValueError("Case hash mismatch")
    records = read_rows(run / "records.jsonl")
    pairs = [(r["case_id"], r["mode"]) for r in records]
    expected = {(c["case_id"], m) for c in cases for m in ("llm_only", "cdss_qa_adapter")}
    complete = set(pairs) == expected
    if len(pairs) != len(set(pairs)) or not set(pairs) <= expected or (not complete and not allow_partial):
        raise ValueError("Incomplete or duplicate matrix: cannot export final paper results")
    metrics = summarize(cases, records)
    saved = json.loads((run / "metrics.json").read_text())
    if metrics != saved:
        raise ValueError("Replay differs from saved metrics")
    gold = {c["case_id"]: c["gold"] for c in cases}
    dataset_ids = {d: {c["case_id"] for c in cases if c["dataset"] == d} for d in metrics}
    paired = {}
    for dataset, ids in dataset_ids.items():
        rows = {(r["case_id"], r["mode"]): r for r in records if r["case_id"] in ids}
        adapter_only, direct_only, paired_n = 0, 0, 0
        for case_id in ids:
            if (case_id, "llm_only") not in rows or (case_id, "cdss_qa_adapter") not in rows:
                continue
            paired_n += 1
            direct = rows[case_id, "llm_only"].get("answer") == gold[case_id]
            adapter = rows[case_id, "cdss_qa_adapter"].get("answer") == gold[case_id]
            adapter_only += adapter and not direct
            direct_only += direct and not adapter
        paired[dataset] = {"paired_cases": paired_n, "adapter_correct_direct_wrong": adapter_only,
                           "direct_correct_adapter_wrong": direct_only}
    retrieval_totals = {k: sum(r.get("retrieval", {}).get(k, 0) for r in records)
                        for k in ("graph_candidates", "vector_items", "authoritative_passages")}
    claim_statuses = Counter(c.get("status", "unknown") for r in records
                            for c in r.get("report", {}).get("claims", []))
    payload = {"experiment": "Frozen three-dataset adapted QA pilot", "complete": complete,
               "recorded_attempts": len(records), "planned_attempts": len(expected), "manifest": manifest,
               "records_sha256": digest(run / "records.jsonl"), "replay_verified": True,
               "metrics": metrics, "paired_discordances": paired,
               "reference_class_counts": {d: dict(Counter(c["gold"] for c in cases if c["dataset"] == d)) for d in metrics},
               "retrieval_totals": retrieval_totals, "system_claim_status_counts_not_gold_labels": dict(claim_statuses),
               "external_ieee_reported_correct_of_50": {"MedQA": 47, "PubMedQA": 44, "MedBullets": 42},
               "external_comparability": "Different sample/protocol; no direct superiority inference"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".json").write_text(json.dumps(payload, indent=2)+"\n")
    lines = ["# Frozen adapted QA benchmark results" + (" — INCOMPLETE" if not complete else ""), "",
        (f"**Partial run: {len(records)}/{len(expected)} planned arm attempts recorded. "
         "Stopped on the provider's 500-requests-per-day quota. Do not present this as the completed "
         "50-question-per-dataset experiment or as evidence of superiority.**" if not complete else
         f"All {len(expected)} planned arm attempts are recorded, including failures."), "",
        "These are exam/research-question results, not patient diagnostic accuracy or clinical safety estimates.", "",
        "The CDSS QA adapter runs the production graph/text clinical-report pipeline, followed by an added answer-selection call. "
        "The direct LLM baseline receives the same question, context and options without a report. "
        "The arms have different inference budgets; differences do not isolate graph or verification effects.", "",
        "| Dataset | Arm | Correct / attempted | Accuracy (Wilson 95% CI) | Failed answers |", "| --- | --- | ---: | --- | ---: |"]
    for dataset, modes in metrics.items():
        for mode, m in modes.items():
            low, high = m["accuracy_wilson95"]
            lines.append(f"| {dataset} | {mode} | {m['correct']}/{m['n_attempted']} | {m['accuracy']:.1%} ({low:.1%}–{high:.1%}) | {m['failures']} |")
    lines.extend(["", "For valid single-label outputs, micro precision, recall and F1 each equal accuracy. "
        "Class-level scores, macro-F1 and one-vs-rest specificity are in the JSON artifact. "
        "Failures remain in the accuracy denominator. Intervals are descriptive and do not account for public-test contamination or topic clustering.", "",
        "Selection was frozen by a fixed SHA-256 ordering before inference, with source hashes and case IDs retained. "
        "Answers/explanations were withheld from model inputs. PubMedQA uses official test IDs and question-plus-abstract "
        "yes/no/maybe classification; MedQA and MedBullets use five-option exact label matches. "
        "The requested model is Gemini Flash Lite, temperature zero; provider fallback, adaptive retry, web discovery and DrugCentral are disabled.", "",
        "The IEEE paper reports 47/50, 44/50 and 42/50 correct for MedQA, PubMedQA and MedBullets respectively. "
        "Those are external reported results on a different question selection; its PubMedQA scoring also differs. "
        "They must not be treated as a controlled baseline or evidence of superiority. "
        "Source: https://doi.org/10.1109/ACCESS.2025.3613340", "",
        f"Recorded retrieval totals were {retrieval_totals['graph_candidates']} graph disease candidates, "
        f"{retrieval_totals['vector_items']} textbook items and {retrieval_totals['authoritative_passages']} pinned source passages "
        "across CDSS attempts with saved reports. Counts include repeated retrieval across questions. "
        "Retrieval counts do not establish relevance or claim support.", "",
        "The clinical pipeline's narrow hypertension/amlodipine authoritative corpus and patient-case prompts "
        "limit applicability to general QA. The answer selector may rely on its own knowledge. "
        "No conclusion about MedRAGChecker, general claim-support accuracy, prescribing safety, or patient benefit follows.", "",
        "Raw question text, keys and reports remain in the ignored run directory. Aggregate metrics were regenerated "
        "from every recorded arm attempt and matched the saved metrics exactly.", ""])
    output.with_suffix(".md").write_text("\n".join(lines))
    print(json.dumps({"output": str(output), "attempts": len(records), "replay_verified": True}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output stem")
    parser.add_argument("--allow-partial", action="store_true", help="Export an explicitly incomplete status report")
    args = parser.parse_args()
    export(args.run, args.output, args.allow_partial)
