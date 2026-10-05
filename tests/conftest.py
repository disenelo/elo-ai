"""
conftest.py — skip script-style test files during pytest collection;
provide shared fixtures for sequential-pattern test files.

Script-style tests (no def test_ functions) use sys.exit() at module level
and are designed to be run directly: python3 tests/test_xxx.py
Importing them under pytest triggers SystemExit (INTERNALERROR).
This hook prevents pytest from importing those files.
"""
from __future__ import annotations

import json
import os
import sys

import os as _os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pytest_ignore_collect(collection_path, config):
    name = collection_path.name
    if collection_path.suffix == ".py" and name.startswith("test_"):
        try:
            source = collection_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None
        if "def test_" not in source and "class Test" not in source:
            return True  # skip — script-style, not pytest-style
    return None


# ── fixtures for test_loop_one_brain.py ─────────────────────────────────────
# test_loop_2/3/4/7 take `rows`; test_loop_6/7 take `confirmed_lessons`.
# These are read from live runtime files — skip if not present yet.

@pytest.fixture(scope="module")
def rows():
    """Read decision_journal.jsonl rows for LOOP-2/3/4/7 tests."""
    dj = os.path.join(ROOT, "self", "journals", "decision_journal.jsonl")
    if not os.path.exists(dj):
        pytest.skip("decision_journal.jsonl not present (no live run yet)")
    with open(dj, encoding="utf-8") as f:
        _rows = [json.loads(l) for l in f if l.strip()]
    if not _rows:
        pytest.skip("decision_journal.jsonl is empty (no live run yet)")
    return _rows


@pytest.fixture(scope="module")
def confirmed_lessons():
    """Read confirmed lessons from lessons_ledger.jsonl for LOOP-6/7 tests."""
    ledger = os.path.join(ROOT, "self", "lessons_ledger.jsonl")
    if not os.path.exists(ledger):
        pytest.skip("lessons_ledger.jsonl not present (reflection loop not yet run)")
    with open(ledger, encoding="utf-8") as f:
        lessons = [json.loads(l) for l in f if l.strip()]
    confirmed = [l for l in lessons if l.get("status") == "confirmed"]
    if not confirmed:
        pytest.skip("No confirmed lessons yet (reflection loop not closing)")
    return confirmed


# ── fixtures for test_w2_decision_journal_session_id.py ─────────────────────
# test_w2_dj_1/2 take `tmp_journal`; test_w2_dj_2/3 take `first_sid`.
# Sequential: first_sid writes one record to tmp_journal, returns its session_id.

@pytest.fixture(scope="module")
def tmp_journal(tmp_path_factory):
    """Shared temp journal file for the W2-DJ test sequence."""
    p = tmp_path_factory.mktemp("w2dj") / "decision_journal.jsonl"
    return str(p)


@pytest.fixture(scope="module")
def first_sid(tmp_journal):
    """Write one record to tmp_journal; return the session_id — for W2-DJ-2 and W2-DJ-3."""
    sys.path.insert(0, ROOT)
    from self import decision_journal as dj  # noqa: E402
    orig = dj._JOURNAL
    dj._JOURNAL = tmp_journal
    dj.record(
        turn="hello world",
        action="conversation",
        exec_decision={"cal_reason": "fixture-init"},
        backend="mock",
        outcome="spoke",
    )
    with open(tmp_journal, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    sid = json.loads(lines[-1]).get("session_id", "")
    yield sid
    # Restore journal path after the W2-DJ module completes so other tests are unaffected.
    dj._JOURNAL = orig


# ── The SPG graph is eLo's memory, not scratch space ────────────────────────
#
# Measured 2026-10-04: a full `pytest tests/` run added 8 nodes to the live
# data/spg_graph.json — 340 before, 348 after — and across the day's runs
# roughly 112 of that store's growth was created by testing.
#
# The leak is structural, not one careless test.
# tests/test_wo_wkg_001_phase1_schema.py isolates itself correctly by
# patching _WKG_DIR, and then WO-SPG-LINK-001 gave record_claim() an SPG
# write that the WKG isolation does not cover. Any test that records a claim
# leaks, whether or not its author knows SPG exists.
#
# Redirected for EVERY test, so the next function to acquire a store-writing
# side effect cannot quietly start writing eLo's memory either. A test that
# genuinely needs the live store reads it by its own path, which this does
# not touch.

@pytest.fixture(autouse=True)
def _isolate_spg_graph(tmp_path_factory, monkeypatch):
    import memory.spg_graph as _spg_graph
    target = tmp_path_factory.mktemp("spg") / "spg_graph.json"
    monkeypatch.setattr(_spg_graph, "_GRAPH_PATH", target)
    yield


# ── self/journals/body_relay.jsonl — the same leak, second instance ──────────
#
# The SPG note above ends: "the next function to acquire a store-writing side
# effect cannot quietly start writing eLo's memory either." This is that
# function, and it did not need to acquire the side effect — it shipped with
# it.
#
# runtime/body_relay.relay_body_event() appends to the LIVE journal, and the
# only callers it has ever had are tests. Measured 2026-10-05: 154 entries,
# every one of them event_kind="sit_commanded", and the newest carries the
# payload {"target": "cursor"} written verbatim by
# tests/test_canon_vii_executive.py:393. eLo's record of his own body is
# entirely a record of the test suite running.
#
# Redirected for EVERY test, like the SPG store, so this cannot be rebuilt by
# the next test that emits a body event.

# An autouse fixture CANNOT fix this, and that was the first attempt:
# tests/test_canon_vii_executive.py is a script, not a set of test
# functions — its relay_body_event() calls run at IMPORT, during
# collection, before any fixture exists. Measured: the live journal still
# grew 154 -> 156 on a run that reported "no tests ran".
#
# conftest is imported before any test module, so the redirect is done
# here at import time and covers collection as well as tests.

import tempfile as _tempfile
import runtime.body_relay as _body_relay

_RELAY_TMP = _os.path.join(
    _tempfile.mkdtemp(prefix="elo-relay-"), "body_relay.jsonl"
)
_body_relay._RELAY_LOG = _RELAY_TMP
