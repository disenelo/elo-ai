# WO-PRES-001 — Run/Run-up Capability in Navigation Planner
**From:** Board / Lead Architect  
**Date:** 2026-08-31  
**Priority:** P2  
**Authority:** David L3 ratification 2026-08-24 (`_intake/SOURCE_2026-08-24_DAVID_L3_PRES_candidates_ratification.md`)  
**RTR:** RTR-053  
**Spec:** `docs/architecture/specs/SPEC_PRES_NAVIGATION_2026-08-24.md` §PRES-001  
**Depends on:** WO-NAV-013 ✅ DONE — gate cleared  
**Lane:** Builder (Python). No executive.py. No contracts.py.

---

## What to build

Run and run-up are distinct movement modes. A run-up changes what is reachable. The planner must know this before choosing a route.

### 1 — Extend `capability_set` with run fields

In `runtime/capabilities/registry.py` or wherever `capability_set` is constructed, add:

```python
"run_capability": bool        # True if eLo can run on current surface
"run_up_distance_px": float   # Minimum pixel run distance before a long jump is achievable
```

Default: `run_capability = True`, `run_up_distance_px = 120.0` (estimate — use jump_px as reference: 576px jump; run-up ~20% of screen width).

### 2 — Navigation planner (SP-11 candidate generation)

In the planner's candidate generation, when evaluating a distant surface:

- If `horizontal_gap > jump_px` AND `run_capability = True` AND `run_up_distance_px` is available on current surface:
  - Add a candidate route: `[run_on_current, jump_to_destination]` with `requires_run_up = True`
- If `horizontal_gap > jump_px + run_up_bonus` OR `run_capability = False`:
  - Mark destination unreachable

Run-up bonus = `jump_px * 0.25` (estimate — first implementation; measure actual Unity physics).

### 3 — Route leg representation

A route leg with run-up must be expressible in `route_nodes` as:

```python
{"action": "run_on_current", "surface": current_surface_id}
{"action": "jump", "from": current_surface_id, "to": destination_id, "run_up": True}
```

### Acceptance tests

1. When gap < jump_px: direct jump planned, no run-up leg in route_nodes
2. When jump_px < gap < jump_px + bonus AND run_capability=True: run-up route planned
3. When gap > jump_px + bonus: surface marked unreachable even with run-up
4. When run_capability=False: no run-up route attempted, surface marked unreachable
5. `run_capability` and `run_up_distance_px` appear in capability_set output

Do NOT touch executive.py. Do NOT add new subsystems. This is a planner constraint + capability_set field addition only.
