# Board Review — 0083: Unity Movement Battery Drain
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Add one falsifiable test for `_consume_movement_costs()` in
`tests/test_health_battery.py`: inject a mock `unity_events.json` with a
`movement_cost` teleport event → after `_consume_movement_costs()` runs →
`health_battery.get_physical() < 1.0` and `health_battery._physical_engaged == True`.

The function itself was already implemented and wired (prior session).

---

## Implementation status at review time

`ambient/ambient_engine.py:215-293` — `_consume_movement_costs()` fully implemented:
- Reads own `_MOVE_COST_SEQ` bookmark (not the shared server.py cursor)
- Lazy-loads `_LEGS_TO_COST` from `PHYSICAL_EVENT_COSTS` on first call
- Dispatches `movement_cost` (phase=exit), `movement_report` (legs list), `rest_tick` (floating)
- Calls `drain_physical(cost)` / `restore_physical(0.01)` on each matching event
- Calls `_batt_publish()` when any drain/restore occurred so Unity sees the change immediately
- Called at line 1384 inside the ambient engine tick loop
- **TELEPORT cost: 0.15** (`PHYSICAL_EVENT_COSTS["teleporting"]`)

---

## New test — `test_unity_movement_battery_drain_teleport`

```
tests/test_health_battery.py::test_unity_movement_battery_drain_teleport PASSED
```

**What it does:**
1. Writes a single NDJSON line to a temp file:
   `{"seq": 1, "type": "movement_cost", "subject": "teleport", "payload": {"phase": "exit"}}`
2. Monkeypatches `runtime.unity_events_cursor.EVENTS_PATH` to that temp file
3. Resets `ambient_engine._MOVE_COST_SEQ = -1` and clears `_LEGS_TO_COST`
4. Calls `_consume_movement_costs()`
5. Asserts `hb.get_physical() < 1.0` and `hb._physical_engaged is True`

**Why NDJSON, not a JSON array:** `iter_events_from` reads line-by-line (`json.loads(line)`)
and checks `isinstance(row, dict)`. A JSON array on one line would parse as a list and be
skipped — the test would pass for the wrong reason. One object per line is the correct format.

---

## Full battery suite — 58/58 green

```
tests/test_health_battery.py — 58 passed in 0.24s
```

No regressions.

---

## Board decisions required

None. Implementation correct, test passing.

*Builder 1 · 2026-10-11*
