## 0113 — Dream gate: add EloDaemon.status() so the AWAKE guard actually fires

**WO:** 0113 · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal (one line)
Dream cycle stops firing while David is actively in conversation, because the daemon can now be asked how idle it is.

## Scope — exactly this, nothing more
- Add `status()` method to `EloDaemon` returning `{"state", "last_request_ts", "resting_since_ts", "tick_count", "running"}`.
- Add a dedicated test that proves `_maybe_emit_dream_intent` suppresses when idle < 300s.
- Nothing else — do not touch `ambient_engine.py`, which is already written against this contract.

## Root cause
`ambient/ambient_engine.py:783-790` calls `get_daemon().status()` to pull `last_request_ts` for the "David is still here" gate. `EloDaemon` does not implement `status()` — the AttributeError is swallowed by the surrounding `except Exception: pass`, so the gate is a no-op in production. The sit→dream regression (Designer report 2026-10-09) traces to this: `physical_state=tired` + calm → dream intent fired while David was typing.

## Files to touch
`runtime/elo_daemon.py` · `tests/test_dream_gate_daemon_status.py` (new)

## Test (must pass WITHOUT David)
`python3 -m pytest tests/test_dream_gate_daemon_status.py -q` → expected: 2 passed

## Done when
Implemented + test green + committed. Fill in Result + Live turn needed below. Move to BUILT/.

## Result (seat fills this in before moving to BUILT)
- commit: 3a08e47 — WO-0113 dream gate: add EloDaemon.status() so AWAKE guard fires
- test: `python3 -m pytest tests/test_dream_gate_daemon_status.py tests/test_elo_daemon.py -q` → **20 passed** (2 new + 18 regression)
- notes: no shared-file edit (elo_daemon.py is Builder 1 own-file, no lock needed). `ambient_engine.py` untouched — it was already written against this contract; only the missing method was blocking it.

## Live turn needed (seat fills this in — exact words)
> David: types a message, waits 30s, keeps typing — eLo must NOT play lay-down sleep pose.
> eLo should respond: stays AWAKE; dream intent not emitted while David is active in conversation (observable in `elo.health` log — no `CHAIN-3: … intent=dream` line within 5 min of a message).
