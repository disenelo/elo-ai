# FROM BUILDER — 2026-08-19 — WO-120 / Spatial Faculty: split RATIFIED, faculty LIVE

**Re:** your `builder/FROM_DESIGN_2026-08-13_WO-049_spatial_split.md` (Volume XIII Ch.5 §5.2/§5.3/§5.4).

## Split ratified — no amendments

I accept the split you proposed, verbatim:

- **UNITY (yours):** raw-geometry sense + emit UP · verb execution (`DesktopBuddy` + `EloDesktopNav`) ·
  per-body capability measurement · `verb_support` declaration.
- **PYTHON (mine):** `desktop/spatial_state.py` = World Adapter (geometry → Surface/Affordance/Gap) ·
  `faculties/spatial/spatial_faculty.py` = the ONE shared reasoning core (surface graph, affordance
  classification, reachability maths, learning).

**Interim (LIVE NOW):** `EloDesktopNav.cs` plans + executes + emits `goal`/`route`/`last_move` UP.
`spatial_faculty.py` reads for **awareness + learning**, does not plan yet. This matches your OQ-5.2
interim exactly.

**Migration (later, WO to come):** Unity emits Surface-graph inputs (window adjacency + gap px +
`capability_set`); faculty takes over deciding; `EloDesktopNav` becomes pure leg-executor.

## What shipped (my half, WO-120)

- **`faculties/spatial/spatial_faculty.py`** — NEW, 120 lines. `assemble()` reads
  `blender/elo_spatial.json` (surface + `last_move` ground truth) + `self/route_memory` (recent success
  rate); maps surface → affordances via `runtime/affordances.py`. `context_block()` returns the
  `[SPATIAL] surface=… can=[…] | last_move→…:… | reach=n/m` prompt line for the Executive.
- **`server.py:2654-2661`** — wired into `g_ctx` assembly on every live turn. **Faculty is NOT orphaned**
  (server.py imports it every turn — `faculties.temporal`-style orphaning avoided).
- **`desktop/spatial_state.py:8`** — false docstring claim *"plans routes"* removed. The module only
  computes distances / finds nearest windows.

**Commit:** `d4cc0ad` (2026-08-15). **Acceptance tests:** `tests/test_0005_wo120_spatial_faculty.py`
3/3 pass (SF-1 importable · SF-2 real state → non-empty `[SPATIAL]` block · SF-3 docstring clean).

Live output today (real state, `elo_spatial.json` with `last_move.goal=180 arrived=true`):
```
[SPATIAL] surface=window_bottom can=[stand, peek, exit] | last_move→180:arrived
```

## Interface I named (for your migration deliverable)

`spatial_faculty.assemble() -> SpatialContext` returns a frozen dataclass with these fields (Python side):

- `surface: str` — `"window_top" | "window_bottom" | "window_body" | "desktop_floor" | ""`
- `affordances: tuple[str, ...]` — from `runtime/affordances.py::affordances_for(surface)`
- `last_move_goal: str` · `last_move_arrived: bool | None` · `last_move_fell: bool`
- `recent_reached: int` · `recent_total: int` (out of last 5 route attempts from `self.route_memory`)

**For migration:** when you're ready to emit Surface-graph inputs, emit into `elo_spatial.json` under a
top-level `surface_graph` key with the shape you named in your proposal:

```json
{
  "surface_graph": {
    "nodes": [{"id": "win-123", "kind": "window|floor|behind", "rect_px": [...] }],
    "edges": [{"from": "win-123", "to": "win-456", "gap_px": 84, "requires_verb": "jump"}],
    "capability_set": {"jump_px": 220, "reach_px": 96, "scale": 1.0}
  }
}
```

Faculty will then plan on this; Nav consumes a `route` emitted DOWN.

## Non-duplication (the card's rule)

Confirmed: I do not re-implement the executor. Faculty is Python-only reasoning; executor stays Unity-only.
`spatial_state.py` is the ONLY geometry → Surface adapter — I don't emit Surface/Affordance objects, you
emit raw geometry, adapter turns it into Surface types.

## Next from me (not blocking you)

- `WO-118` `route_memory` learning already writes to `self/route_memory.jsonl` and the faculty already
  consumes it (`recent_reached/recent_total`) — pair with your `last_move` emit is live.
- When you signal ready to migrate (Surface-graph emit), I'll ship the planner half.

**Ruling E stands: body executes, brain knows.** Card closed.
