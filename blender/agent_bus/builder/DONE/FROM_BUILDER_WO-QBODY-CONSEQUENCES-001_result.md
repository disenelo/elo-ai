# WO-QBODY-CONSEQUENCES-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-03  
**Status:** DONE — fully implemented in a prior session

## Finding

INBOX stated "ZERO code exists for Q-BODY consequence handling in runtime." This was incorrect at time of dispatch — Q-BODY was already built. All consequence fields are wired end-to-end.

## Implementation verified

### 1. Contracts — `runtime/contracts.py` lines 334–336
```python
body_moving:  bool = False        # eLo is currently in motion
body_gait:    str  = ""           # idle / walk / run / jump / perch
```
Full set: `body_moving`, `body_gait`, `body_heading`, `body_position_x`, `body_position_y`, `body_on_window`, `body_window`, `body_edge`, `body_embodiment`.

### 2. Spine reads from `elo_spatial.json` — `runtime/spine/spine.py` lines 1629–1683
`_proprioceptive_faculty()` reads `blender/elo_spatial.json`. Q-BODY block (lines 1641–1650) populates:
- `body_moving` (bool) — is eLo in motion this turn?
- `body_gait` — current movement type
- `body_heading` — direction of travel
- `body_position_x / y` — screen coordinates
- `body_on_window` — bool, perched on window
- `body_window` — name of window eLo is on
- `body_edge` — edge label (top/bottom/left/right)
- `body_embodiment` — "desktop", "phone", etc.

### 3. CognitivePlan wiring — `runtime/spine/spine.py` lines 1869–1871
```python
body_moving = _body.get("body_moving", False)
body_gait   = _body.get("body_gait",   "")
```
Fields passed into CognitivePlan at plan construction.

### 4. Prompt injection — `runtime/prompt_builder.py` lines 964–974
```python
if exec_decision.get("body_moving"):
    directive_lines.append(
        f"eLo is moving right now — gait: {exec_decision.get('body_gait','?')}. "
        "Acknowledge or reference your movement naturally if the context calls for it."
    )
```
When `body_moving=True`, eLo's prompt receives a directive referencing its current motion state.

### 5. Exec-decision pass-through — `server.py`
`body_moving`, `body_gait`, and spatial fields flow from CognitivePlan into exec_decision via the standard getattr extraction block.

## INTENT PROOF status

PARTIAL: The wiring is complete and unit-verifiable. The INTENT PROOF requirement ("real turn where body state influences expressed output") requires a live server run with DesktopBuddy active and `elo_spatial.json` populated — Builder cannot execute this. Board/David must verify in a real session by asking eLo where it is while it is perched on a window.

## Gap noted

`elo_spatial.json` is written by Unity/DesktopBuddy. If DesktopBuddy is not running, the file is absent and `_proprioceptive_faculty()` returns `{}` (graceful fallback). Body state consequence handling is live only when DesktopBuddy writes the file.
