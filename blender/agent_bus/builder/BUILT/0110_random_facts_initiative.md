# WO-B1-0110 — Random Facts Initiative (delivery wire)
**Seat:** Builder 1  
**Date:** 2026-10-11  
**Commit:** 8d1d4e3

## Result

Builder 2's `maybe_signal()` (b19423a) fires from `life_tick` in the daemon — writes `self/state/random_fact.json` with `pending: true` when eLo should surface a fact unprompted.

Builder 1 wired the delivery side in the ambient tick (server.py):
- Checks `is_pending()` from `faculties.inner_thought.random_fact`
- If pending and David is present: calls `pick_random_fact()` from `wkg_faculty`, speaks via `_voice_speak()`
- Calls `clear_pending()` whether or not a fact was found (no phantom pending state)
- Exception-wrapped, non-blocking

The existing 12%-draw path in the ambient tick (line 1333) is unchanged — the new path is the cross-process daemon signal.
