# CANON-XIII §D — Python Route Injection — RESULT: IMPLEMENTED
**WO:** GATE-CLEAR 2026-10-05 (§A–§C confirmed) + WO-CANON-XIII-E-CLEARED
**Date:** 2026-10-05
**By:** Builder 1
**Commit:** df9efbc

---

## §A–§C status (verified before §D)

- `faculties/spatial/` — EXISTS and populated (spatial_faculty.py)
- `desktop/spatial_state.py` — EXISTS
- `blender_bridge/state_writer.py` — EXISTS with `route`/`issued_by` fields already in move_command envelope

## §D: what was added

### spatial_faculty.py (new functions)

```python
def leg_to_dict(leg: RouteLeg) -> dict
    # Serialises one RouteLeg to JSON-safe dict

def route_to_list(route: Route) -> list
    # Serialises all Route legs

def _nearest_surface_in_direction(elo_x, elo_y, direction, world_map) -> Surface | None
    # Finds nearest walkable Surface in a cardinal direction from eLo's current pixel position

def route_for_direction(elo_x, elo_y, direction, world_map, body, presence) -> Route | NoRoute
    # §D entry-point: direction + world map → plan_route() → Route
    # Resolves from_surface from eLo position, to_surface from nearest in direction
```

### server.py (new §D wire at move intent activation)

After the §C parity log, when `_mv_intent["name"] == "move"` and no route is already set:
1. `get_elo_spatial()` → eLo pixel position
2. `get_windows()` → window list
3. `build_map(windows)` → DesktopWorldMap
4. `route_for_direction(elo_x, elo_y, direction, world_map)` → Route
5. If `isinstance(result, Route)` and legs exist: inject `_mv_intent["route"]` + `_mv_intent["issued_by"] = "SpatialFaculty"`

**Additive**: `direction` field preserved in intent. Unity reads route if present, falls back to its own routing if absent. EloDesktopNav not yet retired (§E parity gate pending WO-CANON-XI-UNITY-ROUTE — test `test_xi_ad2_parity_proven` is the guard).

## Move command flow (after §D)

```
Executive → direction intent
  ↓
§D wire: route_for_direction() → Route(legs, issued_by="SpatialFaculty")
  ↓
_mv_intent["route"] = [leg_to_dict(l) for l in route.legs]
_mv_intent["issued_by"] = "SpatialFaculty"
  ↓
state_writer.patch({"motion": _mv_intent})
  ↓
blender_state.json: move_command.route + move_command.issued_by populated
  ↓
Unity EloDesktopNav: reads route → executes leg sequence
```

## Test baseline

3023 passed, 0 regressions. 1 intentional parity gate fail (`test_xi_ad2_parity_proven`)
unchanged — this is the guard that must go red before §E retirement is complete.

## §E status

§E (EloDesktopNav demotion from decision-maker → receiver) is L3 cleared.
Precondition: `test_xi_ad2_parity_proven` must go green (WO-CANON-XI-UNITY-ROUTE, Design seat).
Unity side: Designer demotes EloDesktopNav to receiver-only once the parity test proves
Python routes match Unity routes at acceptable match rate.

Builder 1 · 2026-10-05
