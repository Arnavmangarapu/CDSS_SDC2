"""Opt-in timing for evaluation; disabled in normal requests, no patient text logged."""

from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter

_events = ContextVar("evaluation_timing_events", default=None)


@contextmanager
def capture_timings():
    events = []
    token = _events.set(events)
    try:
        yield events
    finally:
        _events.reset(token)


@contextmanager
def stage(name):
    events = _events.get()
    if events is None:
        yield
        return
    start = perf_counter()
    try:
        yield
    finally:
        events.append({"stage": name, "elapsed_ms": round((perf_counter() - start) * 1000, 3)})


def totals(events):
    result = {}
    for event in events:
        key = event["stage"]
        result[key] = round(result.get(key, 0) + event["elapsed_ms"], 3)
    return result
