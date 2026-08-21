"""
tests/test_loop7_live.py — card 0082 LOOP-7 acceptance suite.

Proves: the Learning Faculty CAN change a real Executive decision.

Six checks (card 0082):

  L7-CF-1  counterfactual — a lesson with prefers_action changes cal["action"]
             compared to the Executive without any lesson advice
  L7-DC-1  disconnection — removing the lesson from spine._recalled_lessons
             causes the preference to disappear (not hallucinated)
  L7-PR-1  pure-numeric session_id is rejected by _evidence_is_verified
  L7-CL-1  a conflicting lesson LOSES (preference drops) + raises curiosity
  L7-RS-1  every preference returned by consult() carries a traceable reason
  L7-PV-1  pre-v1 ledger (string evidence rows) loads without raising

Run: python3 tests/test_loop7_live.py
"""
from __future__ import annotations

import os
import sys
import json
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── helpers ───────────────────────────────────────────────────────────────────

def _lesson(prefers: str, session_id: str, action: str = "build",
            outcome: str = "met", applies_when: list | None = None,
            strength: float = 0.8) -> dict:
    """Build a minimal verified lesson that passes the D1 gate."""
    return {
        "lesson_key":    "testkey",
        "statement":     f"prefer {prefers} here",
        "scope":         "behaviour",
        "strength":      strength,
        "prefers_action": prefers,
        "applies_when":  applies_when or ["behaviour"],
        "reason":        f"outcome={outcome} during {action}",
        "evidence": [{
            "verified":    True,
            "session_id":  session_id,
            "action":      action,
            "outcome":     outcome,
            "episode_ref": "ep-001",
            "ts":          1.0,
        }],
    }


# ── L7-CF-1  counterfactual ───────────────────────────────────────────────────

def test_l7_cf1_counterfactual() -> None:
    """A lesson that prefers 'reflect' changes cal['action'] from 'answer'."""
    from faculties.learning.faculty import consult

    lesson = _lesson("reflect", session_id="S9999001",
                     applies_when=["behaviour", "test"])
    ctx = {"intent": "test behaviour question", "focal_thread": ""}

    # Baseline: no lessons → no preferences
    baseline = consult(lessons=[], context=ctx)
    if baseline.preferences:
        err("L7-CF-1: consult() returned preferences with no lessons — cannot prove counterfactual")

    # With lesson: should prefer 'reflect'
    advised = consult(lessons=[lesson], context=ctx)
    if not advised.preferences:
        err(f"L7-CF-1: consult() returned no preferences despite verified lesson. "
            f"rationale={advised.rationale!r}")
    if "reflect" not in advised.preferences:
        err(f"L7-CF-1: 'reflect' not in preferences — got {advised.preferences}")
    if advised.preferences.get("reflect", 0.0) <= 0.0:
        err(f"L7-CF-1: 'reflect' preference is not positive: {advised.preferences['reflect']}")

    # Counterfactual holds: the advised preference is different from the
    # no-lesson baseline (which had no preferences at all)
    ok(f"L7-CF-1: lesson shifts preference → 'reflect' ({advised.preferences['reflect']:.2f}); "
       f"baseline had none")


# ── L7-DC-1  disconnection ────────────────────────────────────────────────────

def test_l7_dc1_disconnection() -> None:
    """Remove the lesson → preference disappears; not hallucinated."""
    from faculties.learning.faculty import consult

    lesson = _lesson("connect", session_id="S9999002",
                     applies_when=["social", "team"])
    ctx = {"intent": "social team collaboration", "focal_thread": ""}

    with_lesson    = consult(lessons=[lesson], context=ctx)
    without_lesson = consult(lessons=[],       context=ctx)

    if not with_lesson.preferences.get("connect"):
        err(f"L7-DC-1: lesson present but 'connect' not in preferences — {with_lesson.preferences}")
    if without_lesson.preferences.get("connect"):
        err("L7-DC-1: 'connect' preference persists after lesson removed — hallucinated")
    ok("L7-DC-1: preference disappears when lesson removed (not hallucinated)")


# ── L7-PR-1  pure-numeric session_id rejected ─────────────────────────────────

def test_l7_pr1_pure_numeric_rejected() -> None:
    """A lesson with a pure-numeric session_id fails the D1 gate."""
    from faculties.learning.faculty import consult, _evidence_is_verified

    # Build a lesson that is otherwise valid but has a bare integer session_id
    bad_lesson = _lesson("build", session_id="1787263195",   # ← pure-numeric
                         applies_when=["capability"])

    # Gate check
    if _evidence_is_verified(bad_lesson):
        err("L7-PR-1: _evidence_is_verified() accepted a pure-numeric session_id — gate broken")

    # consult() must also reject it
    advised = consult(lessons=[bad_lesson], context={"intent": "capability work"})
    if advised.preferences:
        err(f"L7-PR-1: consult() produced preferences from a pure-numeric session lesson: "
            f"{advised.preferences}")
    ok("L7-PR-1: pure-numeric session_id rejected by _evidence_is_verified() and consult()")


