"""
tests/test_wo017_movement_trace.py — Acceptance tests for WO-017

Spec: DISPATCH_BOARD §WO-017 / D-L decision
Trace why the avatar moved: Python logs movement_intent/movement_trigger +
driving state (which layer fired, why) → plan.movement_debug + blender_state.json.

6 tests covering each major layer + trace shape.

Run: python3 tests/test_wo017_movement_trace.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from runtime.spine.presence_faculty import compute, _last_non_empty_intent_ts
import runtime.spine.presence_faculty as _pf
from runtime.spine.plan import CognitivePlan


# ── Minimal attention stub ────────────────────────────────────────────────────

def _attn(momentum="stable", valence="neutral", energy=0.5, load="medium"):
    return {
        "emotional_context": {
            "momentum": momentum,
            "valence":  valence,
            "energy":   energy,
        },
        "_exec_decision": {"cognitive_load": load},
    }


def _plan(**kw) -> CognitivePlan:
    p = CognitivePlan(**kw)
    p.presence_plan = {}
    return p


# ── AT-1: Signal word fires → layer = "signal_word" ──────────────────────────

# Force grace window to be inactive (set last intent to long ago)
_pf._last_non_empty_intent_ts = 0.0

p1 = _plan(raw="can you explore a bit", tone="DIRECT", conversation_action="answer",
           intent="conversation")
result1 = compute(p1, _attn())
try:
    dbg = result1.movement_debug
    assert dbg, "movement_debug must be populated"
    assert dbg["layer"] == "signal_word", f"expected signal_word, got {dbg['layer']!r}"
    assert result1.movement_intent == "explore", f"expected explore, got {result1.movement_intent!r}"
    assert "explore" in dbg["reason"].lower(), f"reason should mention 'explore': {dbg['reason']!r}"
    assert "raw_snippet" in dbg["state"], "state must include raw_snippet"
    ok(f"AT-1: signal_word layer → intent={result1.movement_intent!r}; reason={dbg['reason']!r}")
except AssertionError as e: fail("AT-1", e)


# ── AT-2: Light engine emotional state fires → layer = "light_engine" ────────

_pf._last_non_empty_intent_ts = 0.0

p2 = _plan(raw="let me think about that", tone="DIRECT", conversation_action="answer",
           intent="inquiry")
p2.presence_plan = {"emotional_state": "curiosity"}
result2 = compute(p2, _attn(energy=0.3))  # energy < 0.55 so inquiry branch doesn't fire
try:
    dbg = result2.movement_debug
    assert dbg["layer"] == "light_engine", f"expected light_engine, got {dbg['layer']!r}"
    assert result2.movement_intent == "go_top", f"expected go_top (curiosity→go_top), got {result2.movement_intent!r}"
    assert "curiosity" in dbg["reason"], f"reason should mention curiosity: {dbg['reason']!r}"
    ok(f"AT-2: light_engine layer → intent={result2.movement_intent!r}; reason={dbg['reason']!r}")
except AssertionError as e: fail("AT-2", e)


# ── AT-3: Settle grace fires → layer = "grace", intent = "" ─────────────────

import time as _time
_pf._last_non_empty_intent_ts = _time.time()  # just settled

p3 = _plan(raw="that makes sense", tone="DIRECT", conversation_action="answer",
           intent="conversation")
p3.presence_plan = {"emotional_state": ""}
result3 = compute(p3, _attn())
try:
    dbg = result3.movement_debug
    assert dbg["layer"] == "grace", f"expected grace, got {dbg['layer']!r}"
    assert result3.movement_intent == "", f"expected empty intent in grace, got {result3.movement_intent!r}"
    assert "grace" in dbg["reason"].lower() or "hold" in dbg["reason"].lower(), (
        f"reason should mention grace/hold: {dbg['reason']!r}"
    )
    ok(f"AT-3: grace layer → intent=''; reason={dbg['reason']!r}")
except AssertionError as e: fail("AT-3", e)


# ── AT-4: Distress (negative_high valence) → layer = "distress" ──────────────

_pf._last_non_empty_intent_ts = 0.0

# NOTE: input must not contain signal words (e.g. "stuck"/"frustrated" → "grounding"
# via signal_word layer which has higher priority than distress). Use purely emotional
# phrasing that has no movement signal words so valence drives the layer.
p4 = _plan(raw="everything feels impossible today", tone="DIRECT", conversation_action="ground",
           intent="emotional")
p4.presence_plan = {"emotional_state": ""}
result4 = compute(p4, _attn(valence="negative_high"))
try:
    dbg = result4.movement_debug
    assert dbg["layer"] == "distress", f"expected distress, got {dbg['layer']!r}"
    assert result4.movement_intent == "grounding", (
        f"expected grounding, got {result4.movement_intent!r}"
    )
    assert "negative_high" in dbg["reason"], f"reason should mention negative_high: {dbg['reason']!r}"
    ok(f"AT-4: distress layer → intent={result4.movement_intent!r}; reason={dbg['reason']!r}")
except AssertionError as e: fail("AT-4", e)


# ── AT-5: Fallback → layer = "fallback", intent = "" ────────────────────────

_pf._last_non_empty_intent_ts = 0.0

p5 = _plan(raw="hmm", tone="DIRECT", conversation_action="answer",
           intent="conversation")
p5.presence_plan = {"emotional_state": ""}
result5 = compute(p5, _attn(momentum="stable", valence="neutral", energy=0.3, load="medium"))
try:
    dbg = result5.movement_debug
    assert dbg["layer"] == "fallback", f"expected fallback, got {dbg['layer']!r}"
    assert result5.movement_intent == "", f"expected empty, got {result5.movement_intent!r}"
    ok(f"AT-5: fallback layer → intent=''; reason={dbg['reason']!r}")
except AssertionError as e: fail("AT-5", e)


# ── AT-6: movement_debug shape is complete ────────────────────────────────────

_pf._last_non_empty_intent_ts = 0.0

p6 = _plan(raw="go up to the top", tone="DIRECT", conversation_action="answer",
           intent="inquiry")
p6.presence_plan = {"emotional_state": ""}
result6 = compute(p6, _attn())
try:
    dbg = result6.movement_debug
    required_keys = {"intent", "trigger", "gesture", "layer", "reason", "state", "ts"}
    missing = required_keys - set(dbg.keys())
    assert not missing, f"movement_debug missing keys: {missing}"

    state_keys = {"emotional_state", "momentum", "valence", "energy",
                  "tone", "action", "intent_signal", "load", "raw_snippet"}
    missing_state = state_keys - set(dbg["state"].keys())
    assert not missing_state, f"movement_debug.state missing keys: {missing_state}"

    assert isinstance(dbg["ts"], float),        "ts must be float"
    assert isinstance(dbg["state"]["energy"], float), "energy must be float"
    assert len(dbg["state"]["raw_snippet"]) <= 60, "raw_snippet must be ≤ 60 chars"
    ok(f"AT-6: movement_debug shape complete; layer={dbg['layer']!r}, ts present")
except AssertionError as e: fail("AT-6", e)


print(f"\nResult: {PASS}/6 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
