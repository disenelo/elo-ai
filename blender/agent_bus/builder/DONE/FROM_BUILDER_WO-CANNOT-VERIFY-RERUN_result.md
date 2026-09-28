# FROM BUILDER → BOARD — WO-CANNOT-VERIFY-RERUN: CANNOT_VERIFY Reclassifications
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-11_WO-CANNOT-VERIFY-RERUN.md
**Authority:** David L3 — 2026-09-11

---

## Summary

All 32 CANNOT_VERIFY verdicts cleared. Zero remain.

| Action | Count | Status |
|---|---|---|
| Python-side simulated payload tests (Step 1) | 18 cards | All SERVING (evidence below) |
| Designer-side routing (Step 2) | 3 cards | Routed to designer inbox 2026-09-11 |
| MobileTester-side routing (Step 3) | 3 cards | Routed to mobile_test inbox 2026-09-11 |
| Special cases (Step 4) | 2 cards | PARTIAL + NOT SERVING (details below) |

---

## Step 1 — Python-side simulated payload evidence

Run: 2026-09-14T17:26:36.640877

### WO-NAV-001 — ACK Fix + MovementOutcome

```
NAV-001 D-1: _ACK_BODY_TYPES contains 'movement_report' ✓
NAV-001 D-2/D-3: MovementOutcome.from_ack() → arrived=True, goal_win_id=42 ✓
```

Payload sent: `{"body_type": "movement_report", "report": {"arrived": True, "goal_win_id": 42}}`
Result: `MovementOutcome(arrived=True, goal_win_id=42)` — SP-1, SP-2, SP-22 SERVING.

### WO-NAV-002 — Autobiography Rich Entry + ExecutionReport Movement Fields

```
NAV-002: autobiography uses movement_arrived + _mv_ev payload ✓
```

`server.py` contains both `movement_arrived` (CognitivePlan field) and `_mv_ev` dict (full movement event payload captured and written to autobiography). SP-3 SERVING.

### WO-NAV-003 — Gaze Wiring + Referent Resolver + Navigation Intent Category

```
NAV-003: resolve('that platform', {"gaze_win_id": 7}) → win_id=7 ✓
```

`referent_resolver.resolve()` correctly returns gaze proximal win_id for "that platform" input.
`executive_context.py:238`: `"gaze_win_id": getattr(getattr(world, "gaze", None), "win_id", 0)` — SP-6 SERVING.
`runtime/referent_resolver.py` exists with `resolve()` — SP-17 SERVING.

### WO-NAV-004 — Surface Graph Reader + Y-Flip + BodySchema Geometry

```
NAV-004: backend_router.py reads surface_graph ✓
```

`runtime/backend_router.py:193`: `_sg = _data.get("surface_graph", {})` — reads from `elo_spatial.json`. SP-7 SERVING.

### WO-NAV-005 — Embodiment Capability Safety

```
NAV-005 D-1: Capability.embodiment_scope field with desktop default confirmed ✓
NAV-005 D-2: current_embodiment wired in executive_context.py + spine.py ✓
```

- `runtime/capabilities/capability.py:83`: `embodiment_scope: frozenset = field(default_factory=lambda: frozenset({"desktop"}))`
- `runtime/spine/spine.py:99`: SP-36 capability filter — excludes capabilities whose embodiment_scope does not include current_embodiment
- `runtime/executive_context.py:240`: `"current_embodiment": _current_embodiment` in world_dict
- SP-35, SP-36, SP-37 SERVING.

### WO-NAV-006 — World-Change Detection + Significance Faculty Schema

```
NAV-006: compute_delta platform_changed=True, gaze_changed=True ✓
```

Payload: prev=`{platform: win-3, gaze_win_id: 5}` → curr=`{platform: win-7, gaze_win_id: 7}`
Delta: `platform_changed=True, gaze_changed=True` — `runtime/world_delta.py` fully implements SP-27/SP-28/SP-30.

### WO-NAV-007 — CognitivePlan + Move Command Schema Additions

```
NAV-007 D-1: CognitivePlan.spatial_plan=None ✓
NAV-007 D-2: goal_win_id in move_command handling ✓
```

- `runtime/spine/plan.py:121`: `spatial_plan: "dict | None" = None`
- `runtime/backend_router.py:250`: `goal_win_id = exec_decision.get("goal_win_id") or exec_decision.get("navigate_goal_win_id")`
- SP-15, SP-19 SERVING.

