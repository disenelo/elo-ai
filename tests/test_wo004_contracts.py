"""
tests/test_wo004_contracts.py — Acceptance tests for WO-004: Contract functions in Spine

Covers:
  WO-004a: build_execution_report() — call-site + test
  WO-004b: assemble_cognitive_state() + build_embodiment_state()

Spec: runtime/spine/spine.py, runtime/contracts.py, docs/architecture/16_spine_runtime.md

Run: python3 tests/test_wo004_contracts.py
"""
import sys
sys.path.insert(0, '.')

PASS = 0; FAIL = 0
def ok(n):  global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from runtime.spine.spine import (
    assemble_cognitive_state, build_embodiment_state, build_execution_report,
)
from runtime.spine.plan import CognitivePlan
from runtime.contracts import CognitiveState, EmbodimentState, ExecutionReport

# ── Stub faculty outputs ─────────────────────────────────────────────────────
LANGUAGE = {
    "original": "what are you working on",
    "meaning":  "what are you working on",
    "register": "",
    "social":   "",
    "intent":   "conversation",
    "confidence": 0.95,
}
ATTENTION = {"momentum": "building", "valence": "positive", "scores": {}, "context": {}}
CAPABILITIES = [{"name": "vault_lookup", "available": True, "latency_ms": 40}]


# ── WO-004b: assemble_cognitive_state ────────────────────────────────────────

# AC-2: CognitiveState is frozen after assembly
cs = assemble_cognitive_state(LANGUAGE, None, ATTENTION, CAPABILITIES, None, None)
try:
    assert isinstance(cs, CognitiveState), f"expected CognitiveState, got {type(cs)}"
    ok("WO-004b-1: assemble_cognitive_state returns CognitiveState")
except AssertionError as e: fail("WO-004b-1", e)

try:
    try:
        cs.raw_input = "hacked"
        fail("WO-004b-2", "CognitiveState is not frozen")
    except Exception:
        ok("WO-004b-2 (AC-2): CognitiveState is frozen — mutation rejected")
except Exception as e: fail("WO-004b-2", e)

# Assembly populates language fields correctly
try:
    assert cs.raw_input  == LANGUAGE["original"]
    assert cs.intent_signal == LANGUAGE["intent"]
    assert cs.momentum   == ATTENTION["momentum"]
    assert cs.valence    == ATTENTION["valence"]
    ok(f"WO-004b-3: language + attention fields assembled correctly; confidence={cs.assembly_confidence}")
except AssertionError as e: fail("WO-004b-3", e)

# Missing faculty → confidence lowered (not crashed)
try:
    cs_degraded = assemble_cognitive_state(LANGUAGE, None, {}, [], None, None)
    assert cs_degraded.assembly_confidence < 1.0, f"conf={cs_degraded.assembly_confidence}"
    ok(f"WO-004b-4: missing faculties lower confidence; degraded_conf={cs_degraded.assembly_confidence}")
except AssertionError as e: fail("WO-004b-4", e)

# Capability candidates populated
try:
    assert len(cs.capability_candidates) == 1
    assert cs.capability_candidates[0][0] == "vault_lookup"
    ok("WO-004b-5: capability_candidates populated from faculty output")
except AssertionError as e: fail("WO-004b-5", e)


# ── WO-004b: build_embodiment_state ───────────────────────────────────────────

plan = CognitivePlan()
plan.presence_plan = {
    "animation": "calm", "speed": 0.4, "intensity": 0.5, "duration": 4.0,
    "emotional_state": "calm", "mode": "idle", "pacing": "measured",
}
plan.emotional_vector = {"emotion": "calm"}
plan.direct_response = "I'm here, working through it with you."
plan.movement_intent  = ""
plan.movement_trigger = ""
plan.movement_gesture = ""

es = build_embodiment_state(plan, sequence_id=42)
try:
    assert isinstance(es, EmbodimentState), f"got {type(es)}"
    ok("WO-004b-6: build_embodiment_state returns EmbodimentState")
except AssertionError as e: fail("WO-004b-6", e)

try:
    try:
        es.response_text = "hacked"
        fail("WO-004b-7", "EmbodimentState is not frozen")
    except Exception:
        ok("WO-004b-7: EmbodimentState is frozen")
except Exception as e: fail("WO-004b-7", e)

try:
    assert es.response_text == plan.direct_response
    assert es.sequence_id   == 42
    assert es.emotional_state in ("calm", "neutral", "curious", "alert", "excited", "joy", "sad", "distress")
    assert es.motion_command["animation"] == "calm"
    ok(f"WO-004b-8: EmbodimentState fields populated; emotional_state={es.emotional_state}")
except AssertionError as e: fail("WO-004b-8", e)

try:
    assert es.published_at, "published_at should be set"
    assert es.robot_led_state in ("teal", "white", "amber", "coral", "violet")
    ok(f"WO-004b-9: publish metadata set; robot_led={es.robot_led_state}")
except AssertionError as e: fail("WO-004b-9", e)


# ── WO-004a: build_execution_report call-site + test ─────────────────────────

er = build_execution_report(
    plan,
    voice_delivered=True,
    voice_provider="openai_tts",
    unity_online=True,
    errors=(),
    completion_state="delivered",
    execution_start_ms=1000,
    execution_end_ms=1800,
    llm_latency_ms=600,
)
try:
    assert isinstance(er, ExecutionReport), f"got {type(er)}"
    ok("WO-004a-1: build_execution_report returns ExecutionReport")
except AssertionError as e: fail("WO-004a-1", e)

try:
    assert er.voice_delivered == True
    assert er.completion_state == "delivered"
    assert er.completed == True
    assert er.llm_latency_ms == 600
    ok(f"WO-004a-2: ExecutionReport fields correct; latency={er.llm_latency_ms}ms")
except AssertionError as e: fail("WO-004a-2", e)

try:
    try:
        er.completion_state = "hacked"
        fail("WO-004a-3", "ExecutionReport is not frozen")
    except Exception:
        ok("WO-004a-3: ExecutionReport is frozen")
except Exception as e: fail("WO-004a-3", e)


print(f"\nResult: {PASS}/12 passed, {FAIL} failed")
print()
print("CALL-SITE NOTE (for Architect):")
print("  build_execution_report() is wired in tools/truth_sync.py (session close path).")
print("  It is NOT yet called in server.py per-turn path.")
print("  WO-004b wires assemble_cognitive_state() + build_embodiment_state() into spine.py")
print("  as standalone functions; full per-turn wiring is S3+S6 migration (parity-verified).")
sys.exit(1 if FAIL else 0)
