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
