"""
tests/test_wo_conv_authority_001.py — WO-CONV-AUTHORITY-001
Explicit conversation authority gate: current statement outranks stale inference.

AT-1  "Not sending anything out" → explicit_correction_detected = True
AT-2  Correction annotates stale_inference_tier = "unknown" in correction context
AT-3  Non-correction turns → explicit_correction_detected = False, no side effects
AT-4  CognitivePlan has explicit_correction_detected field (default False)
AT-5  correction_applied present in build_correction_context() output
"""
from __future__ import annotations
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── AT-1: correction phrases → explicit_correction_detected = True ─────────────
def test_at1_correction_detected():
    """AT-1: known correction phrases → detect_explicit_correction returns True."""
    from runtime.conv_authority import detect_explicit_correction
    correction_examples = [
        "Not sending anything out.",
        "No, I never said that.",
        "That's not what I meant.",
        "I'm not going with that direction.",
        "No, that's wrong.",
        "I didn't say that.",
        "I didn't mean that.",
    ]
    for phrase in correction_examples:
        result = detect_explicit_correction(phrase)
        assert result is True, \
            f"AT-1: expected True for correction phrase {phrase!r}, got {result!r}"
    ok(f"AT-1: {len(correction_examples)} correction phrases detected correctly")


# ── AT-2: correction context marks stale_inference_tier as unknown ─────────────
def test_at2_stale_inference_downgraded():
    """AT-2: build_correction_context() returns stale_inference_tier='unknown'."""
    from runtime.conv_authority import build_correction_context
    ctx = build_correction_context("Not sending anything out.")
    assert ctx.get("stale_inference_tier") == "unknown", \
        f"AT-2: stale_inference_tier={ctx.get('stale_inference_tier')!r}, expected 'unknown'"
    assert ctx.get("authority_level") == "explicit_current_statement", \
        f"AT-2: authority_level={ctx.get('authority_level')!r}"
    ok("AT-2: correction context marks stale_inference_tier='unknown', "
       "authority_level='explicit_current_statement'")


# ── AT-3: non-correction turns → False, no side effects ──────────────────────
def test_at3_non_correction_false():
    """AT-3: normal conversational phrases → detect_explicit_correction = False."""
    from runtime.conv_authority import detect_explicit_correction
    non_corrections = [
        "What should I do next?",
        "Let me think about that.",
        "Maybe we can try tomorrow.",
        "That's interesting.",
        "I haven't decided yet.",
        "What do you think?",
    ]
    for phrase in non_corrections:
        result = detect_explicit_correction(phrase)
        assert result is False, \
            f"AT-3: expected False for non-correction {phrase!r}, got {result!r}"
    ok(f"AT-3: {len(non_corrections)} non-correction phrases correctly return False")


# ── AT-4: CognitivePlan has explicit_correction_detected field ────────────────
def test_at4_cognitive_plan_field():
    """AT-4: CognitivePlan.explicit_correction_detected exists with default False."""
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan()
    assert hasattr(plan, "explicit_correction_detected"), \
        "AT-4: CognitivePlan missing explicit_correction_detected field"
    assert plan.explicit_correction_detected is False, \
        f"AT-4: explicit_correction_detected default={plan.explicit_correction_detected!r}, expected False"
    ok("AT-4: CognitivePlan.explicit_correction_detected = False by default")


# ── AT-5: correction_applied in build_correction_context() ───────────────────
def test_at5_correction_applied_logged():
    """AT-5: build_correction_context() includes correction_applied=True."""
    from runtime.conv_authority import build_correction_context
    ctx = build_correction_context("Not sending anything out.")
    assert ctx.get("correction_applied") is True, \
        f"AT-5: correction_applied={ctx.get('correction_applied')!r}, expected True"
    assert ctx.get("explicit_correction_detected") is True, \
        "AT-5: explicit_correction_detected missing from correction context"
    ok("AT-5: correction_applied=True and explicit_correction_detected=True in context")


# ── runner ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("WO-CONV-AUTHORITY-001 — Explicit conversation authority gate")
    print("Source: eLo Intent Alignment §5 + eLo Response Authority §6")
    print()
    test_at1_correction_detected()
    test_at2_stale_inference_downgraded()
    test_at3_non_correction_false()
    test_at4_cognitive_plan_field()
    test_at5_correction_applied_logged()
    print()
    print("5/5 PASS — explicit correction detected, stale inference downgraded to UNKNOWN")
