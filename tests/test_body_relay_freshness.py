"""
tests/test_body_relay_freshness.py — an old event is not evidence about now.

audit_body_relay() exists to catch one thing: a body that is sitting when
nothing commanded it to sit. It read the last 20 relay events with no bound on
their age, so any event ever written satisfied the check.

Measured on the live journal 2026-10-05, before the fix:

    events the audit reads : 20
    age range              : 0.0d - 37.5d old
    kinds                  : ['sit_commanded']
    audit verdict          : ok=True  violations=[]

Every one of those had been written by the test suite, and the audit could
therefore return neither of its two findings — not the VIOLATION, not the
pending_unacked. It was a check that could not fail.

These tests are causal: the ONLY thing that differs between them is how old
the event is.
"""
from __future__ import annotations

import json
import time

import pytest

import runtime.body_relay as br


class _Body:
    """Minimal stand-in for the BodySchema fields the audit reads."""

    def __init__(self, pending_sit: bool = True, queued_intent: str = ""):
        self.pending_sit = pending_sit
        self.queued_intent = queued_intent


def _write_event(age_s: float) -> None:
    """Put one sit_commanded event in the log, aged age_s seconds."""
    entry = {
        "ts": time.time() - age_s,
        "event_kind": "sit_commanded",
        "is_reflex": False,
        "payload": {"target": "cursor"},
    }
    with open(br._RELAY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


@pytest.fixture(autouse=True)
def _own_log(tmp_path, monkeypatch):
    """Each test gets an empty log, so neither sees the other's events."""
    monkeypatch.setattr(br, "_RELAY_LOG", str(tmp_path / "body_relay.jsonl"))


# ── the causal pair ─────────────────────────────────────────────────────────

def test_a_stale_relay_event_does_not_excuse_an_uncommanded_sit():
    _write_event(age_s=br.RELAY_FRESH_S * 10)        # long past the bound

    res = br.audit_body_relay(_Body(pending_sit=True), recent_journal=[])

    assert res["ok"] is False, (
        "a sit relayed long ago was accepted as evidence for a sit happening "
        "now — this is the bug that made the audit unable to fail"
    )
    assert any("pending_sit" in v for v in res["violations"])


def test_a_fresh_relay_event_does_excuse_it():
    _write_event(age_s=1.0)                          # inside the bound

    res = br.audit_body_relay(_Body(pending_sit=True), recent_journal=[])

    assert res["ok"] is True, (
        "a sit relayed one second ago is exactly the evidence the audit "
        "should accept"
    )
    assert res["violations"] == []


# ── the bound itself ────────────────────────────────────────────────────────

def test_the_reader_is_unbounded_unless_asked():
    """
    The default is deliberately unchanged, so callers wanting the raw tail
    still get it. Only the audit opts into the bound.
    """
    _write_event(age_s=br.RELAY_FRESH_S * 10)

    assert len(br.recent_relay_events(20)) == 1
    assert br.recent_relay_events(20, max_age_s=br.RELAY_FRESH_S) == []


def test_an_event_with_no_timestamp_is_not_treated_as_fresh():
    """A missing ts must not read as 1970 OR as now; it must simply not count."""
    with open(br._RELAY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"event_kind": "sit_commanded"}) + "\n")

    assert br.recent_relay_events(20, max_age_s=br.RELAY_FRESH_S) == []
