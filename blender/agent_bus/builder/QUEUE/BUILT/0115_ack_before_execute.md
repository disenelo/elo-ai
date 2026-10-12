# WO-B1-0115 — Ack Before Execute (auto-wired for all tools)
**Seat:** Builder 1  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11  
**Status:** PARTIALLY DONE — `pre_ack.py` exists (commit 3332caf, 8/8 AT). Not yet auto-wired for all tool calls in server.py. Board returning it.

---

## What's left

`runtime/pre_ack.py` is built. Builder 3 can call `pre_ack.emit()` manually before slow operations. That's not enough.

**Required:** Every tool call in `server.py` must emit a pre-ack phrase BEFORE the tool executes. David should never wait in silence for any tool.

## How

In `server.py`, at the point where a tool call is identified and about to execute:
- Call `pre_ack.emit(tool_name)` or equivalent
- The phrase goes to TTS immediately (background, non-blocking)
- Then the tool runs

This covers ALL tools — Spotify, weather, web search, document creation, company control — not just document_write.

## Done when

Board tests 3 different tool-requiring requests. First thing eLo says each time is the pre-ack phrase — before any tool result. File to Board with test log.
