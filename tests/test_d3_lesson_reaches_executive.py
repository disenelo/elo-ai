"""
tests/test_d3_lesson_reaches_executive.py — Card 0075 (D3 · Option A · David L3 2026-08-21)

Governing law: docs/architecture/adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md
  D1  "Language alone is never evidence. Only executed actions with verified
       consequences influence future policy."
  D6  Learning Faculty is a faculty the Executive ASKS — never inside the Executive.

David's ruling:
  Option A — add `lessons` to ExecutiveContext ONLY. The frozen executive.decide()
  reads its context as a flat dict via as_dict(); a new key may be readable
  without editing the frozen file.

This card is a MEASUREMENT before it is a change. The counterfactual:
    same input, action WITH lesson present  vs.  action WITHOUT lesson
    → if identical, the frozen logic does NOT consult the key,
      lesson_id stays "", LOOP-7 stays UNKNOWN. Reported honestly.

Tests:
    1. ExecutiveContext carries `lessons` field; as_dict() exposes it at
       top-level key `"lessons"` (so a frozen reader would find it if written to).
    2. Counterfactual: identical input, decide() output byte-identical WITH
       lessons present vs absent — proves the frozen file does NOT read the key.
    3. Disconnection test: remove the `lessons` key entirely → still identical
       (belt-and-braces confirmation that the frozen executive is lesson-blind).
    4. plan.lesson_id policy: stays "" unless the counterfactual holds (it
       does not, so this test asserts the current honest state = "").
    5. runtime/executive.py is byte-identical to the pre-card hash — proves
       the frozen file was never touched.
    6. D1 gate — a lesson whose evidence is language-only (no verified entry)
       is REJECTED from ExecutiveContext.lessons.
    7. D1 gate — a lesson whose only verified session_id is a pure-numeric
       process id is REJECTED (called out explicitly by card 0075).

Run: python3 tests/test_d3_lesson_reaches_executive.py
"""
from __future__ import annotations

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_ok  = lambda msg: print(f"  PASS  {msg}")
_err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# Pre-card frozen hash of runtime/executive.py, captured before this card began.
# If executive.py ever changes byte-for-byte, this test goes RED — Rule 3
# (LANE) enforcement at the test layer.
_EXECUTIVE_FROZEN_SHA1 = "fd090c9719ec064c1ae2c3363a70e02bd8c48706"  # updated 2026-09-03: South London greeting routing (Builder seat, David-authorized)


def test_1_executive_context_carries_lessons():
    from runtime.executive_context import ExecutiveContext
    ec = ExecutiveContext()
    if not hasattr(ec, "lessons"):
        _err("1: ExecutiveContext missing `lessons` attribute")
    if ec.lessons != []:
        _err(f"1: default lessons should be [] — got {ec.lessons!r}")
    d = ec.as_dict()
    if "lessons" not in d:
        _err("1: as_dict() must expose top-level key 'lessons' (a frozen reader would look for that name)")
    _ok("1: ExecutiveContext.lessons exists, defaults to [], surfaced by as_dict() at top-level key 'lessons'")


def _sample_input():
    """Neutral conversational input that falls through _conversation_action to the default branch."""
    return {
        "intent": "conversation",
        "emotional_context": {
            "inferred_state": "present",
            "valence":  "neutral",
            "momentum": "stable",
            "closure":  "open",
            "energy":   0.5,
            "tension":  0.4,
        },
        "wm_winner": "",
        "wm_mode":   "reactive",
        "wm_budget": 0.5,
        "world_state": {"available": True, "route_history": []},
    }


def _fake_lesson():
    """A lesson row that clears the D1 gate — verified evidence, non-numeric session_id."""
    return {
        "lesson_key": "abc123deadbeef",
        "statement":  "David likes short answers first",
        "status":     "confirmed",
        "strength":   0.90,
        "scope":      "communication",
        "evidence":   [
            {"episode_ref": "ep-1", "verified": True, "ts": 1755000000.0,
             "session_id": "eLo OS", "contradicting": False},
            {"episode_ref": "ep-2", "verified": True, "ts": 1755100000.0,
             "session_id": "eLo OS", "contradicting": False},
        ],
    }


def test_2_counterfactual_frozen_logic_does_not_read_lessons():
    """
    The whole point of the card: does the frozen executive.decide() change its
    output when `lessons` is present vs absent?
    """
    from runtime.executive import decide

    base = _sample_input()

    with_lesson    = dict(base); with_lesson["lessons"]    = [_fake_lesson()]
    without_lesson = dict(base); without_lesson["lessons"] = []

    out_with    = decide(with_lesson,    loop_detected=False, user_input="i've been thinking")
    out_without = decide(without_lesson, loop_detected=False, user_input="i've been thinking")

    if out_with != out_without:
        _err(f"2: counterfactual UNEXPECTEDLY HOLDS — frozen executive appears to read `lessons`.\n"
             f"    WITH:    {out_with}\n    WITHOUT: {out_without}")
    _ok("2: counterfactual DOES NOT HOLD — frozen executive.decide() output is identical WITH vs WITHOUT lessons")
    _ok("   → LOOP-7 stays UNKNOWN. Honest negative result. plan.lesson_id must stay ''")


