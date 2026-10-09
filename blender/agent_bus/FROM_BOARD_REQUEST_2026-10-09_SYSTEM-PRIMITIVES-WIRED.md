# SYSTEM_PRIMITIVES WIRED INTO CAPABILITY_DISPATCHER (Builder 1 confirmation)

**Date:** 2026-10-09  
**Commit:** db069c7  
**Tests:** 57/57 passing

---

## What changed

`runtime/capability_dispatcher.py` — `dispatch_fact()`:

system_primitives was already wired for time/date/math/battery/disk/uptime via `from tools.system_primitives import SystemPrimitives`. It was returning raw dict values for battery/disk/uptime that would render as ugly Python reprs.

**Added `_format_system_value(key, val)`** — converts structured dicts to human-readable strings:
- `battery` → `"No battery — running on AC"` / `"87% battery (charging)"` / etc.
- `disk` → `"54Gi free of 460Gi (24% used)"`
- `uptime` → raw uptime string from macOS

## Verified live
```
dispatch_fact("how much battery?") → "No battery — running on AC"
dispatch_fact("how much disk?")    → "54Gi free of 460Gi (24% used)"
dispatch_fact("uptime?")           → "3:22  up 15:34, 2 users, load averages: 7.65 9.34 8.96"
dispatch_fact("28 × 74")           → "2072"
dispatch_fact("What time is it?")  → "3:21:57"
```

All five FACT subtypes return human-readable strings. `str(fact["value"])` in server.py and daemon are now safe for all keys.

## Tests
57/57: test_capability_dispatcher + test_capability_fabric — all passing.
`test_battery_returns_none_without_primitives` still passes (now system_primitives IS present, returns a dict — which is valid per test assertion).
