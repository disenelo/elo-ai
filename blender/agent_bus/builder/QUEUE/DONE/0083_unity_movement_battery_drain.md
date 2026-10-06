**WO:** UNITY-MOVEMENT-BATTERY · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
eLo's battery drops when he teleports, runs, jumps. Right now it never does — `physical_battery` is null and `_physical_engaged` is always False on desktop.

## Scope — exactly this, nothing more
In `ambient/ambient_engine.py`, add `_consume_movement_costs()` called once per 0.5s tick:

```python
from runtime.unity_events_cursor import iter_events_from, read_cursor, write_cursor
from core.health_battery import PHYSICAL_EVENT_COSTS, drain_physical

_LEGS_TO_COST = {
    "teleport":     PHYSICAL_EVENT_COSTS["teleporting"],   # 0.035
    "parkour":      PHYSICAL_EVENT_COSTS["parkour"],       # 0.020
    "parkour_drop": PHYSICAL_EVENT_COSTS["parkour"],
    "wall_jump":    PHYSICAL_EVENT_COSTS["parkour"],
    "climb":        PHYSICAL_EVENT_COSTS["parkour"],
    "climb_down":   PHYSICAL_EVENT_COSTS["parkour"],
    "hop":          PHYSICAL_EVENT_COSTS["jumping"],       # 0.015
    "drop":         PHYSICAL_EVENT_COSTS["jumping"],
}

def _consume_movement_costs() -> None:
    cursor_seq = read_cursor()
    max_consumed = cursor_seq
    for event in iter_events_from(cursor_seq):
        seq = event.get("seq", -1)
        etype = event.get("type", "")
        if etype == "movement_cost":
            subject = str(event.get("subject", "")).lower()
            payload = event.get("payload", {})
            if payload.get("phase", "exit") == "exit":
                cost = _LEGS_TO_COST.get(subject) or PHYSICAL_EVENT_COSTS.get(subject)
                if cost:
                    drain_physical(cost)
        elif etype == "movement_report":
            legs = event.get("legs", [])
            for leg in (legs if isinstance(legs, list) else []):
                cost = _LEGS_TO_COST.get(str(leg).lower())
                if cost:
                    drain_physical(cost)
        if isinstance(seq, int) and seq > max_consumed:
            max_consumed = seq
    if max_consumed > cursor_seq:
        write_cursor(max_consumed)
```

Call `_consume_movement_costs()` in the existing tick loop.

## Files to touch
`ambient/ambient_engine.py`

## Test
`python3 tests/test_health_battery.py` — all existing pass.
Write one new test: inject a mock `unity_events.json` with a `movement_cost` teleport event → after `_consume_movement_costs()` runs → `health_battery.get_physical() < 1.0` and `health_battery._physical_engaged == True`.

## Done when
Implemented + test green + committed. `blender_state.json` after a teleport shows `physical_battery` non-null and `elo_battery` below 1.0.

**Full spec + evidence:** `blender/agent_bus/builder/FROM_ARCHITECT_2026-10-06_UNITY-MOVEMENT-BATTERY-FIX.md`
**Designer's original report:** `blender/agent_bus/designer/DONE/FROM_DESIGNER_2026-10-05_TELEPORT-DRAIN-NOT-APPLIED.md`

## Result
- commit:
- test:
- notes:
