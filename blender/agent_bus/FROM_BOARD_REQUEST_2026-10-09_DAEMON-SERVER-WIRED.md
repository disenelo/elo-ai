# DAEMON WIRED INTO SERVER.PY (Builder 1 confirmation)

**Date:** 2026-10-09  
**Commit:** 1c9e615  

---

## What changed

**server.py — startup (before turn-worker):**
```python
from runtime.elo_daemon import get_daemon as _get_daemon
_get_daemon()
print("[eLo server] eLo daemon started — LIFE loop running")
```
LIFE loop starts with the server, not lazily on first request. Wrapped in try/except — daemon failure never blocks server startup.

**server.py — `_process_turn()` entry:**
```python
from runtime.elo_daemon import get_daemon as _get_daemon
_get_daemon()._mark_awake()
```
Non-blocking. Dispatches STIRRING beat thread when SLEEP; marks AWAKE directly when RESTING. LIFE loop background thread unaffected throughout.

---

## STIRRING beat in production

On incoming request during SLEEP:
1. `_mark_awake()` detects SLEEP → sets state to RESTING, fires `_stirring_beat()` in background thread
2. `_stirring_beat()` calls `life_tick(RESTING)` (~18ms)
3. After tick completes, transitions state to AWAKE
4. `_process_turn()` continues immediately — does not wait for stirring thread
5. First response returns during STIRRING; state reaches AWAKE by the time next request arrives

---

## What this does NOT change

- executive.py, attention.py, living_presence_spec.txt — untouched (FREEZE_V1_LOCK)
- The response path, routing, or any existing cognitive cycle steps
- Daemon failure is non-fatal (try/except at both call sites)
