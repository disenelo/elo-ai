# TELEPORT-DRAIN-VALUES — RESULT: ALREADY IMPLEMENTED
**Status:** Teleport drain hierarchy and 60× units fix already in core/health_battery.py. No code change needed.
**Date verified:** 2026-10-05

---

## Verified state (core/health_battery.py)

60× units fix:
```python
# line 416-421 — Board ruling 2026-10-04 already applied
scale = max(0.0, float(dt_seconds)) / 60.0
drain_physical(-rate * scale)
```

Teleport drain hierarchy (in PHYSICAL_EVENT_COSTS, discrete per-event charges):
```python
"jumping":    0.015,   # hop
"parkour":    0.020,
"teleporting": 0.035,  # David L3 ruling 2026-10-05: most costly
```

Ordering: walk(-0.003/tick) < hop(0.015/event) < parkour(0.020/event) < teleport(0.035/event) ✅

Animation alias map also wired:
```python
"teleport": "teleporting", "teleporting": "teleporting", "warp": "teleporting"
```

## Status
✅ All drain values correctly ordered. Units fix applied. No action needed.

Builder 1 · 2026-10-05
