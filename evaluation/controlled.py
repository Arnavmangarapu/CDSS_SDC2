"""Tracked single-provider evaluation policy. Run in a dedicated process, not a server.

Only transport HTTP 429 responses are retried. Generated answers are never retried.
The underlying raw response bodies, keys and request URLs are never logged.
"""

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import requests

from backend.services.llm_fallback import LLMFallback
from backend.services.telemetry import stage

_policy = ContextVar("controlled_evaluation", default=None)


class DailyQuotaReached(RuntimeError):
    pass


def require_model(llm):
    policy = _policy.get()
    if policy and (llm.last_provider != "Gemini Flash Lite" or llm.last_model != policy["model"]):
        raise RuntimeError("Controlled model unavailable; refusing deterministic/provider fallback")


def configure_llm(llm):
    policy = _policy.get()
    if policy:
        selected = next((p for p in llm.providers if p[0] == "Gemini Flash Lite" and p[1]), None)
        if selected is None:
            raise RuntimeError("Configured Gemini credential unavailable")
        name, key, _ = selected
        model = policy["model"]
        llm.MODEL_IDS = {**llm.MODEL_IDS, name: model}
        llm.providers = ((name, key, lambda key, prompt, system: llm._gemini(model, key, prompt, system)),)


def configure_pipeline(base):
    if _policy.get():
        for key in ("clarifier", "fusion"):
            configure_llm(base[key].llm)
        vector = base["orchestrator"].vector_retriever
        if not vector.is_ready or getattr(vector, "reranker", None) is None:
            raise RuntimeError("Controlled run requires the configured vector index and local reranker")
        if not base["orchestrator"].graph_retriever.is_ready:
            raise RuntimeError("Controlled run requires the configured graph retriever")


def strict_retrieval():
    return _policy.get() is not None


@contextmanager
def controlled_transport(model, interval=4.2, retries=3, event_sink=None):
    if interval < 0 or retries < 0:
        raise ValueError("Interval and transport retries must be nonnegative")
    if _policy.get():
        raise RuntimeError("Nested controlled transports are not supported")
    token = _policy.set({"model": model})
    original = LLMFallback._post
    last_start = None

    def post(url, headers, payload):
        nonlocal last_start
        for attempt in range(retries + 1):
            if last_start is not None:
                delay = max(0, last_start + interval - time.monotonic())
                if delay:
                    with stage("pacing_wait"):
                        time.sleep(delay)
            last_start = time.monotonic()
            event = {"utc": datetime.now(timezone.utc).isoformat(), "attempt": attempt + 1}
            try:
                with stage("http_service"):
                    data = original(url, headers, payload)
                event.update(status=200, returned_model_version=data.get("modelVersion"),
                             response_id=data.get("responseId"))
                if event_sink:
                    event_sink(event)
                return data
            except requests.RequestException as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                delay = 45.0
                quota_ids = []
                if status == 429:
                    try:
                        for detail in exc.response.json().get("error", {}).get("details", []):
                            quota_ids.extend(v.get("quotaId", "") for v in detail.get("violations", []))
                            if "retryDelay" in detail:
                                delay = min(60, max(1, float(detail["retryDelay"].rstrip("s"))))
                    except (ValueError, TypeError, AttributeError):
                        pass
                daily = any("PerDay" in item for item in quota_ids)
                event.update(status=status, quota_ids=quota_ids, daily_quota=daily,
                             error_type=type(exc).__name__)
                if event_sink:
                    event_sink(event)
                if daily:
                    raise DailyQuotaReached("Daily quota reached; partial records preserved") from None
                if status != 429 or attempt == retries:
                    raise
                with stage("transport_retry_wait"):
                    time.sleep(delay)
    LLMFallback._post = staticmethod(post)
    try:
        yield
    finally:
        LLMFallback._post = staticmethod(original)
        _policy.reset(token)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--model", default=LLMFallback.MODEL_IDS["Gemini Flash Lite"])
    parser.add_argument("--interval", type=float, default=4.2)
    parser.add_argument("--transport-retries", type=int, default=3)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; preserve previous attempts and use a new path")
    from evaluation.freeze import validate_protocol
    protocol = validate_protocol(args.protocol, args.cases)
    if protocol["model"] != args.model:
        parser.error("Requested model differs from frozen protocol")
    # Sibling journal exists even if initialization or quota interrupts the run.
    journal = args.output.with_name(args.output.name + "-transport")
    journal.mkdir(parents=True, exist_ok=False)
    def event_sink(event):
        with (journal / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event) + "\n")
    details = {"model": args.model, "provider_fallback": False, "temperature": 0,
               "adaptive_retrieval_retries": 0, "generated_answer_retries": 0,
               "minimum_request_interval_seconds": args.interval,
               "transport_429_retries": args.transport_retries,
               "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "timing_note": "Stages are nested wall times, not additive. HTTP service excludes separately recorded pacing/retry waits.",
               "status": "started"}
    (journal / "policy.json").write_text(json.dumps(details, indent=2) + "\n")
    previous = sys.argv
    try:
        sys.argv = ["evaluation.run", "--cases", str(args.cases), "--output", str(args.output),
                    "--max-retries", "0", "--review-sample-size", "1000000"]
        with controlled_transport(args.model, args.interval, args.transport_retries, event_sink):
            from evaluation.run import main as run_main
            run_main()
        validate_protocol(args.protocol, args.cases)
        manifest_path = args.output / "run_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        details["status"] = "complete"
        manifest.update(evidence_role=protocol["evidence_role"],
                        frozen_protocol_sha256=hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
                        controlled_policy=details)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    except BaseException as exc:
        details.update(status="interrupted", error_type=type(exc).__name__)
        raise
    finally:
        sys.argv = previous
        (journal / "policy.json").write_text(json.dumps(details, indent=2) + "\n")


if __name__ == "__main__":
    main()
