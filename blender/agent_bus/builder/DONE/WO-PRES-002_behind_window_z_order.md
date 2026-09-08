# WO-PRES-002 — Behind-Window Z-Order Spatial State
**From:** Board / Lead Architect  
**Date:** 2026-08-31  
**Priority:** P2  
**Authority:** David L3 ratification 2026-08-24 (`_intake/SOURCE_2026-08-24_DAVID_L3_PRES_candidates_ratification.md`)  
**RTR:** RTR-054  
**Spec:** `docs/architecture/specs/SPEC_PRES_NAVIGATION_2026-08-24.md` §PRES-002  
**Depends on:** SP-9 `body_win_id` (Unity-WO-B1 ✅ DONE), WO-NAV-009 ✅ DONE  
**Lane:** Builder (Python) + Unity side (separate Unity WO not needed — existing `EloWindowOcclusion` handles render layer). Python world model only.

---

## What to build

eLo can exist spatially behind open desktop windows. This is a position state, not just a render effect. The brain must know "eLo is behind window X" so it can reason about it.

### 1 — World model extension

In `runtime/world_delta.py` or wherever `world_dict` / `LiveWorldState` is assembled, add:

```python
"behind_window_id": str | None   # win_id of window eLo is currently behind; None if in front of all windows
```

Populate from Unity event stream: Unity emits an occlusion event when eLo moves behind a window. Python reads it and sets `behind_window_id`.

If Unity does not yet emit this event: write the consumer to handle it when it does arrive (no change to Unity required from Python side).

### 2 — Navigation planner route leg

Add a route leg type `behind_window` to `route_nodes`:

```python
{"action": "move_behind", "window_id": win_id}
{"action": "emerge_from", "window_id": win_id}
```

Planner (SP-11/SP-13) treats a `behind_window` path as a valid route leg when:
- Destination is accessible by moving through a behind-window path
- The window is currently open (in `open_windows` world state)

### 3 — EloSelfState annotation

Add `behind_window_id: str | None = None` to `EloSelfState` so the Executive can read it from CognitiveState.

### Acceptance tests

1. `world_dict` contains `behind_window_id` key (None when eLo is in front)
2. When Unity occlusion event arrives: `behind_window_id` is set to the relevant win_id
3. Route planner accepts `behind_window` and `emerge_from` as valid leg types without error
4. `EloSelfState.behind_window_id` is populated from world state per turn
5. No executive.py changes. No contracts.py changes.