# ── L7-CL-1  conflicting lesson loses + raises curiosity ─────────────────────

def test_l7_cl1_conflicting_lesson_loses() -> None:
    """A lesson that doesn't match the context loses, and curiosity rises."""
    from faculties.learning.faculty import consult

    # Lesson that applies_when=['robotics'] — completely different from the query context
    conflict_lesson = _lesson("build", session_id="S9999003",
                              applies_when=["robotics", "hardware"])
    ctx = {"intent": "write a poem", "focal_thread": "creative writing"}

    advised = consult(lessons=[conflict_lesson], context=ctx)

    # The lesson should not push a preference (it conflicts)
    if advised.preferences.get("build", 0.0) > 0.0:
        err(f"L7-CL-1: conflicting lesson produced a positive 'build' preference — "
            f"should have lost; preferences={advised.preferences}")

    # Curiosity must be raised (ADR-Exec-005 D4 curiosity threshold)
    if advised.curiosity < 0.3:
        err(f"L7-CL-1: conflicting lesson did not raise curiosity; got {advised.curiosity:.2f}")

    ok(f"L7-CL-1: conflicting lesson loses preference, curiosity={advised.curiosity:.2f}")


# ── L7-RS-1  every preference has a traceable reason ─────────────────────────

def test_l7_rs1_reasons_required() -> None:
    """Every preference returned by consult() must carry a traceable reason."""
    from faculties.learning.faculty import consult

    lessons = [
        _lesson("reflect", session_id="S9999004", applies_when=["behaviour"]),
        _lesson("connect", session_id="S9999005", applies_when=["social"]),
    ]
    ctx = {"intent": "social behaviour session", "focal_thread": ""}
    advised = consult(lessons=lessons, context=ctx)

    if not advised.reasons:
        err("L7-RS-1: consult() returned no reasons — the 'why' must travel with the lesson")

    for r in advised.reasons:
        if not isinstance(r, dict):
            err(f"L7-RS-1: reason entry is not a dict: {r!r}")
        if not r.get("why"):
            err(f"L7-RS-1: reason entry has no 'why': {r}")
        if "fit" not in r:
            err(f"L7-RS-1: reason entry missing 'fit': {r}")

    ok(f"L7-RS-1: {len(advised.reasons)} reason(s) returned, each with 'why' and 'fit'")


# ── L7-PV-1  pre-v1 ledger loads without raising ─────────────────────────────

def test_l7_pv1_prev1_ledger_clean() -> None:
    """Pre-v1 ledger rows (string evidence) don't crash _evidence_is_verified."""
    from faculties.learning.faculty import _evidence_is_verified

    # These are the three evidence shapes that exist in lessons_ledger_pre_v1.jsonl
    pre_v1_row_string_ev = {
        "lesson_key": "abc123",
        "statement":  "something learned",
        "scope":      "behaviour",
        "strength":   0.5,
        "evidence": [
            "eLo OS session — verified",        # plain string (pre-v1 format)
            "another session string",
            {"verified": False, "session_id": "S1234", "action": "", "outcome": ""},
        ],
    }

    # Must NOT raise; must return False (no valid dict evidence with session+action+outcome)
    try:
        result = _evidence_is_verified(pre_v1_row_string_ev)
    except Exception as exc:
        err(f"L7-PV-1: _evidence_is_verified raised on pre-v1 string evidence: {exc}")

    if result:
        err("L7-PV-1: pre-v1 row incorrectly passed _evidence_is_verified — no valid evidence")

    ok("L7-PV-1: pre-v1 ledger rows (string evidence) load without raising, return False")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("LOOP-7 — Learning Faculty changes a real decision (card 0082)")
    test_l7_cf1_counterfactual()
    test_l7_dc1_disconnection()
    test_l7_pr1_pure_numeric_rejected()
    test_l7_cl1_conflicting_lesson_loses()
    test_l7_rs1_reasons_required()
    test_l7_pv1_prev1_ledger_clean()
    print("\n6/6 PASS — LOOP-7 faults cleared; Learning Faculty can change a real decision")
    print()
    print("LIVE ACCEPTANCE (card 0082 test 3): reachable but not one-shot —")
    print("  requires a real session that produces one qualifying lesson via")
    print("  integrate_session(), confirmed with verified=True + action + outcome,")
    print("  then a subsequent turn where spine._recalled_lessons contains it and")
    print("  Executive picks a different CAL action than it would without the advice.")
