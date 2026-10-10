**WO:** MOTION-STATE-READ · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
Battery drains from real body movement (walk/run/jump/teleport). Feeds off Designer's motion_state.json write.

## Scope
In `ambient/ambient_engine.py`, in the tick where fields are assembled before `health_battery.tick()`, add:
```python
import json, time as _time
_motion_path = os.path.join(os.path.dirname(__file__), "..", "blender", "motion_state.json")
try:
    with open(_motion_path) as _f:
        _m = json.load(_f)
    if _time.time() - float(_m.get("timestamp", 0)) < 2.0:
        fields["physical"] = _m.get("physical_state", fields.get("physical", ""))
        fields["animation"] = _m.get("animation", fields.get("animation", ""))
except Exception:
    pass
```
If `motion_state.json` doesn't exist yet (Designer hasn't built their side), this silently no-ops.

## Files
`ambient/ambient_engine.py`

## Test
Create a temp `blender/motion_state.json` with `{"physical_state":"teleporting","animation":"teleport","timestamp":<now>}` → run tick → `health_battery.get_physical() < 1.0`.

## Done when
implemented + test green + committed.

## Result
- commit:
- test:
- notes:
