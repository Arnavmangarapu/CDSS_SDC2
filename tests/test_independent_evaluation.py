"""Synthetic unit fixtures for study safeguards, not clinical validation cases."""

import json

import pytest
import requests

from backend.services.llm_fallback import LLMFallback
from backend.services.telemetry import capture_timings, stage, totals
from evaluation.claim_challenge import adjudicate, prepare, score as score_claims
from evaluation.controlled import controlled_transport, DailyQuotaReached, require_model
from evaluation.holdout import build_registry, select_medqa
from evaluation.metrics import MODES
from evaluation.paired_statistics import exact_mcnemar, holm, summarize
from evaluation.retrieval_baselines import bm25, judged_metrics
from evaluation.safety_v2 import score as score_safety
from evaluation import freeze


def test_returned_identity_token_usage_and_trace_reset(monkeypatch):
    llm = LLMFallback()
    response = {"modelVersion": "actual-version", "responseId": "response-123",
                "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 4, "private": "omit"},
                "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '{"ok":true}'}]}}]}
    monkeypatch.setattr(llm, "_post", lambda *args: response)
    llm.providers = (("Gemini Flash Lite", "not-a-real-key", llm._gemini_lite),)
    llm.generate_json("private text", "system")
    trace = llm.response_trace()
    assert trace["model"] != trace["returned_model_version"]
    assert trace["returned_model_version"] == "actual-version"
    assert trace["usage_metadata"] == {"promptTokenCount": 12, "candidatesTokenCount": 4}
    assert "private text" not in json.dumps(trace)
    llm.providers = (("bad", "not-a-real-key", lambda *args: "not json"),)
    assert llm.generate_json("p", "s") is None
    assert llm.last_response_metadata == {}


def test_transport_retries_only_429_and_excludes_secrets(monkeypatch):
    calls, events = [], []
    def post(*args):
        calls.append(1)
        if len(calls) == 1:
            response = requests.Response(); response.status_code = 429
            response._content = b'{"error":{"details":[{"retryDelay":"1s"}]}}'
            raise requests.HTTPError(response=response)
        return {"modelVersion": "v1", "responseId": "r1"}
    monkeypatch.setattr(LLMFallback, "_post", staticmethod(post))
    monkeypatch.setattr("evaluation.controlled.time.sleep", lambda seconds: None)
    with capture_timings() as timing:
        with controlled_transport("fixed", interval=0, retries=1, event_sink=events.append):
            assert LLMFallback._post("secret-url", {"key": "secret"}, {"text": "private"})["modelVersion"] == "v1"
    assert [e["status"] for e in events] == [429, 200]
    assert "transport_retry_wait" in totals(timing)
    assert "private" not in json.dumps(events) and "secret" not in json.dumps(events)
    assert LLMFallback._post is post


def test_daily_quota_stops_instead_of_retrying(monkeypatch):
    def post(*args):
        response = requests.Response(); response.status_code = 429
        response._content = b'{"error":{"details":[{"violations":[{"quotaId":"RequestsPerDay"}]}]}}'
        raise requests.HTTPError(response=response)
    monkeypatch.setattr(LLMFallback, "_post", staticmethod(post))
    monkeypatch.setattr("evaluation.controlled.time.sleep", lambda seconds: pytest.fail("Must not wait"))
    with controlled_transport("fixed", interval=0):
        with pytest.raises(DailyQuotaReached):
            LLMFallback._post("url", {}, {})
        with pytest.raises(RuntimeError, match="fallback"):
            require_model(LLMFallback())


def test_nested_timing_is_context_local_and_resets():
    with capture_timings() as outer:
        with stage("outer"):
            with capture_timings() as inner:
                with stage("inner"):
                    pass
    assert set(totals(outer)) == {"outer"}
    assert set(totals(inner)) == {"inner"}
    with stage("not-captured"):
        pass
    assert set(totals(outer)) == {"outer"}


def test_paired_failures_empty_predictions_and_duplicate_rejection():
    cases = [{"case_id": str(i), "reference_diagnosis_aliases": ["Correct"]} for i in range(3)]
    rows = [{"case_id": c["case_id"], "mode": mode, "status": "ok",
             "report": {"ranked_diagnoses": [{"diagnosis": "Correct"}]}}
            for c in cases for mode in MODES]
    rows[0] = {"case_id": "0", "mode": "llm_only", "status": "error"}
    rows[3]["report"]["ranked_diagnoses"] = []
    result = summarize(cases, rows, bootstrap_replicates=100)
    assert result["per_mode"]["llm_only"]["correct"] == 1
    assert result["per_mode"]["llm_only"]["attempted"] == 3
    assert exact_mcnemar(0, 2) == .5
    assert exact_mcnemar(2, 3) == 1
    assert holm([.03, .01, .04]) == [.06, .03, .06]
    with pytest.raises(ValueError, match="Exactly one"):
        summarize(cases, rows + [rows[0]])


def test_registry_excludes_both_reserved_and_executed_rows(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"selection": {"MedQA": {"selected_ids": ["5"]}}}))
    records = tmp_path / "records.jsonl"
    records.write_text(json.dumps({"case_id": "medqa-us-test-0007", "case_text": "Private case text"}) + "\n")
    registry = build_registry([tmp_path])
    assert registry["medqa_us_test_indices"] == [5, 7]
    assert "Private case text" not in json.dumps(registry)
    from evaluation import medqa_adapter
    monkeypatch.setattr(medqa_adapter, "make_cases", lambda *args: {"selection": {}, "cases": [
        {"case_id": f"medqa-us-test-{i:04d}", "source_row_index_zero_based": i,
         "case_text": f"Case number {i}", "exam_step": "step1"} for i in (5, 6, 7)]})
    selected = select_medqa(tmp_path / "unused", registry, 1, "fixed-seed")
    assert selected["cases"][0]["source_row_index_zero_based"] == 6
    with pytest.raises(ValueError, match="only 1 remain"):
        select_medqa(tmp_path / "unused", registry, 2, "fixed-seed")


