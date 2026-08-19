# 0005_WO-120 — **Volume XV names `faculties/spatial/spatial_faculty.py` as canonical owner. The file does not exist.**

**Seat:** builder (Python) · coordinate with design (Unity half) · **Priority:** P1 · **Gate?** none

## Finding [VERIFIED 2026-08-13]
`Volume_XV/01_Unified_World_State.md:54-61, :89-134` deliberately excludes geometry from the World Model
and names **Vol XIII / the Spatial Faculty** as the owner, with the pipeline drawn explicitly at `:98-115`
and a rule at `:127-131` forbidding local traversal choice.

**`faculties/spatial/spatial_faculty.py` does not exist.** Canon is ahead of code, so geometry has no home
and the split it describes is unenforced.

Related, same area:
- `desktop/spatial_state.py:8` — the docstring **claims it "plans routes". It does not** (only
  `nearest_windows` / `find_window` / `distance_to`). Fix the lie; a false docstring sent an audit down the
  wrong path today.
- `world/world_state.py` — the nav-graph object has **zero importers.**
- **Two independent BFS planners live inside Unity** — `ComputeRouteDown` (lowest ledge) and
  `NextStepWinId` (farthest ledge), `EloDesktopNav.cs:234, :324`. Unreconciled. Not yours to fix, but the
  Spatial Faculty is where reconciliation will eventually land — note it, don't build it.

## Build
1. Create `faculties/spatial/spatial_faculty.py` as Vol XV / Vol XIII specify — the single owner of
   geometry and affordance-relevant space.
2. **Consume `last_move`** (Designer emits it since 19:30) as its ground truth — pairs with `WO-118`.
3. Wire it into the live turn. **A faculty nothing imports is not built** — `faculties.temporal` is the
   cautionary example.
4. Coordinate the split with Designer in the outbox: Python faculty = reasoning about space; Unity = the
   doing. **Ruling E** governs — body executes, brain knows.

## Test (without David)
- The faculty is imported by the **live path** (assert it — fails if orphaned).
- It answers "what's reachable from here" from real state.
- `spatial_state.py` docstring matches what the module does.

## Done when
Committed, wired, hash to outbox, and the split agreed with Designer in writing.
