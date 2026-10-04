# WO-QMOVEMENT-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-03  
**Status:** DONE — fully implemented in a prior session

## Finding

INBOX stated "ZERO code found for any of these five states." This was incorrect at time of dispatch — all five Q-MOVEMENT lifecycle states are implemented and wired.

## Five-state lifecycle — verified

| State | Field | Location |
|---|---|---|
| WHERE I AM | `movement_where_i_am` (str) | spine.py:1652–1653 |
| WANT TO GO | `movement_want_to_go` (int, goal window ID) | spine.py:1655–1659 |
| AM MOVING | `movement_am_moving` (bool) | spine.py:1660–1661 |
| ARRIVED | `movement_arrived` (bool, from last_move) | spine.py:1663–1665 |
| WHAT HAPPENED | `movement_what_happened` (str outcome) | spine.py:1663–1666 |

### Contracts — `runtime/contracts.py` lines 345–350
```python
# Q-MOVEMENT (five lifecycle states)
movement_where_i_am:   str  = ""   # "window:<name> edge:<edge>"
movement_want_to_go:   int  = -1   # goal window ID (-1 = none)
movement_am_moving:    bool = False
movement_arrived:      bool = False
movement_what_happened: str = "none"
```

### CognitivePlan — `runtime/spine/plan.py` lines 196–200
All five fields declared on CognitivePlan.

### Spine passthrough — `runtime/spine/spine.py` lines 1427–1428
```python
"movement_where_i_am", "movement_want_to_go",
"movement_am_moving", "movement_arrived", "movement_what_happened",
```
Listed in the plan field extraction pass — all five fields flow into exec_decision.

### Prompt injection — `runtime/prompt_builder.py` line 969–971
```python
_mov_arrived = exec_decision.get("movement_arrived", False)
_mov_where   = exec_decision.get("movement_where_i_am", "")
```
Consumed in prompt construction. When arrived=True and where is non-empty, eLo's prompt references the arrival event.

### Movement outcome log — `runtime/movement_outcome.py`
SP-22 / WO-NAV-001 — outcome records written to `last_move` in `elo_spatial.json`. `_proprioceptive_faculty()` reads `last_move.arrived` and `last_move.outcome` each turn.

## INTENT PROOF status

PARTIAL: All five states are wired from Unity → `elo_spatial.json` → spine → CognitivePlan → exec_decision → prompt. The INTENT PROOF requirement ("real turn where eLo references its own movement in expressed output") requires a live session with DesktopBuddy active and a move in progress or recently completed. Builder cannot execute this. Board/David must verify in a real session.

## Source of truth

Data flows from Unity NavAgent through `elo_spatial.json`. When DesktopBuddy is not running, file absent → faculty returns `{}` → all five fields default to empty/false. The consequence chain is live only with an active DesktopBuddy session.
