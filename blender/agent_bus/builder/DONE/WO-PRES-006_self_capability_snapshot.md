# WO-PRES-006 — SelfCapabilitySnapshot per Turn
**From:** Board / Lead Architect  
**Date:** 2026-08-31  
**Priority:** P2  
**Authority:** David L3 ratification 2026-08-24 (ADDED by David, `_intake/SOURCE_2026-08-24_DAVID_L3_PRES_candidates_ratification.md`)  
**RTR:** RTR-058  
**Spec:** `docs/architecture/specs/SPEC_PRES_NAVIGATION_2026-08-24.md` §PRES-006  
**Depends on:** WO-NAV-004 ✅ (jump_px/embodiment_scope), Unity-WO-B1 ✅ (body_win_id)  
**Lane:** Builder (Python). No executive.py. No contracts.py.

---

## What to build

The planner must know what the body can physically do before choosing a route. Currently `jump_px` and `embodiment_scope` are in `capability_set` but not assembled into one snapshot object. This WO assembles `SelfCapabilitySnapshot` per turn and makes it the single source the planner reads.

### SelfCapabilitySnapshot dataclass

Create `runtime/self_capability_snapshot.py`:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SelfCapabilitySnapshot:
    jump_px: float                  # max jump reach in pixels (from capability_set)
    embodiment_scope: list[str]     # ["desktop", "mobile", ...] (from capability_set)
    run_capability: bool            # from WO-PRES-001 addition to capability_set
    run_up_distance_px: float       # from WO-PRES-001 addition to capability_set
    size_px: float                  # eLo's body footprint in pixels (from elo_spatial.json body bounds)
    movement_speed_px_s: float      # approximate movement speed (from capability_set or default 200.0)
    wrap_available: bool            # True if desktop boundaries allow toroidal wrap (WO-PRES-003 ✅)
    body_win_id: Optional[str]      # current body surface (from elo_spatial.json / body_win_id)

def build_snapshot(capability_set: dict, spatial: dict) -> SelfCapabilitySnapshot:
    """Assemble per-turn snapshot from capability_set and elo_spatial.json."""
    ...
```

### Integration

In `runtime/spine/spine.py`, after the capability assembly step and before the navigation planner is called, call `build_snapshot()` and pass the result into the planner context. The planner replaces all individual `capability_set["jump_px"]` reads with `snapshot.jump_px`.

This is a refactor of existing reads, not new capability logic. No new decisions. No new subsystems.

### Acceptance tests

1. `SelfCapabilitySnapshot` instantiates without error from valid capability_set + spatial dict
2. `snapshot.jump_px` equals `capability_set["jump_px"]`
3. `snapshot.run_capability` equals `capability_set["run_capability"]` (from WO-PRES-001)
4. `snapshot.wrap_available` is True when gravity-wrap is enabled (existing WO-PRES-003 flag)
5. Planner can read all fields from snapshot (no KeyError on any field)
6. No executive.py changes. No contracts.py changes.
