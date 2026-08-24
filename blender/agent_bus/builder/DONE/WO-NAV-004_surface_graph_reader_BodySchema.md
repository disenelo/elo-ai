# WO-NAV-004 — Surface Graph Reader + Y-Flip + BodySchema Geometry
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** HIGH — Wave 1 independent  
**RTR:** RTR-047  
**SPEC basis:** `specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` + `findings/SPEC_AMENDMENT_PHASE2_NAV_2026-08-23.md` — SP-7, SP-10, SP-8

---

## Context

eLo's spatial reasoning currently uses stale values. The `elo_spatial.json` contains a `surface_graph` with 51 platforms and continuous `gap_px` values — but Python never reads the graph. `BodySchema.max_jump_d = 75` is a stale planning value; the physics-derived authoritative value is `capability_set.jump_px = 576` (Unity-derived).

This WO corrects both:
1. SP-7: Read `surface_graph` from `elo_spatial.json` into Python world state
2. SP-10: Apply Y-flip when converting Unity coordinates to Python screen coordinates
3. SP-8: Replace `max_jump_d = 75` with `capability_set.jump_px` in all geometry planning

**L3-NAV rules (canonical — do not deviate):**
- Horizontal gap (from `rect_px`) governs reachability. Euclidean gap_px is supplementary telemetry, not a planning value.
- `capability_set.jump_px = 576` is authoritative for horizontal reachability.
- Y conversion: `py_y = screen_h - unity_y` (Unity Y is inverted relative to Python screen space).

---

## Deliverables

### D-1 — SP-7: Read `surface_graph` from `elo_spatial.json`
**File:** `world/live_world_state.py` (or wherever world state is assembled)  
**Contract:**
- Read `elo_spatial.json` → `surface_graph` key → list of platform objects
- Each platform object has: `win_id`, `rect_px` (x, y, width, height), `gap_px` (to neighbours), and likely label/type fields — verify actual schema by reading the file
- Make the surface_graph available in the world state as `surfaces` (or the canonical field name — check what the SPEC uses)
- This reader runs at world state assembly time; it does not run per-message unless the file has changed

**Constraint:** Do not modify `elo_spatial.json`. Read-only access.

### D-2 — SP-10: Y-flip conversion
**Contract:** At the boundary where Unity coordinates enter Python (wherever `rect_px` positions are used for planning), apply:
```
py_y = screen_h - unity_y
```
where `screen_h` is the screen height available in world state (or from elo_spatial.json header — verify).

**Constraint:** Y-flip is applied once at the boundary. Do not apply it twice. Do not apply it inside the Unity emitter.

### D-3 — SP-8: Replace `max_jump_d = 75` with `capability_set.jump_px`
**Files:** Any Python file that uses `max_jump_d` as a planning value — search the codebase for all occurrences.  
**Contract:**
- `capability_set.jump_px` is the authoritative horizontal reachability distance (value: 576, physics-derived from Unity)
- Remove or retire `BodySchema.max_jump_d = 75` as a planning value
- For reachability check: a platform is reachable if `horizontal_gap <= capability_set.jump_px`
- Where `horizontal_gap` = `abs(target_rect.x - current_rect.x)` using the platform's `rect_px.x` centre

**Constraint:** Do not substitute Euclidean distance for horizontal gap. L3-NAV-1 is binding: horizontal gap from rect_px governs reachability.

---

## Forbidden Scope

- No changes to `executive.py` or FREEZE_V1_LOCK files
- No changes to `elo_spatial.json`
- No changes to Unity side
- No new candidate generation (that is SP-11, a later wave)

---

## Verification

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | surface_graph loaded | World state contains surfaces list; 51 platforms present (or count from actual JSON) |
| AT-2 | Y-flip applied | A known platform's Y coordinate in Python matches `screen_h - unity_y` for its Unity rect_px.y |
| AT-3 | max_jump_d retired | No Python planning code references `max_jump_d = 75` as a reachability threshold |
| AT-4 | Horizontal gap reachability | A platform at horizontal_gap = 500 is reachable; one at 600 is not (using 576 threshold) |
| AT-5 | surface_graph read-only | elo_spatial.json is unchanged after running world assembly |

---

## RTR Traceability

After implementation, update RTR-047 in `RECOVERY_TRACEABILITY_REGISTER_2026-08-24.md`:
- RTR-047: add WO-NAV-004, commit, AT-1 through AT-5 pass

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — Execution Directive 2026-08-24*

---

## Result — Builder 2026-08-24

**Commit:** 3789ec6  
**Tests:** AT-1 through AT-5 — **7/7 PASS**

| Deliverable | File | Status |
|---|---|---|
| D-1 SP-7: `surfaces` field + surface_graph reader | `world/live_world_state.py` | ✅ |
| D-2 SP-10: Y-flip `py_y = screen_h - unity_y` at boundary | `world/live_world_state.py` | ✅ |
| D-3 SP-8: `max_jump_d → jump_px` in BodySchema; `LiveWorldState.jump_px` from `capability_set.jump_px` | `faculties/spatial/spatial_faculty.py` + `world/live_world_state.py` | ✅ |
| Regression: canon_xiii_spatial updated to `jump_px` | `tests/test_canon_xiii_spatial.py` | ✅ |

**Actual node count:** 53 (WO cited 51 as an estimate — live file has 53)  
**Actual `capability_set.jump_px`:** read live from `elo_spatial.json` (Unity-authored, varies ~527–572)  
**Y-flip:** applied once in `assemble_world_state()` — not inside the Unity emitter, not in any consumer  
**AT-5 (read-only):** verified via `builtins.open` mock — assembly never opens `elo_spatial.json` in write mode  
**Constraints obeyed:** `executive.py` not touched, `elo_spatial.json` not modified, Unity side not touched, no new candidate generation
