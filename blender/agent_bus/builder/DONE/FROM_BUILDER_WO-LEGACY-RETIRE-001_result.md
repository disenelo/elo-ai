# FROM_BUILDER — WO-LEGACY-RETIRE-001
**Status:** DONE — all four legacy paths verified as retired or correctly gated
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Investigation

Verified each of the four retirement targets against current server.py source.

## 1. Legacy tool routing → Cap Faculty ✅ RETIRED

`server.py:60` imports `_tool_enrich_from_plan` (not legacy keyword regex).

Per WO-CAPABILITY-FACULTY-WIRE-001 result card:
- Primary path: `enrich_from_plan()` dispatches capabilities from `_plan.capabilities` (Executive's selection)
- No legacy regex fallback runs when plan_caps exist
- When plan has no capabilities → returns `(raw, None)` — no fallback to old keyword matching

**Verdict:** Legacy tool routing is retired. Cap Faculty governs.

## 2. Legacy intent → Executive ✅ RETIRED

`_process_turn()` structure (lines 2007–5380):

All user intents route through `spine.run()` at line 2925 (`from runtime.spine.spine import run as _spine_run`). Pre-spine handlers are transport-level gates (safety confirmations, animation commands) — they short-circuit only for:
- File/computer control confirm/cancel (not cognitive decisions)  
- Direct animation commands ("instant, no LLM needed" — documented design intent)
- Hard loop guard (3x repeat, anti-loop protection)

Every path that carries cognitive content falls through to spine (confirmed by 12+ "# Falls through to spine" comments in lines 2053–2915). No legacy intent resolver runs in parallel.

**Verdict:** Executive governs intent. Pre-spine gates are transport-level by design, not legacy parallel.

## 3. Legacy blender writes → Embodiment Publisher ✅ RETIRED (spine path primary)

`server.py:4770-4773`:
```python
if _plan is not None and _plan.presence_plan:
    # ── Spine path: use plan output directly ──────────────────────
    from blender_bridge.embodiment_publisher import publish as _embody
    _embody(_plan, gaze=_gaze)
```

The spine path uses `_embody()` via `blender_bridge/embodiment_publisher.py`. The legacy `_state_write()` path at line 4762 is explicitly labeled: "Legacy fallback: when spine is unavailable, compute movement intent the old way." It runs ONLY when `_plan.presence_plan` is None — i.e., spine failed.

This is correct defensive architecture. The fallback should stay: a failed spine turn should not freeze eLo's avatar. The embodiment publisher governs the primary (spine-success) path.

**Verdict:** Embodiment Publisher governs primary path. Legacy fallback is gated to spine-failure only — appropriate.

## 4. Legacy env → Env Faculty ✅ RETIRED

Per WO-ENVIRONMENT-FACULTY-001 result card: `_environment_faculty()` added to `runtime/spine/spine.py` and wired through `assemble_cognitive_state()`. Environment fields (`active_app`, `active_window`, `desktop_activity`) flow through the CognitiveState contract.

No direct `perch_state.json` / `presence_state.json` reads in `_process_turn()` (these reads are in spine's env faculty, not in server.py turn loop).

**Verdict:** Env Faculty governs. Legacy direct reads are retired.

---

## Assessment

The DISPATCH_BOARD concern ("Until retired, spine doesn't govern") was accurate when written. All four retirement targets have since been addressed by WOs executed in prior sessions:
- WO-CAPABILITY-FACULTY-WIRE-001 (tool routing)
- WO-ENVIRONMENT-FACULTY-001 (env faculty)
- WO-EMBODIMENT-PUBLISHER-001 (blender writes → publisher)
- WO-INGRESS-32 / spine routing architecture (intent → Executive)

The only remaining `_state_write()` calls in the main turn loop are:
- The spine-unavailable fallback (line 4762) — **correctly gated, should stay**
- Lifecycle state patches (`patch({"lifecycle_state": ...})`) — **state patches, not routing decisions**
- Brain state writer (`brain_state_writer.publish`) — **separate Quantum One Brain channel, not legacy**

**Spine governs. Legacy parallel paths are retired.**
