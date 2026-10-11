# Board Review — WO-0106: eLo Persistent Daemon
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

eLo daemon — long-running process that loads config/kernel/memory/faculties once and
keeps them alive. AWAKE/RESTING/SLEEP life loop with STIRRING beat on wake from SLEEP.
Thresholds: 5 min idle → RESTING, 20 min resting → SLEEP (confirmed David 2026-10-09).

Deliverables: `runtime/elo_daemon.py` with `FacultyRegistry`, `EloDaemon`, life loop
background thread, state transitions, graceful SIGTERM shutdown.

---

## Implementation status

Already landed (commit `c3fccba`). Prior board filing at `4c25ecb`.
AWAKE-guard fires via `EloDaemon.status()` added in `3a08e47`.

---

## Tests — `tests/test_elo_daemon.py`

```
python3 -m pytest tests/test_elo_daemon.py -v
→ 18 passed in 25.10s
```

| Group | Tests |
|-------|-------|
| FacultyRegistry | loads-without-error, capability_dispatcher_loaded, same-object-across-loads |
| DaemonStartStop | starts-awake, life-thread-running, life-thread-exits, registry-loaded |
| DaemonHandleRequest | math/time/unknown, no-reload-between, marks-awake |
| DaemonLifeLoop | ticks-during-idle, tick-count-increments, inner-life-not-suspended |
| DaemonStateTransitions | resting-after-idle, back-to-awake, stirring-beat-from-sleep |

---

## Board decisions required

None. FREEZE_V1_LOCK untouched.

*Builder 1 · 2026-10-11*
