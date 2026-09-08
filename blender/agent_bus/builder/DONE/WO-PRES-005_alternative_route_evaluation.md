# WO-PRES-005 — Alternative Route Evaluation (Proportional Depth)
**From:** Board / Lead Architect  
**Date:** 2026-08-31  
**Priority:** P2  
**Authority:** David L3 ratification 2026-08-24 (`_intake/SOURCE_2026-08-24_DAVID_L3_PRES_candidates_ratification.md`)  
**RTR:** RTR-057  
**Spec:** `docs/architecture/specs/SPEC_PRES_NAVIGATION_2026-08-24.md` §PRES-005  
**Depends on:** WO-NAV-013 ✅ DONE, WO-PRES-001 (run capability)  
**Lane:** Builder (Python planner). No executive.py.

---

## What to build

When a direct route is unavailable, eLo evaluates alternatives proportionally before giving up. Not infinite search — bounded depth. The order is: direct → intermediate surface → run-up → wrap → give-up.

### Evaluation ladder (fixed depth)

```
1. DIRECT:       jump straight to destination. If reachable → use it.
2. INTERMEDIATE: find a surface closer to destination, jump there first, then jump to destination.
                 Search: up to 3 intermediate candidates from current candidate_surfaces.
3. RUN-UP:       if run_capability=True, try run-up route (WO-PRES-001).
4. WRAP:         if wrap_available=True (WO-PRES-006 / capability_set), try bottom→top wrap route leg.
5. GIVE-UP:      emit navigation_failed (WO-PRES-004 ✅ DONE — consequence chain already built).
```

### Implementation

In the route planner (SP-11 candidate generation + SP-13 route selection), add a `evaluate_alternatives(destination, depth=4)` function that:

1. Checks direct reachability (existing logic)
2. If not: searches `candidate_surfaces` for intermediates within `jump_px` of both current position and destination
3. If found: returns a two-leg route `[jump_to_intermediate, jump_to_destination]`
4. If not: tries run-up if available (calls WO-PRES-001 logic)
5. If not: tries wrap route if `wrap_available` (RTR-055 / WO-PRES-003 ✅ DONE)
6. If all fail: returns `navigation_failed` outcome

**Limit:** Maximum 3 intermediate candidates evaluated (not exhaustive search). First valid one wins.

### Acceptance tests

1. Direct route exists → single jump leg returned, no alternative search
2. Direct route unavailable, intermediate exists → two-leg route returned
3. No intermediate AND no run-up AND no wrap → `navigation_failed` emitted
4. Run-up available (WO-PRES-001) → run-up route returned before give-up
5. Wrap available → wrap route returned before give-up
6. Maximum 3 intermediates evaluated (not more — performance guard)
7. No executive.py changes. No contracts.py changes.