def test_safety_failure_stays_in_recall_and_always_abstain_has_zero_usefulness():
    cases = [{"case_id": "a", "expected_warning_types": ["amlodipine_allergy"],
              "expected_supported_warning_types": ["amlodipine_allergy"]}]
    rows = [{"case_id": "a", "mode": "empty", "status": "ok", "actual_warning_types": [],
             "actual_supported_warning_types": []}, {"case_id": "a", "mode": "failed", "status": "error"}]
    metrics = score_safety(cases, rows, ["empty", "failed"])["modes"]
    assert metrics["failed"]["warning_recall"]["value"] == 0
    assert metrics["empty"]["useful_supported_warning_recall"]["value"] == 0
    assert metrics["empty"]["false_supported_fraction"]["value"] is None


def test_claim_review_blinds_labels_and_keeps_disagreements(tmp_path):
    cases = [{"case_id": "a", "case_text": "Case", "claim_text": "Claim", "cited_passages": [],
              "expected_status": "supported", "family_id": "f", "claim_type": "treatment"}]
    prepare(cases, tmp_path / "packet")
    assert "expected_status" not in (tmp_path / "packet/review_packet.jsonl").read_text()
    index = [{"review_id": "r", "case_id": "a"}]
    a = {"review_id": "r", "reviewer_id": "unit-a", "support_label": "supported", "applicability_label": "applicable"}
    b = {**a, "reviewer_id": "unit-b", "applicability_label": "unknown"}
    labels, disagreements = adjudicate([a, b], index)
    assert not labels and disagreements
    prediction = [{"case_id": "a", "mode": "unit", "status": "ok", "decision": "supported"}]
    assert score_claims(cases, prediction, labels, ["unit"])["metrics_available"] is False
    with pytest.raises(ValueError, match="Duplicate reviewer"):
        adjudicate([a, a], index)


