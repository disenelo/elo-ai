# Board Review — 0087: Motion State JSON Read
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Real body movement (walk/run/jump/teleport) feeds the physical battery via
`blender/motion_state.json` (written by Designer whenever Unity moves eLo).
Ingest it in `ambient/ambient_engine.py` `_battery_tick()`.

---

## Implementation status at review time

Already implemented. `ambient/ambient_engine.py:476-494`:

```python
# ── WO-MOTION-STATE-READ: ingest Designer's motion_state.json ────────
# Silent no-op if the file doesn't exist yet or is stale (> 2s old).
try:
    with open(_MOTION_STATE_PATH) as _ms_f:
        _ms = json.load(_ms_f)
    if time.time() - float(_ms.get("timestamp", 0)) < 2.0:
        _ms_motion = state.get("motion") or {}
        _ms_phys = _ms.get("physical_state")
        _ms_anim = _ms.get("animation")
        if _ms_phys:
            _ms_motion = dict(_ms_motion, physical_state=_ms_phys)
        if _ms_anim:
            _ms_motion = dict(_ms_motion, animation=_ms_anim)
        state = dict(state, motion=_ms_motion)
except Exception:
    pass
```

`_MOTION_STATE_PATH = os.path.join(..., "blender", "motion_state.json")` at line 441.

**How teleport drains**: `animation="teleport"` → `infer_physical_activity()` returns
`"teleporting"` (via ANIMATION_TO_PHYSICAL) → `_tick_physical("teleporting")` fires
`drain_physical(0.15)` on first frame of the activity. Physical battery: 1.0 → 0.85.

**Freshness gate**: timestamp must be within 2 seconds. Stale file (Unity paused or
prior session) is silently ignored.

---

## Tests — `tests/test_motion_state_json_read.py`

2 new tests:

1. `test_motion_state_teleport_drains_physical_battery` — fresh file with teleport →
   `get_physical() < 1.0` and `_physical_engaged == True`
2. `test_stale_motion_state_is_ignored` — 10s-old file → `_physical_engaged == False`

```
tests/test_motion_state_json_read.py — 2 passed in 0.44s
```

Both tests monkeypatch `_MOTION_STATE_PATH` and `_read_state` to isolate from live
server state (observed in test_s4: live file had "sitting" while test asserted "walk").

---

## Board decisions required

None. Implementation correct, both tests passing.

*Builder 1 · 2026-10-11*
