---
id: WO-025
title: "Perception spatial sensor stub — pointcloud/depth domain in PerceptionFaculty (Vol XV §2) → unblocks INT-3"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P3
reason: "Builder relay (2026-08-01): INT-3 (pointcloud → World Model spatial nodes) is NOT blocked on WO-002 (that's DONE) — the real gap is there is no pointcloud/depth sensor stubbed in PerceptionFaculty. Vol XV §2 spatial domain is unstubbed, so INT-3 has no spatial input to consume."
review_required: L1 (Architect) — additive, test-gated
risk: low (additive faculty stub; no frozen-kernel edit; behind a capability flag)
status: READY
created: 2026-08-01
unblocks: INT-3
---

# WO-025 — Spatial sensor stub (pointcloud/depth) in PerceptionFaculty

**Why:** INT-3 wants to turn a pointcloud into World Model spatial nodes, but PerceptionFaculty has no
spatial-sensor input to feed it. This WO adds the **stub** so INT-3 has a real (if synthetic) source.

## Scope (additive only — no frozen-kernel edits)
1. Add a **spatial domain** to `PerceptionFaculty` per **Vol XV §2** — a `spatial` sensor channel that
   emits a normalized **pointcloud/depth frame** into the unified world state (`Vol XV` spatial nodes):
   `{points:[{x,y,z,conf}], frame_id, ts, source}`.
2. Provide a **stub/synthetic source** (fixture pointcloud or depth-cam mock) behind a capability flag
   (`ELO_SPATIAL_SENSOR=1`, off by default) so nothing changes at runtime until enabled — mirrors the
   WO-021 computer-control gating pattern.
3. Write the spatial frame into the existing world-state envelope so downstream (INT-3) can subscribe;
   do **not** build INT-3 itself here — just the source it consumes.
4. Emit a trace (`blender/spatial_trace.json`: frame_id, point count, source, ts) for observability,
   per the WO-017/019 trace pattern.

## Acceptance
1. `ELO_SPATIAL_SENSOR=1` → PerceptionFaculty emits a valid spatial frame into world state each tick;
   flag off → no spatial emission, byte-identical to today.
2. Frame validates against the Vol XV §2 spatial schema (points + frame_id + ts + source).
3. Frozen cognitive-kernel tests stay green (additive-only proof).
4. Acceptance test `tests/test_wo025_spatial_sensor.py` (≥4 cases: schema · flag-gate on/off · trace
   emitted · frozen-kernel green).
5. Handback: diff + test output. On green → INT-3 re-opens with its real dependency (WO-025) met.

## Notes
- Test-gated + additive + no visual/human gate → **🟢 AUTO** under `wo_policy` (auto-closes on green
  via the continuation loop). INT-3 stays P3 — this just removes its false blocker.
