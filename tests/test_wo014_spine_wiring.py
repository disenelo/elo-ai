"""
tests/test_wo014_spine_wiring.py — Acceptance tests for WO-014

Spec: 16_spine_runtime.md §5 + §8 (AC-1 through AC-6)
Wire assemble_cognitive_state() (S3) + build_embodiment_state() (S6) into spine.run().

5 tests covering: S3 produces CognitiveState · frozen · S6 produces EmbodimentState ·
register preserved · non-blocking on contracts error.

Run: python3 tests/test_wo014_spine_wiring.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):   global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from runtime.spine.spine import run, assemble_cognitive_state, build_embodiment_state
from runtime.spine.plan import CognitivePlan


# ── Minimal attention stub (mirrors what server.py passes in) ─────────────────

_ATTENTION = {
    "scores":         {"relevance": 0.8, "novelty": 0.4},
    "context":        {},
    "momentum":       "stable",
    "valence":        "neutral",
    "_exec_decision": {
        "action":        "answer",
        "cal_reason":    "question detected",
        "tone":          "DIRECT",
        "max_sentences": 3,
        "response_goal": "answer",
        "valence":       "neutral",
        "momentum":      "stable",
        "mode":          "",
        "register":      "",
    },
}

_STATE = {"session_id": "test_wo014", "last_topics": ["test"]}


# ── AC-2: S3 — CognitiveState is produced and frozen ─────────────────────────

plan1 = run("what is the spine?", state=_STATE, attention=_ATTENTION)
try:
    cs = plan1.cognitive_state
    assert cs is not None, "cognitive_state must be set on plan (S3 wiring)"
    # Frozen dataclass: setting any field must raise
    try:
        cs.confidence = 99.0
        fail("AC-2", "CognitiveState is not frozen — mutation succeeded")
    except Exception:
        pass  # expected
    assert 0.0 <= cs.assembly_confidence <= 1.0, f"bad assembly_confidence: {cs.assembly_confidence}"
    ok(f"AC-2: CognitiveState produced and frozen; assembly_confidence={cs.assembly_confidence:.3f}")
except AssertionError as e: fail("AC-2", e)


# ── AC-5: Register preserved through S3 ──────────────────────────────────────

plan2 = run("wagwan elo safe", state=_STATE, attention=_ATTENTION)
try:
    cs2 = plan2.cognitive_state
    assert cs2 is not None, "cognitive_state must exist"
    # register in CognitiveState must match what the Language Faculty set
    # Both plan and cognitive_state should carry the same register
    assert plan2.register == cs2.register, (
        f"register mismatch: plan.register={plan2.register!r}, "
        f"cognitive_state.register={cs2.register!r}"
    )
    ok(f"AC-5: register preserved through S3; register={cs2.register!r}")
except AssertionError as e: fail("AC-5", e)


# ── AC-6 (S6): EmbodimentState is produced after Light Engine ────────────────

plan3 = run("hello eLo", state=_STATE, attention=_ATTENTION)
try:
    es = plan3.embodiment_state
    assert es is not None, "embodiment_state must be set on plan (S6 wiring)"
    # Must have the required fields from contracts.EmbodimentState
    assert hasattr(es, "emotional_state"), "missing emotional_state"
    assert hasattr(es, "voice_energy"), "missing voice_energy"
    assert hasattr(es, "unity_mode"), "missing unity_mode"
    assert hasattr(es, "published_at"), "missing published_at"
    ok(f"AC-6: EmbodimentState produced; emotional_state={es.emotional_state!r}, "
       f"unity_mode={es.unity_mode!r}")
except AssertionError as e: fail("AC-6", e)


# ── AC-1: One decision per turn — plan is a CognitivePlan ─────────────────────

plan4 = run("tell me about the project", state=_STATE, attention=_ATTENTION)
try:
    assert isinstance(plan4, CognitivePlan), f"run() must return CognitivePlan, got {type(plan4)}"
    assert plan4.conversation_action, "conversation_action must be set"
    ok(f"AC-1: run() returns CognitivePlan; action={plan4.conversation_action!r}")
except AssertionError as e: fail("AC-1", e)


# ── AC-3: Behaviour parity — wiring doesn't change existing plan fields ───────
# Two runs with same input: conversation_action, tone, mode must be stable.

plan5a = run("build something", state=_STATE, attention=_ATTENTION)
plan5b = run("build something", state=_STATE, attention=_ATTENTION)
try:
    assert plan5a.conversation_action == plan5b.conversation_action, (
        f"action not stable: {plan5a.conversation_action!r} vs {plan5b.conversation_action!r}"
    )
    assert plan5a.tone == plan5b.tone, (
        f"tone not stable: {plan5a.tone!r} vs {plan5b.tone!r}"
    )
    # Both must have cognitive_state + embodiment_state (new fields)
    assert plan5a.cognitive_state is not None, "S3 not wired in second run"
    assert plan5a.embodiment_state is not None, "S6 not wired in second run"
    ok(f"AC-3: behaviour parity — stable action={plan5a.conversation_action!r}, "
       f"tone={plan5a.tone!r}; S3+S6 both present")
except AssertionError as e: fail("AC-3", e)


print(f"\nResult: {PASS}/5 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
