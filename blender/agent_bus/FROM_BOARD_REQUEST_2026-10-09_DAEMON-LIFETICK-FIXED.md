# DAEMON LIFE_TICK — FIXED (Builder 1 confirmation)

**Date:** 2026-10-09  
**Commit:** db069c7  
**Tests:** 18/18 passing

---

## What changed

`runtime/elo_daemon.py` `_tick()` method:

**Before (wrong):**
```python
from runtime.inner_thought_first import tick as _it_tick
_it_tick(state=state.value, idle_seconds=idle_seconds)
```

**After (correct):**
```python
from faculties.inner_thought import life_tick as _life_tick
_life_tick(state.value)
```

## Verified live
```
from faculties.inner_thought import life_tick, RESTING, SLEEP
life_tick(RESTING) → {'actions': ['carried_threads'], 'state': 'RESTING', 'ok': True, 'elapsed_ms': 18.0}
```
18ms. Never raised. Contract verified.

## STIRRING beat added [DAVID 2026-10-09]
On incoming request during SLEEP: daemon transitions to RESTING, fires one life_tick at RESTING pace, then transitions to AWAKE. test_stirring_beat_from_sleep: PASS.

## Thresholds confirmed [DAVID 2026-10-09]
5min AWAKE→RESTING, 20min RESTING→SLEEP. `[PROPOSAL]` annotation removed.

## Builder 2 action
Gate is open. IS ELO acceptance suite can run.
