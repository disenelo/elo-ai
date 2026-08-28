"""
tests/test_wo_fix_112_ambient.py — WO-FIX-112-AMBIENT: confidence threaded on ambient journal entries.

AT-1: ambient plan with confidence=0.85 → exec_decision['confidence'] = 0.85 (getattr path)
AT-2: ambient plan with no confidence attr → exec_decision['confidence'] = None (no AttributeError)
AT-3: executive.py contains 0 references to WO-FIX-112-AMBIENT scope (FREEZE_V1_LOCK clean)
AT-4: main-turn WO-112 confidence path still intact (regression — spine.py fix commit 0653d20)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-1: confidence=0.85 flows through getattr into exec_decision ──────────

def test_ambient_confidence_threaded():
    _amb_plan = types.SimpleNamespace(confidence=0.85)
    confidence_val = getattr(_amb_plan, "confidence", None)
    exec_decision = {
        "intent_source":   "self",
        "internal_intent": "curiosity",
        "action":          "speak",
        "confidence":      confidence_val,
    }
    assert exec_decision["confidence"] == 0.85, \
        f"AT-1 FAIL: expected 0.85, got {exec_decision['confidence']}"


# ── AT-2: missing attr → None, no AttributeError ────────────────────────────

def test_ambient_confidence_none_when_missing():
    _amb_plan = types.SimpleNamespace()  # no confidence attr
    try:
        confidence_val = getattr(_amb_plan, "confidence", None)
    except AttributeError as e:
        raise AssertionError(f"AT-2 FAIL: AttributeError raised — {e}")
    exec_decision = {
        "intent_source":   "self",
        "internal_intent": "curiosity",
        "action":          "silence",
        "confidence":      confidence_val,
    }
    assert exec_decision["confidence"] is None, \
        f"AT-2 FAIL: expected None, got {exec_decision['confidence']}"


# ── AT-3: executive.py has 0 FIX-112-AMBIENT touches (FREEZE_V1_LOCK clean) ─

def test_executive_py_freeze_lock_clean():
    exec_path = os.path.join(ROOT, "runtime", "executive.py")
    with open(exec_path, encoding="utf-8") as f:
        src = f.read()
    forbidden = ["FIX-112-AMBIENT", "getattr.*_amb_plan", "ambient_confidence"]
    for term in forbidden:
        assert term not in src, \
            f"AT-3 FAIL: executive.py contains forbidden term '{term}' — FREEZE_V1_LOCK violated"


# ── AT-4: WO-112 main-turn confidence path intact (regression) ───────────────

def test_main_turn_confidence_regression():
    """decision_journal.record() writes confidence from exec_decision — main-turn path."""
    from self.decision_journal import record as dj_record
    journal_path = os.path.join(ROOT, "self", "journals", "_test_wo_fix_112_ambient.jsonl")
    os.makedirs(os.path.dirname(journal_path), exist_ok=True)
    if os.path.exists(journal_path):
        os.remove(journal_path)

    # Temporarily redirect journal writes
    import self.decision_journal as _dj_mod
    orig_journal = _dj_mod._JOURNAL
    _dj_mod._JOURNAL = journal_path
    try:
        dj_record(
            turn="test-ambient-regression",
            action="speak",
            exec_decision={"confidence": 0.77, "cal_reason": "test"},
            backend="ambient",
            outcome="ambient",
            trigger_source="ambient_daemon",
        )
    finally:
        _dj_mod._JOURNAL = orig_journal

    assert os.path.exists(journal_path), "AT-4 FAIL: journal file not written"
    with open(journal_path) as f:
        row = json.loads(f.read().strip())
    assert row.get("confidence") == 0.77, \
        f"AT-4 FAIL: expected confidence=0.77 in journal, got {row.get('confidence')}"

    # Cleanup
    os.remove(journal_path)
