"""
tests/test_wo112_choose_confidence.py — WO-112: confidence flows from exec_out to journal.

AT-112-1: executive.decide() returns confidence in output dict
AT-112-2: spine._executive_faculty() sets plan.confidence from exec_out
AT-112-3: server.py builds exec_decision with confidence key from plan
AT-112-4: decision_journal.record() writes non-null confidence when exec_decision has it
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-112-1: executive.decide() includes confidence ────────────────────────

def test_executive_decide_returns_confidence():
    from runtime.executive import decide
    result = decide({"intent": "inquiry", "valence": "neutral", "momentum": "stable"},
                    user_input="what time is it?")
    assert "confidence" in result, \
        "executive.decide() missing 'confidence' key — WO-112 prerequisite not met"
    assert result["confidence"] is not None, \
        "executive.decide() returned confidence=None — must be a float"
    assert isinstance(result["confidence"], (int, float)), \
        f"confidence must be numeric, got: {type(result['confidence'])}"


# ── AT-112-2: spine._executive_faculty() threads confidence onto plan ────────

def test_executive_faculty_sets_plan_confidence():
    from unittest.mock import patch
    import runtime.spine.spine as _spine_mod
    from runtime.spine.plan import CognitivePlan

    FIXED_CONFIDENCE = 0.92

    def _mock_decide(attention_in, loop_detected=False, user_input=""):
        return {
            "action": "answer", "confidence": FIXED_CONFIDENCE, "cal_reason": "test",
            "tone": "DIRECT", "max_sentences": 2, "response_goal": "answer",
            "valence": "neutral", "momentum": "stable", "mode": "",
        }

    with patch("runtime.executive.decide", _mock_decide):
        plan = _spine_mod._executive_faculty(
            raw="test", language={"meaning": "test", "intent": "inquiry",
                                   "register": "", "social": "", "confidence": 0.8},
            attention={}, capabilities=[], system_det=None,
        )

    assert abs(plan.confidence - FIXED_CONFIDENCE) < 0.001, (
        f"_executive_faculty did not set plan.confidence from exec_out: "
        f"expected {FIXED_CONFIDENCE}, got {plan.confidence}"
    )


# ── AT-112-3: server.py includes confidence when building exec_decision ──────

def test_server_exec_decision_includes_confidence():
    src_path = os.path.join(ROOT, "server.py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    # Find the exec_decision dict built from _plan (not the fallback exec_decide call)
    idx = src.find('"confidence":    _plan.confidence')
    assert idx != -1, (
        "server.py exec_decision dict does not include 'confidence': _plan.confidence — "
        "WO-112 not applied; journal will continue to write confidence=null"
    )


# ── AT-112-4: decision_journal writes non-null confidence ───────────────────

def test_decision_journal_writes_confidence():
    from self.decision_journal import record
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w")
    tmp.close()

    import self.decision_journal as _dj
    orig_journal = _dj._JOURNAL
    _dj._JOURNAL = tmp.name
    try:
        record(
            turn="what time is it?",
            action="answer",
            exec_decision={"action": "answer", "confidence": 0.95,
                            "cal_reason": "test-AT-112"},
            backend="test",
            outcome="success",
        )
        with open(tmp.name, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
        assert entries, "decision_journal.record() wrote nothing"
        entry = entries[0]
        assert "confidence" in entry, f"journal entry missing 'confidence': {entry}"
        assert entry["confidence"] == 0.95, (
            f"journal entry confidence wrong: expected 0.95, got {entry['confidence']}"
        )
    finally:
        _dj._JOURNAL = orig_journal
        os.unlink(tmp.name)
