# WO-066 — Ambient engine / idle utterances ("feels alive" between conversations)

**Owner:** Builder (eLo OS). **Status:** DONE IN_REVIEW — Builder `2c7e6be`, 7/7 AT
(`test_wo066_ambient_callback.py`), RUN 10. Architect re-verified 7/7 (2026-08-07).
**Note:** this WO-066 is the AMBIENT ENGINE (Builder's committed number). The Intent Gatekeeper that was
briefly mis-numbered WO-066 moved to **WO-072** (git history is permanent; ambient owns 066).

## Problem
`ambient_engine.py` exported only `start()`/`stop()`. `server.py` imported `register_ambient_callback`,
which didn't exist → `ImportError`, caught silently → the ambient engine never started → eLo produced NO
idle utterances between conversations. A direct "feels alive" hole for Presentable v1 (eLo went inert when
not spoken to).

## Fix (shipped)
Added `_ambient_cb = None` module state + `register_ambient_callback(cb)` to the public API; `_run()`'s idle
utterance timer calls the brain-backed `ambient_thought()` via a daemon thread when a callback is registered,
falling back to the static pool otherwise. No other code touched. 7/7 AT.

## Verify (David)
Relaunch the app → the log should read `[eLo server] ambient engine started (Brain callback registered)`
instead of the skip message; eLo then produces idle utterances / brain-backed ambient thoughts between turns.

## Lane
Builder (Python). Presentable "feels alive" contributor.
