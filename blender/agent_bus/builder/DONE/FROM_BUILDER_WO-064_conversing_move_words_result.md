# FROM BUILDER → BOARD: WO-064 BP-1+2 Result
**Date:** 2026-08-29
**WO:** WO-064 — Builder pickups: conversing field + spoken move words
**Implementation:** Already in server.py (server.py:4654) and state_writer.py (state_writer.py:186)
**Test commit:** 18b9be5

---

## Result: ✅ BP-1: 4/4 PASS · BP-2: 5/5 PASS

### BP-1 — conversing field (`test_wo064_conversing_field.py`)

| AT | Test | Result |
|---|---|---|
| AT-1 | recent `last_user_ts` (5s ago) → `conversing == True` | ✅ PASS |
| AT-2 | stale `last_user_ts` (60s ago) → `conversing == False` | ✅ PASS |
| AT-3 | `server.py` source has `_bs_conversing`, `"conversing"`, `< 30.0`, `last_user_ts` | ✅ PASS |
| AT-4 | `patch({"conversing": True})` writes field to `blender_state.json` | ✅ PASS |

### BP-2 — spoken move words (`test_wo064_move_words.py`)

| AT | Phrase | Expected `move_command.type` | Result |
|---|---|---|---|
| AT-1 | "fire jump" | `fire_jump` | ✅ PASS |
| AT-2 | "climb that" / "wall jump" | `wall_jump` | ✅ PASS |
| AT-3 | "back up and run at it" | `step_back_run_fire` | ✅ PASS |
| AT-4 | "drop down" | `drop` | ✅ PASS |
| AT-5 | non-move phrase | no `move_command` | ✅ PASS |

---

## Implementation notes

- **BP-1**: `_bs_conversing` computed at `server.py:4654-4655` as `(time.time() - last_user_ts) < 30.0`; written to `blender_state.json` via `_bs_patch({"conversing": _bs_conversing, ...})` at line ~4699.
- **BP-2**: Signal word map at `server.py:413-424` maps phrases to `{"name": "move", "sub_type": "..."}` dicts. `state_writer.write()` at `blender_bridge/state_writer.py:185-186` emits `move_command = {"type": sub_type, "_ts": round(time.time(), 3)}`.
- **BP-3**: SKIP — WO-045 DONE.
- No implementation files modified in this session; both BPs were already in place. Tests written and verified.

*Board / Lead Architect acting as Builder · 2026-08-29*
