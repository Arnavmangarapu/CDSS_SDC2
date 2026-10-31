"""Safety baselines and deployed-path evaluation, with explicit development status.

Offline regression: python -m evaluation.safety_v2 --cases evaluation/med_safety_cases.v1.json
  --output evaluation/runs/safety-baselines-regression --role regression
Live modes require --live and a frozen protocol. No independent labels are generated.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from backend.services.llm_fallback import LLMFallback
from backend.services.telemetry import capture_timings, totals
from evaluation.controlled import controlled_transport, configure_llm, configure_pipeline, require_model, DailyQuotaReached
from evaluation.metrics import wilson_interval
from evaluation.run_med_safety import evaluate_case, sha256, git_state
from ingestion.authoritative_sources import DEFAULT_MANIFEST, build_passages, load_manifest

WARNING_TYPES = {"amlodipine_allergy", "amlodipine_simvastatin", "allergy_status_unconfirmed"}
SUPPORTED = WARNING_TYPES - {"allergy_status_unconfirmed"}
OFFLINE = ("lexical", "deterministic", "structured_oracle")
LIVE = ("llm_only", "hybrid_fixed_proposal", "full_pipeline")


def lexical(text):
    """Deliberately weak name/keyword baseline; no negation or temporal reasoning."""
    warnings = set()
    if re.search(r"allerg\w*[^.!?]{0,60}\bamlodipine\b", text, re.I):
        warnings.add("amlodipine_allergy")
    if re.search(r"\bsimvastatin\b", text, re.I):
        warnings.add("amlodipine_simvastatin")
    if not re.search(r"no known (?:drug )?allerg|NKDA|allerg\w*[^.!?]{0,60}\b\w+", text, re.I):
        warnings.add("allergy_status_unconfirmed")
    return warnings, warnings & SUPPORTED


def validate_llm(data):
    for key, allowed in (("warning_types", WARNING_TYPES), ("supported_warning_types", SUPPORTED)):
        values = data.get(key)
        if not isinstance(values, list) or any(not isinstance(v, str) or v not in allowed for v in values):
            raise ValueError(f"Invalid {key}")
    if not set(data["supported_warning_types"]) <= set(data["warning_types"]):
        raise ValueError("Supported warnings must also be emitted warnings")


def score(cases, records, modes):
    expected = {(c["case_id"], mode) for c in cases for mode in modes}
    by_key = {(r["case_id"], r["mode"]): r for r in records}
    if len(by_key) != len(records) or set(by_key) != expected:
        raise ValueError("Exactly one record per planned case and mode, including errors, is required")
    output = {}
    for mode in modes:
        tp = emitted = wanted = false_supported = supported = supported_tp = supported_wanted = negatives = 0
        exact = failed = unknown = appropriate_abstention = 0
        for case in cases:
            row = by_key[(case["case_id"], mode)]
            ok = row.get("status") == "ok"
            failed += not ok
            actual = set(row.get("actual_warning_types", [])) if ok else set()
            confirmed = set(row.get("actual_supported_warning_types", [])) if ok else set()
            if not actual <= WARNING_TYPES or not confirmed <= actual & SUPPORTED:
                raise ValueError("Invalid warning/support prediction")
            target = set(case["expected_warning_types"])
            target_supported = set(case["expected_supported_warning_types"])
            tp += len(actual & target); emitted += len(actual); wanted += len(target)
            false_supported += len(confirmed - target_supported)
            supported += len(confirmed); supported_tp += len(confirmed & target_supported)
            supported_wanted += len(target_supported); negatives += len(SUPPORTED - target_supported)
            exact += ok and actual == target and confirmed == target_supported
            if "allergy_status_unconfirmed" in target:
                unknown += 1
                appropriate_abstention += ok and "allergy_status_unconfirmed" in actual and "amlodipine_allergy" not in confirmed
        def ratio(a, b):
            return {"numerator": a, "denominator": b, "value": round(a / b, 6) if b else None}
        output[mode] = {"attempted": len(cases), "failed": failed,
                        "warning_precision": ratio(tp, emitted), "warning_recall": ratio(tp, wanted),
                        "false_supported_fraction": ratio(false_supported, supported),
                        "false_support_rate_on_negative_opportunities": ratio(false_supported, negatives),
                        "useful_supported_warning_recall": ratio(supported_tp, supported_wanted),
                        "supported_decision_coverage": ratio(supported, len(cases) * len(SUPPORTED)),
                        "unknown_allergy_abstention": ratio(appropriate_abstention, unknown),
                        "exact_case_decisions": {**ratio(exact, len(cases)),
                                                 "wilson_95_descriptive": wilson_interval(exact, len(cases))}}
    return {"clinical_validation": False, "modes": output,
            "scope": "Existing amlodipine label rules; structured_oracle is a component upper bound, not a fair raw-text competitor",
            "uncertainty_note": "Warning events within cases/families are correlated; event fractions are descriptive and have no independent-event confidence interval."}


def run_case(case, mode, pinned, labels, pipeline=None, llm=None):
    common = {"case_id": case["case_id"], "mode": mode, "status": "ok"}
    if mode == "lexical":
        warning, supported = lexical(case["case_text"])
        return {**common, "actual_warning_types": sorted(warning),
                "actual_supported_warning_types": sorted(supported)}
    if mode in {"deterministic", "structured_oracle", "hybrid_fixed_proposal"}:
        context = None
        if mode == "hybrid_fixed_proposal":
            context = pipeline["clarifier"].process(case["case_text"])
            require_model(pipeline["clarifier"].llm)
        result = evaluate_case(case, "structured" if mode == "structured_oracle" else "text_extractor",
                               pinned, labels, context_override=context)
        return {**result, **common}
    if mode == "llm_only":
        payload = {"case_text": case["case_text"], "proposed_option": "amlodipine",
                   "sources": [{"id": p.id, "section": p.section, "passage": p.passage} for p in labels]}
        system = ('Assess the supplied case and proposed option against only the supplied label passages. '
                  'Return JSON with warning_types and supported_warning_types arrays. Allowed warning_types: '
                  + ', '.join(sorted(WARNING_TYPES)) + '. Missing/conflicting allergy status requires '
                  'allergy_status_unconfirmed, which cannot be supported. Supported warning types require '
                  'explicit applicable patient facts and supporting supplied evidence. Do not infer missing facts.')
        prediction = llm.generate_json(json.dumps(payload), system, validate=validate_llm)
        require_model(llm)
        return {**common, "actual_warning_types": prediction["warning_types"],
                "actual_supported_warning_types": prediction["supported_warning_types"],
                "provider_trace": llm.response_trace()}
    from backend.api import routes
    result = routes.analyze_case(routes.AnalyzeRequest(case_text=case["case_text"]))
    require_model(pipeline["clarifier"].llm); require_model(pipeline["fusion"].llm)
    findings = result["report"].get("medication_safety", {}).get("findings", [])
    return {**common, "actual_warning_types": sorted({f["type"] for f in findings if f["type"] in WARNING_TYPES}),
            "actual_supported_warning_types": sorted({f["type"] for f in findings
                if f["type"] in SUPPORTED and f.get("verification_status") == "supported"}),
            "other_finding_types": sorted({f["type"] for f in findings if f["type"] not in WARNING_TYPES}),
            "treatment_claims": [c for c in result["report"].get("claims", []) if c.get("claim_type") == "treatment"],
            "retrieval": result["retrieval"],
            "provider_trace": {k: pipeline[k].llm.response_trace() for k in ("clarifier", "fusion")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--role", choices=("regression", "development", "held_out"), required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; do not overwrite prior outcomes")
    dataset = json.loads(args.cases.read_text()); cases = dataset["cases"]
    if not cases or len({c["case_id"] for c in cases}) != len(cases):
        parser.error("Nonempty unique cases required")
    for case in cases:
        if not set(case["expected_warning_types"]) <= WARNING_TYPES or not set(case["expected_supported_warning_types"]) <= SUPPORTED:
            parser.error("Unsupported label scope; add and independently review new rules before expanding drug scope")
        if not set(case["expected_supported_warning_types"]) <= set(case["expected_warning_types"]):
            parser.error("Inconsistent expected support labels")
    protocol = {}
    if args.live or args.role == "held_out":
        if not args.protocol:
            parser.error("Live/held-out runs require a frozen protocol")
        from evaluation.freeze import validate_protocol
        protocol = validate_protocol(args.protocol, args.cases, require_review=args.role == "held_out")
    pinned = [p for entries in build_passages(load_manifest()).values() for p, _ in entries]
    labels = [p for p in pinned if p.source_type == "drug_label"]
    modes = OFFLINE + LIVE if args.live else OFFLINE
    args.output.mkdir(parents=True)
    manifest = {"evidence_role": args.role, "clinical_validation": False,
                "label_status": dataset.get("label_status", "Not independently reviewed"),
                "case_sha256": sha256(args.cases), "source_manifest_sha256": sha256(DEFAULT_MANIFEST),
                "created_utc": datetime.now(timezone.utc).isoformat(), "git": git_state(),
                "modes": modes, "status": "started", "protocol": protocol}
    records = []
    try:
        with controlled_transport(protocol.get("model", LLMFallback.MODEL_IDS["Gemini Flash Lite"])):
            pipeline = llm = None
            if args.live:
                from backend.api import routes
                from backend.agents.adaptive_retry import AdaptiveRetry
                pipeline = routes.get_pipeline(); configure_pipeline(pipeline)
                pipeline["retry"] = AdaptiveRetry(max_retries=0)
                from evaluation.run import RetrievalAblation
                pipeline["orchestrator"] = RetrievalAblation(pipeline["orchestrator"], "graph_text")
                # Full report generation with graph/text retrieval; web/DrugCentral
                # disabled, matching the declared controlled evaluation policy.
                llm = LLMFallback(); configure_llm(llm)
            for index, case in enumerate(cases):
                order = modes[index % len(modes):] + modes[:index % len(modes)]
                for mode in order:
                    try:
                        with capture_timings() as events:
                            row = run_case(case, mode, pinned, labels, pipeline, llm)
                        row["timings_ms"] = totals(events)
                    except DailyQuotaReached:
                        with (args.output / "records.jsonl").open("a", encoding="utf-8") as stream:
                            stream.write(json.dumps({"case_id": case["case_id"], "mode": mode,
                                "status": "error", "error_type": "DailyQuotaReached"}) + "\n")
                        raise
                    except Exception as exc:
                        row = {"case_id": case["case_id"], "mode": mode, "status": "error", "error_type": type(exc).__name__}
                    records.append(row)
                    with (args.output / "records.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(row, default=str) + "\n")
        if protocol:
            validate_protocol(args.protocol, args.cases, require_review=args.role == "held_out")
        result = score(cases, records, modes)
        result.update(evidence_role=args.role, label_status=manifest["label_status"])
        (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        manifest["status"] = "complete"
    except BaseException as exc:
        manifest.update(status="interrupted", error_type=type(exc).__name__)
        raise
    finally:
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
