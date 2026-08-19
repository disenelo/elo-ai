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

---

## RESULT — 2026-08-19 (builder autorun close-out)

**Status:** DONE. **Commit:** `d4cc0ad` — *"WO-120 (card 0005): Spatial Faculty — geometry owner, wired
into live turn"* (2026-08-15, already in `main`).

### Acceptance evidence

- **`faculties/spatial/spatial_faculty.py`** — EXISTS, 120 lines. Vol XIII canonical owner.
  `assemble()` reads `blender/elo_spatial.json` (`last_move` ground truth, per WO-118 pairing) +
  `self.route_memory.recent_routes(5)`; maps surface → affordances via `runtime.affordances`.
  `context_block()` returns `[SPATIAL] surface=… can=[…] | last_move→…:… | reach=n/m`.
- **Wired into the live turn** at `server.py:2654-2661` — imported and called every turn in `g_ctx`
  assembly. Faculty is **NOT orphaned** (fail-mode of `faculties.temporal` avoided).
- **`desktop/spatial_state.py:8`** — false docstring *"plans routes"* removed (only nearest-window +
  distance math remains, matching what it actually does).
- **Test:** `tests/test_0005_wo120_spatial_faculty.py` — 3 passed, 0 failed, re-run 2026-08-19.
  - SF-1 importable ✅ · SF-2 real state → `[SPATIAL] surface=window_bottom can=[stand, peek, exit] |
    last_move→180:arrived` ✅ · SF-3 docstring clean ✅.
- **Split agreed with Designer in writing:** ratified in
  `blender/agent_bus/design/FROM_BUILDER_2026-08-19_WO-120_spatial_faculty_split_ratified.md`
  (accepts Designer's proposal in `builder/FROM_DESIGN_2026-08-13_WO-049_spatial_split.md` verbatim;
  names the Python interface for their migration deliverable).

### Note on card provenance

Card was authored 2026-08-13 stating the file did not exist. Between then and now, the file was created
and wired (commit `d4cc0ad`, 2026-08-15) but the card remained in `DOING/`. This close-out completes the
housekeeping — no new code shipped in this autorun tick.

