# FROM BUILDER — WO-NAV-009 body_win_id Consumer
**Seat:** Builder  
**WO:** WO-NAV-009 — Python body_win_id Consumer (SP-9)  
**Date:** 2026-08-27  
**Authority:** Released by Architect 2026-08-27 (Unity-WO-B1 accepted · WO-NAV-004 ✅)

---

## D-1 — Read body_win_id from elo_spatial.json ✅

`world/live_world_state.py` — in the spatial read block (alongside surface_graph/jump_px):
```python
_body_win_id = int(_sd2.get("body_win_id", -1))  # -1 = mid-hop / unknown
```
Fail-quiet: elo_spatial.json absent or field missing → `_body_win_id = -1`.

---

## D-2 — body_win_id exposed in LiveWorldState ✅

```python
body_win_id: int = -1  # WO-NAV-009 SP-9: eLo body position; -1 = mid-hop / unknown
```
Added to `LiveWorldState` dataclass. Passed in `return LiveWorldState(... body_win_id=_body_win_id)`.

---

## D-3 — L3-NAV-3 enforcement ✅

Module-level `_confirmed_body_win_id: int = -1` tracks the last confirmed body position.

```python
def update_confirmed_body_win_id(arrived: bool, goal_win_id: int | None) -> None:
def get_confirmed_body_win_id() -> int:
```

`update_confirmed_body_win_id()` wired in `server.py` immediately after `MovementOutcome` is built from the movement ACK (in the `_move_acked=True` block). Called with `arrived=_mout.arrived, goal_win_id=_mout.goal_win_id`.

L3-NAV-3 behavior: `arrived=False` → no-op → departure node stays authoritative.

---

## ATs — 6/6 PASS ✅

```
/Users/Disenelo/miniconda3/bin/python3 -m pytest tests/test_wo_nav009_body_win_id.py -v
6 passed in 0.56s
```

AT-1 body_win_id present in LiveWorldState ✅  
AT-2 body_win_id=5 from spatial → LiveWorldState.body_win_id=5 ✅  
AT-3 body_win_id=-1 (mid-hop) → LiveWorldState.body_win_id=-1 ✅  
AT-4 arrived=False → _confirmed_body_win_id unchanged (L3-NAV-3) ✅  
AT-5 arrived=True, goal_win_id=7 → confirmed updated to 7 ✅  
Bonus: get_confirmed_body_win_id() reflects update ✅  

---

## Example world_dict entry

`LiveWorldState.body_win_id = 5` (when Unity emits body_win_id=5 in elo_spatial.json).  
`LiveWorldState.body_win_id = -1` during mid-hop. Navigate handler reads confirmed position via `get_confirmed_body_win_id()`.

---

*Builder · 2026-08-27*
