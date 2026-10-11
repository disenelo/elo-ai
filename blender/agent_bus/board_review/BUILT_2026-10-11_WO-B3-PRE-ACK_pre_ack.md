# Board Review — WO-B3-PRE-ACK: pre_ack.py — eLo speaks before slow B3 ops
**Date:** 2026-10-11
**Builder:** Builder 1
**Commit:** 3332caf
**Status:** READY FOR BOARD REVIEW

## What was built

`runtime/pre_ack.py` — B3 calls `pre_ack.emit(capability, user_text)` at the
top of any slow tool operation so eLo says something while the work runs.

- Non-blocking (fires background TTS thread, returns < 1 ms)
- Never raises (even on voice failure)
- Phrase banks per capability: document_write / device_control / spotify_play / default

## Design choice

Used `voice.voice_engine.speak()` directly from the tool thread rather than the
`ack_pending` heartbeat approach (interim guidance in earlier B3 response).
Direct call is simpler, cleaner, no server-side poll needed.

## Test coverage

**8/8 PASS** (`tests/test_pre_ack.py`) — voice_engine stubbed so no TTS fires in CI.

Board verify: B3 calls `from runtime import pre_ack; pre_ack.emit("document_write")`
before a slow doc write — eLo says a phrase immediately while the write runs.

*Builder 1 · 2026-10-11*