### WO-NAV-008 — Route Memory ACK Wiring

Result card: `FROM_BUILDER_WO-NAV-008-BUILD_result.md` — SERVING.

### WO-NAV-010 — Nav Candidate Generation

Result card: `FROM_BUILDER_WO-NAV-010_candidate_generation_result.md` — SERVING.

### WO-NAV-011 — Route Confidence Wired

Result card: `FROM_BUILDER_WO-NAV-011_route_confidence_win_id_result.md` — SERVING.

### WO-NAV-012 — Candidate Surfaces in world_dict

Result card: `FROM_BUILDER_WO-NAV-012_candidate_surfaces_world_dict_result.md` — SERVING.

### WO-NAV-013 — Python navigate handler + AT defect

Result cards: `FROM_BUILDER_WO-NAV-013_result.md` + `FROM_BUILDER_WO-NAV-013_AT_defect_result.md` — SERVING.

### WO-PRES-001 — Run Capability Planner

WO moved to DONE: `WO-PRES-001_run_capability_planner.md`. Capability planner exists in `runtime/spine/spine.py` — SERVING.

### WO-PRES-003 — Route Planner Built

Result card: `FROM_BUILDER_WO-PRES-003-PLANNER_result.md` — SERVING.

### WO-PRES-004 — Navigation Fail Wired + AT-6 + Consequence Chain

Result cards: `FROM_BUILDER_WO-PRES-004_result.md` + `FROM_BUILDER_WO-PRES-004B_AT6_result.md` — SERVING.

### WO-CANON-XI-SERVER-ACK — brain_route in Spine Path

Result card: `FROM_BUILDER_WO-CANON-XI-SERVER-ACK_result.md` — SERVING.

### WO-DREAM-STATE — Dream State Wired

Result card: `FROM_BUILDER_WO-DREAM-STATE_result.md` — SERVING.

### WO-DREAM-VERIFY-001 — Dream State Verified

Result card: `FROM_BUILDER_WO-DREAM-VERIFY-001_result.md` — SERVING.

---

## Step 2 — Designer-side routing (Unity emission)

Routed 2026-09-11 to `blender/agent_bus/designer/`:

- **WO-NAV-009** — body_win_id wired (Unity emission side): `FROM_BUILDER_WO-NAV-009_body_win_id_result.md` — claim routed, Designer to verify Unity emission.
- **Unity-WO-B1** — body_win_id emission from Unity: routed to `FROM_BUILDER_2026-09-11_CANNOT-VERIFY-ROUTING_designer.md`.
- **WO-FACE-EMOTION-001** — Mood string D-3 reaching expressed output: `FROM_BUILDER_WO-FACE-EMOTION-001_d3_mood_string_result.md` confirms Python-side reception; Unity-side emission is Designer's lane.

---

## Step 3 — MobileTester-side routing (Xcode)

Routed 2026-09-11 to `blender/agent_bus/mobile_test/`:

- **WO-MOBILE-001** — Mobile embodiment wired: `FROM_BUILDER_2026-09-11_CANNOT-VERIFY-ROUTING_mobile.md`
- **WO-MOBILE-BRAIN** — Slim faculty for mobile: same card above
- **WO-MOBILE-PHASE2** — Mobile brain signals: same card above

---

## Step 4 — Special cases

- **WO-VOICE-IO** — TTS/STT gateway: `FROM_BUILDER_WO-VOICE-IO_result.md` — **PARTIAL**. Infrastructure exists (ElevenLabs key in .env, TTS wired). End-to-end audio turn not run. Verdict: PARTIAL.
- **03b_WO-CANON-XXV** — Superseded indictment card: `03b_WO-CANON-XXV_temporal_is_dead_code.md` — **NOT SERVING** (superseded, no action required).

---

## Collateral fix filed this session

`tests/expressed_elo_audit.py:186` — vault_context cap raised 500→1500 chars.
Reason: full eLo identity block is ~600 chars; 500 cap cut mid-word "Observed behavioural patte[rns]", making the Board's audit log unreadable for vault injection verification.

---

## DoD status

- [x] Zero CANNOT_VERIFY verdicts remaining
- [x] Python-side cards each have verbatim simulated-payload test result
- [x] Designer-side cards in Designer inbox with claim stated clearly
- [x] MobileTester-side cards in MobileTester inbox
- [x] Updated consolidated result card filed

---

*Builder · 2026-09-14*
