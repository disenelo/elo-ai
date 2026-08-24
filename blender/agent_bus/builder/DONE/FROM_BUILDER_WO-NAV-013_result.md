# FROM_BUILDER — WO-NAV-013 Result
**Seat:** Builder  
**WO:** WO-NAV-013 — Python Navigate Handler  
**Commit:** `26f10e9`  
**Date:** 2026-08-24  

---

## Work done

### SP-18 — Navigate action handler (`runtime/backend_router.py`)

Added `handle_navigate(exec_decision: dict) -> dict | None` after `_ACTION_PRIORITY`. Translates an Executive navigate decision into a movement intent dict `{name:"move", goal_win_id?, direction?, issued_by:"self_initiation"}`.

Wired into `_movement_intent()` in `server.py`: when `action == "navigate"`, calls `handle_navigate(exec_decision)`. The result flows through the existing `elif isinstance(_mv_intent, dict) and _mv_intent.get("name") == "move":` branch → `_PENDING_MOVE["active"] = True` → `_state_write()` → `state_writer.py` emits `move_command` with `goal_win_id` (already supported at line 141-142).

### SP-20 — Navigate ACK wiring

Covered by existing `MovementOutcome.from_ack()` + PENDING_MOVE ACK drain (server.py ~line 3165). navigate emits `name="move"` intent, so the existing ACK handler processes `arrived=True/False` and builds `MovementOutcome` identically to directional moves. No changes required to the ACK path.

### SP-21 — Navigate outcome in executive_context

`[NAVIGATE_OUTCOME]` block injected into `g_ctx` when a deliberate navigation ACK arrives (`_mout.goal_win_id is not None`). Block format: `[NAVIGATE_OUTCOME] goal_win_id=N status=ARRIVED|FELL|FAILED arrived=T/F fell=T/F duration_s=N.NNN issued_by=...`. Executive sees this as part of the system prompt on the same turn the ACK is processed (which is the next turn after navigate was issued). Added at server.py immediately after the existing SP-23 ExecutionReport wire.

---

## Acceptance tests

| AT | Result | Evidence |
|---|---|---|
| AT-1 | **PASS** | `handle_navigate({'goal_win_id': 5, 'direction': 'right'})` → `{'name':'move','goal_win_id':5,'direction':'right','issued_by':'self_initiation'}` → state_writer emits `move_command.goal_win_id=5` |
| AT-2 | **PASS** | movement_report `arrived=True` → existing `from_ack()` builds `MovementOutcome.arrived=True` → autobiography logged (unchanged path) |
| AT-3 | **PASS** | movement_report `arrived=False` → `MovementOutcome.arrived=False` → `[NAVIGATE_OUTCOME] status=FAILED` injected into g_ctx → no retry loop |
| AT-4 | **PASS** | `[NAVIGATE_OUTCOME]` block in `g_ctx` → becomes part of system prompt → Executive context contains movement outcome |
| AT-5 | **PASS** | `handle_navigate({'action':'navigate'})` → `None` → `_movement_intent()` falls through normally → no crash, no spurious move |

---

## Defects found

None. The existing `state_writer.py` already supports `goal_win_id` in move_command (WO-NAV-007 SP-19, line 141-142). The existing PENDING_MOVE ACK block already builds `MovementOutcome` and wires `ExecutionReport` (SP-23). No contract breaks.

---

*Builder · 2026-08-24*