def test_valid_but_inapplicable_claim_is_false_support_and_abstention_not_utility():
    cases = [{"case_id": "a"}, {"case_id": "b"}]
    labels = {"a": {"support_label": "supported", "applicability_label": "not_applicable"},
              "b": {"support_label": "supported", "applicability_label": "applicable"}}
    rows = [{"case_id": c["case_id"], "mode": mode, "status": "ok", "decision": decision}
            for c in cases for mode, decision in (("support_all", "supported"), ("abstain_all", "unverified"))]
    result = score_claims(cases, rows, labels, ["support_all", "abstain_all"])["modes"]
    assert result["support_all"]["false_supported_fraction"]["value"] == .5
    assert result["abstain_all"]["useful_supported_coverage"]["value"] == 0


def test_retrieval_baseline_and_incomplete_judgments_are_explicit():
    assert bm25("specific token", {"a": "generic", "b": "specific token"})[0] == "b"
    query = {"grades": {"b": 2}, "judgments_complete": False}
    result = judged_metrics(["a", "b"], query, [1, 5])
    assert result["1"]["precision"] is None
    assert result["5"]["recall"] is None
    query["judgments_complete"] = True
    assert judged_metrics(["b", "a"], query, [1])["1"]["precision"] == 1


def test_freeze_refuses_changed_code_and_unreviewed_clinical_holdout(tmp_path, monkeypatch):
    cases = tmp_path / "cases.json"; cases.write_text('{"cases": [{"case_id": "unit"}]}')
    source = tmp_path / "sources/hypertension/manifest.json"
    source.parent.mkdir(parents=True); source.write_text('{}')
    monkeypatch.setattr(freeze, "ROOT", tmp_path)
    monkeypatch.setattr(freeze, "code_hashes", lambda: {"code.py": "original"})
    monkeypatch.setattr(freeze, "runtime_configuration", lambda: {"collection": "unit"})
    protocol = tmp_path / "frozen.json"
    data = {"status": "frozen", "cases_sha256": freeze.digest(cases),
            "source_manifest_sha256": freeze.digest(source), "code_sha256": {"code.py": "original"},
            "runtime_configuration": {"collection": "unit"}}
    protocol.write_text(json.dumps(data))
    assert freeze.validate_protocol(protocol, cases)["status"] == "frozen"
    with pytest.raises(ValueError, match="review missing"):
        freeze.validate_protocol(protocol, cases, require_review=True)
    monkeypatch.setattr(freeze, "code_hashes", lambda: {"code.py": "modified"})
    with pytest.raises(ValueError, match="Implementation changed"):
        freeze.validate_protocol(protocol, cases)


def test_daily_quota_case_attempt_is_checkpointed(monkeypatch):
    from backend.api import routes
    from evaluation import run
    class Clarifier:
        def process(self, text):
            raise DailyQuotaReached("unit quota")
    base = {"clarifier": Clarifier()}
    monkeypatch.setattr(routes, "get_pipeline", lambda: base)
    monkeypatch.setattr("evaluation.controlled.configure_pipeline", lambda base: None)
    saved = []
    with pytest.raises(DailyQuotaReached):
        run.live_records([{"case_id": "unit", "case_text": "synthetic unit"}], 0, record_sink=saved.append)
    assert len(saved) == 3
    assert all(r["status"] == "error" and r["failed_stage"] == "shared_extraction" for r in saved)


def test_corpus_audit_detects_nested_answer_payload_without_printing_text():
    from evaluation.audit_corpus import qa_keys
    assert qa_keys({"metadata": {"answer_idx": "A"}, "text": "normal text"}) == {"answer_idx"}
    assert qa_keys({"source_passage": {"passage": "ordinary source passage"}}) == set()
