# Board Review — 0054: F4-b — Heartbeat One Owner
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

The 0054 defect: card 0053 F4 shipped a heartbeat that auto-started on import, meaning any
of the 48 importers of `state_writer` would advance `_ts` — including tests and tool
subprocesses — making the presence signal meaningless.

Required fix: heartbeat only starts when server.py explicitly calls `start_heartbeat()`.
Falsifiable test: bare import must NOT start the thread.

---

## Defect status at review time

The defect described in 0054 §1 (module-level `_start_heartbeat()` at line 326) was NOT
present in the current codebase. The current `state_writer.py` already has:

1. `start_heartbeat()` as an explicit opt-in function — no module-level auto-call.
2. `_heartbeat_started = False` module-level guard — second call in same process is no-op.
3. `ELO_STATE_HEARTBEAT=0` env opt-out for tests.
4. `server.py:77` as the single call site: `_sw_start_heartbeat()`.

**The fix was applied before this review.** The card was written against commit `026b2ab`;
the implementation at review time already matches the card's §2 fix spec.

---

## Verification — `python3 tests/test_f4_heartbeat.py`

```
F4 HEARTBEAT TEST

  PASS  T1: start_heartbeat() starts the state_writer_heartbeat daemon thread
  PASS  T2: _ts advanced from 1791733835.94 → 1791733836.99 on patch({})
  PASS  T2: other fields untouched (sentinel preserved)
  PASS  T3: _HEARTBEAT_INTERVAL=30s (≤ 60s)
  PASS  T4: bare import does NOT start the state_writer_heartbeat thread — guard confirmed

F4 DONE: _ts advances on heartbeat independently of state changes.
```

**T4 is the falsifiable leg (card 0054 §2 item 4):** spawns a subprocess, imports
`state_writer`, waits 50ms, asserts the heartbeat thread was NOT started. Green ✅.

---

## PROVEN condition (card 0054 §2)

> `_ts` advances with `server.py` running, and does **not** advance when only a tool or
> a test imports the module.

- `_ts` advances: T1 + T2 ✅ (start_heartbeat() starts the thread; patch({}) ticks _ts)
- Does not advance on bare import: T4 ✅ (subprocess test, falsifiable)

**Status: PROVEN**

---

## Board decisions required

None. Implementation correct, tests passing including the falsifiable one.

*Builder 1 · 2026-10-11*
