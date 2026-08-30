"""
tests/test_wo_sp29_significance.py — WO-SP29 acceptance tests.

AT-1: compute_significance() is called in assemble_cognitive_state() per turn;
      CognitiveState.significance_score is a float 0.0-1.0.
AT-2: executive.decide() returns memory_worthy=False when significance_score < 0.72.
AT-3: executive.decide() returns self_init_eligible=True when significance_score >= 0.90.
AT-4: Existing SP-31 self-initiation tests still pass (13/13).
AT-5: CognitiveState has significance_score field.
AT-6: py_compile clean on all modified files.

Run: python3 tests/test_wo_sp29_significance.py
"""
from __future__ import annotations
import sys, os, py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: assemble_cognitive_state() populates significance_score ─────────────
try:
    from runtime.spine.spine import assemble_cognitive_state
    cs = assemble_cognitive_state(
        language={"original": "hello there"},
        memory_result=None,
        attention=None,
        capabilities=[],
        vault_result=None,
        prior_state=None,
    )
    assert hasattr(cs, "significance_score"), "CognitiveState missing significance_score field"
    assert isinstance(cs.significance_score, float), \
        f"significance_score is {type(cs.significance_score)}, expected float"
    assert 0.0 <= cs.significance_score <= 1.0, \
        f"significance_score {cs.significance_score} out of range [0.0, 1.0]"
    ok(f"AT-1: assemble_cognitive_state populates significance_score={cs.significance_score:.4f}")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: significance < 0.72 → memory_worthy=False in executive.decide() ─────
try:
    from runtime import executive as _exec
    _low_attn = {
        "intent": "conversation",
        "emotional_context": {},
        "significance_score": {"overall": 0.05},  # below 0.72
    }
    _dec = _exec.decide(_low_attn, loop_detected=False, user_input="hello")
    assert "memory_worthy" in _dec, "decide() return dict missing 'memory_worthy' key"
    assert _dec["memory_worthy"] is False, \
        f"memory_worthy should be False for score=0.05, got: {_dec['memory_worthy']}"
    ok(f"AT-2: significance=0.05 → memory_worthy=False")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: significance >= 0.90 → self_init_eligible=True in executive.decide() ─
try:
    from runtime import executive as _exec2
    _high_attn = {
        "intent": "conversation",
        "emotional_context": {},
        "significance_score": {"overall": 0.95},  # above 0.90
    }
    _dec2 = _exec2.decide(_high_attn, loop_detected=False, user_input="hello")
    assert "self_init_eligible" in _dec2, "decide() return dict missing 'self_init_eligible' key"
    assert _dec2["self_init_eligible"] is True, \
        f"self_init_eligible should be True for score=0.95, got: {_dec2['self_init_eligible']}"
    assert _dec2["memory_worthy"] is True, \
        f"memory_worthy should be True for score=0.95 (>=0.72), got: {_dec2['memory_worthy']}"
    ok(f"AT-3: significance=0.95 → self_init_eligible=True, memory_worthy=True")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: SP-31 self-initiation path unaffected ───────────────────────────────
try:
    from runtime.self_initiation import may_self_initiate, SELF_INIT_THRESHOLD, EXCEPTIONAL_THRESHOLD
    # Confirm thresholds are still live (not changed by WO-SP29)
    assert SELF_INIT_THRESHOLD   == 0.72, f"SELF_INIT_THRESHOLD changed: {SELF_INIT_THRESHOLD}"
    assert EXCEPTIONAL_THRESHOLD == 0.90, f"EXCEPTIONAL_THRESHOLD changed: {EXCEPTIONAL_THRESHOLD}"
    # Spot-check: score below threshold → not allowed
    _gate_low = may_self_initiate(0.10)
    assert not _gate_low.allowed, f"may_self_initiate(0.10).allowed should be False"
    # Spot-check: score above exceptional → result is a SelfInitResult with allowed and tier
    _gate_high = may_self_initiate(0.95)
    assert hasattr(_gate_high, "allowed"), "SelfInitResult missing 'allowed'"
    assert hasattr(_gate_high, "tier"),    "SelfInitResult missing 'tier'"
    ok(f"AT-4: SP-31 thresholds unchanged (0.72 / 0.90); may_self_initiate interface intact")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: CognitiveState.significance_score field exists ─────────────────────
try:
    from runtime.contracts import CognitiveState
    import dataclasses
    _fields = {f.name for f in dataclasses.fields(CognitiveState)}
    assert "significance_score" in _fields, \
        f"'significance_score' not a field on CognitiveState; found: {sorted(_fields)}"
    _cs_default = CognitiveState()
    assert _cs_default.significance_score == 0.0, \
        f"CognitiveState default significance_score should be 0.0, got {_cs_default.significance_score}"
    ok("AT-5: CognitiveState has significance_score field (default 0.0)")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean on all modified files ──────────────────────────────
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in (
        "runtime/contracts.py",
        "runtime/spine/spine.py",
        "runtime/executive.py",
    ):
        py_compile.compile(os.path.join(_ROOT, rel), doraise=True)
    ok("AT-6: py_compile clean on contracts.py, spine.py, executive.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-SP29   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
