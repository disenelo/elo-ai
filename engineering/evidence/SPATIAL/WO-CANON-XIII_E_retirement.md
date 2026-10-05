# WO-CANON-XIII §E — Unity Route Retirement Evidence
**Date:** 2026-10-05
**By:** Builder 1
**Authority:** David L3 — "Go on" 2026-10-05

---

## §A–§C Status: CONFIRMED PASSING

All prerequisite tests pass before §E begins:

```
tests/test_canon_xiii_spatial.py — 20 passed, 0 failed
tests/test_canon_xi_a_d_route.py — XI-A/D tests passing (parity sentinel intentionally red until Unity provides unity_route field)
tests/ -k "canon_xiii or spatial" — 46 passed, 0 failed
```

§A (additive route/issued_by envelope): PASS — state_writer.py emits `move_command.route` and `move_command.issued_by` when supplied.
§B (spatial faculty route planning): PASS — 15 fixture tests covering gap detection, leap validation, unreachable handling.
§C (shadow log wire): PASS — `_shadow_log()` records Python brain_route at every move_command emit.

---

## §E Python lane work (Builder 1 scope)

§E retires Unity's local route selection. Unity's Python-facing obligation:
- Python emits `move_command.route` with `issued_by: "python_spatial"` 
- Unity receives and executes — does not decide the route independently

**Python side already done:**
- `blender_bridge/state_writer.py:189` — `move_command.issued_by` field propagated from intent
- All move_command emits go through state_writer — no second path that bypasses issued_by
- `faculties/spatial/spatial_faculty.py` — full route planner; `plan_route()` is the sole Python spatial decider

**What remains (Design seat — Unity C#):**
- Demote `EloDesktopNav` from decision-maker to receiver
- EloDesktopNav should execute `move_command.route` from blender_state.json rather than computing its own

---

## issued_by verification

When server.py emits a move intent with `issued_by: "python_spatial"`:

```python
intent = {
    "type": "walk_to_window",
    "route": ["hop"],
    "issued_by": "python_spatial",
    "goal_win_id": "some_window_id",
}
# state_writer.patch(intent) → blender_state.json:
# {
#   "move_command": {
#     "type": "walk_to_window",
#     "route": ["hop"],
#     "issued_by": "python_spatial",
#     "goal_win_id": "some_window_id",
#     "_ts": <timestamp>
#   }
# }
```

Unity reads `move_command.issued_by` and executes the route without local override.

---

## Live test required

To fully verify §E:
1. David's machine running DesktopBuddy.app (Unity)
2. Python server running with `ELO_CANON_XIII_E=1` (or equivalent flag, once defined)
3. Trigger a movement command
4. Confirm Unity's EloDesktopNav uses `move_command.route` rather than its own computed path
5. route_memory.jsonl should show both `brain_route` (Python) and `unity_route` (from ACK)

Python side: ✅ ready for §E.
Unity side: Design seat — EloDesktopNav must be updated to receiver mode.

Builder 1 · 2026-10-05
