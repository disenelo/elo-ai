# WO-TIRED-SIT-001 — Wire physical tiredness → Sit_hold animation (One Brain path)
**Date:** 2026-10-02  **Priority:** P1  **Assigned:** Builder 1 (server.py/ambient) + Designer (Sit_hold anim confirm)
**Lane:** ambient/ambient_engine.py + blender_bridge/state_writer.py + WO-INNER-THOUGHTS-001 Phase 2

## Gap
Physical battery drain from walking/running/parkour tracks correctly in `core/health_battery.py`. The five physical states (rested, normal, tired, fatigued, exhausted) are computed each tick. `PHYSICAL_EXPRESSIONS` specifies the inner_thought conditioning text ("I've been standing all day — let me sit for a bit to reset my legs") for each band. But the conditioning is currently routed ONLY to the inner_thought pipeline (WO-INNER-THOUGHTS-001 Phase 2) — it is not verified as wired, and no direct path exists from `physical_state == "tired"` → sit animation command → Sit_hold playing on DISENELO Presence.

Evidence:
- `core/health_battery.py:92-98` — physical_state bands defined
- `core/health_battery.py:112-137` — PHYSICAL_EXPRESSIONS dict with inner_thought + response text
- `core/health_battery.py:108-111` — "NOT templates … soft conditioning passed to inner_thought pipeline (WO-INNER-THOUGHTS-001 Phase 2)"
- `ambient/ambient_engine.py:_calm_on_low_battery()` — emits Calm animation on low battery ✅ but has NO tired→sit path
- No grep result for `Sit_hold`, `sit_down`, or `tired.*sit` in ambient_engine.py

## Architecture (confirmed by code)
Battery → Calm (meditation) = conscious rest. ✅ Already wired.
Battery → Sleep: FORBIDDEN. The battery does NOT trigger sleep. Only the One Brain (dream_faculty) triggers sleep.
tired → wanting to sit → Sit_hold = physical expression, NOT sleep. Must go through Executive → intent → embodiment.

## Fix

### Part A — Builder 1: emit tired-sit inner event from ambient health tick
In `ambient/ambient_engine.py` battery tick (around line 260-266), after calling `_hb.tick()` and getting `snapshot()`:
- If `physical_state in ("tired", "fatigued", "exhausted")` AND `motion.mode not in ("calm", "sit", "sitting", "sleeping", "dream")`:
  - Emit inner_event `{"type": "physical_tired", "state": physical_state, "inner_thought": PHYSICAL_EXPRESSIONS[physical_state]["inner_thought"]}` into `blender_state.json.inner_events` queue (same pattern as idea_event, gesture_event)
  - Do NOT emit a direct motion command — eLo decides whether to sit

### Part B — Builder 1: wire inner_thought from physical_tired event
When `inner_thought` pipeline (WO-INNER-THOUGHTS-001) receives a `physical_tired` inner event, it generates the inner_thought text from `PHYSICAL_EXPRESSIONS`. The Executive may then decide to: issue a sit command (emit `sit_command` to blender_state.json) or continue current activity.

### Part C — Designer: confirm Sit_hold animation is the correct clip for this state
Verify that the Sit_hold animation exists and is appropriate for "eLo getting tired and sitting down" (not commanded sit — autonomous tiredness sit). If a different clip is more appropriate, note it.

## Acceptance
Walking/running raises physical drain. When `physical_state` reaches "tired" or below: inner_event fires. Inner_thought pipeline picks it up. eLo may decide to sit. If Executive issues a sit intent, Sit_hold animation plays in DISENELO Presence. The sleep animation does NOT play from physical tiredness alone — only from dream_phase becoming non-empty.