def test_3_disconnection_missing_key_still_identical():
    """Belt-and-braces: also remove the `lessons` key entirely — result unchanged."""
    from runtime.executive import decide

    base = _sample_input()
    with_lesson = dict(base); with_lesson["lessons"] = [_fake_lesson()]
    # base has NO `lessons` key at all

    out_with = decide(with_lesson, loop_detected=False, user_input="i've been thinking")
    out_no_key = decide(base,      loop_detected=False, user_input="i've been thinking")

    if out_with != out_no_key:
        _err(f"3: removing `lessons` key changed output — the frozen file IS reading it.\n"
             f"    WITH KEY: {out_with}\n    NO KEY:   {out_no_key}")
    _ok("3: disconnection test — output identical whether the key is present or absent")


def test_4_lesson_id_gated_on_counterfactual():
    """
    plan.lesson_id must be "" until the counterfactual holds. Since test 2
    proves it does not, spine.py must set lesson_id="" unconditionally.
    """
    src = open(os.path.join(ROOT, "runtime", "spine", "spine.py"), encoding="utf-8").read()
    if 'plan.lesson_id = ""' not in src:
        _err("4: spine.py must set `plan.lesson_id = \"\"` (attribution gated on counterfactual)")
    _ok("4: spine.py holds lesson_id=\"\" — attribution correctly withheld while counterfactual is FALSE")


def test_5_executive_py_byte_identical():
    """Rule 3 (LANE) at the test layer — the frozen file's SHA-1 must not change."""
    p = os.path.join(ROOT, "runtime", "executive.py")
    with open(p, "rb") as f:
        h = hashlib.sha1(f.read()).hexdigest()
    if h != _EXECUTIVE_FROZEN_SHA1:
        _err(f"5: runtime/executive.py CHANGED — expected {_EXECUTIVE_FROZEN_SHA1}, got {h}")
    _ok(f"5: runtime/executive.py byte-identical (sha1={h})")


def test_6_d1_gate_rejects_language_only_lesson():
    """
    ADR-Exec-005 D1: language alone is never evidence. A lesson with zero
    verified evidence entries must not enter ExecutiveContext.lessons.
    """
    from runtime.executive_context import build_executive_context

    language_only = {
        "lesson_key": "lang-only-1",
        "statement":  "eLo said something reflective once",
        "status":     "confirmed",
        "strength":   0.80,
        "scope":      "communication",
        "evidence":   [
            {"episode_ref": "ep-lang-1", "verified": False, "ts": 1755000000.0,
             "session_id": "eLo OS"},
        ],
    }

    ec = build_executive_context(
        intent="conversation",
        emotional_context={},
        world=None,
        working_memory=None,
        capabilities=[],
        cognitive_state=None,
        affordances=None,
        attention={},
        lessons=[language_only],
    )
    if ec.lessons:
        _err(f"6: language-only lesson passed the D1 gate — must be rejected. got {ec.lessons}")
    _ok("6: D1 gate rejects language-only lesson (no verified evidence entry)")


def test_7_d1_gate_rejects_pure_numeric_session_id():
    """
    Card 0075: "one was promoted on session IDs that were process numbers."
    A lesson whose only verified session_id is pure digits (a pid, not a
    session) must not enter ExecutiveContext.lessons.
    """
    from runtime.executive_context import build_executive_context

    pid_session = {
        "lesson_key": "pid-1",
        "statement":  "capability milestone reached",
        "status":     "confirmed",
        "strength":   0.90,
        "scope":      "capability",
        "evidence":   [
            {"episode_ref": "ep-pid-1", "verified": True, "ts": 1755000000.0,
             "session_id": "1787122077"},
            {"episode_ref": "ep-pid-2", "verified": True, "ts": 1755100000.0,
             "session_id": "1787261879"},
        ],
    }

    ec = build_executive_context(
        intent="conversation",
        emotional_context={},
        world=None,
        working_memory=None,
        capabilities=[],
        cognitive_state=None,
        affordances=None,
        attention={},
        lessons=[pid_session],
    )
    if ec.lessons:
        _err(f"7: pure-numeric session_id lesson passed the D1 gate — must be rejected. got {ec.lessons}")
    _ok("7: D1 gate rejects lesson whose only verified session_id is a pure-numeric process id")


if __name__ == "__main__":
    print("Card 0075 — D3 · Option A · lessons reach ExecutiveContext")
    print("Governing law: ADR-Exec-005 (D1 verified-evidence gate · D6 no learning inside Executive)")
    print()
    test_1_executive_context_carries_lessons()
    test_2_counterfactual_frozen_logic_does_not_read_lessons()
    test_3_disconnection_missing_key_still_identical()
    test_4_lesson_id_gated_on_counterfactual()
    test_5_executive_py_byte_identical()
    test_6_d1_gate_rejects_language_only_lesson()
    test_7_d1_gate_rejects_pure_numeric_session_id()
    print()
    print("7/7 PASS — Card 0075 done.")
    print()
    print("RESULT REPORTED (D3 · Option A · empirical):")
    print("  · does frozen executive.decide() read the new `lessons` key?  NO")
    print("  · counterfactual (WITH vs WITHOUT):                           IDENTICAL output")
    print("  · plan.lesson_id:                                             \"\" (unchanged)")
    print("  · LOOP-7:                                                     UNKNOWN (unchanged)")
    print("  · runtime/executive.py:                                       byte-identical")
    print()
    print("This is the honest negative result the card asked for. Option B is")
    print("forbidden by ADR-Exec-005 D6. A real learning path now requires either")
    print("(a) unfreezing executive.py behind an ADR-Exec-005 D6 Learning-Faculty")
    print("consult, or (b) a David-ruled option C.")
