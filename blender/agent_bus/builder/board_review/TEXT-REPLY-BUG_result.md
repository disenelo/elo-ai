# TEXT-REPLY-BUG — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-04  
**Dispatch:** `FROM_ARCHITECT_2026-10-03_TEXT-REPLY-BUG.md`  
**Status:** DONE — committed `536df84`

---

## Root Cause

`_early_tts()` fires during streaming (server.py:5887, `on_first_sentence` callback) **before** `elo_response_gate` runs. When `elo_response_gate` detects a repetition (window=1 exact match), it returns `""` at line 1010. The D-6 handler then sets `_bubbles = []` and leaves `response = ""`. Unity receives `{"response": ""}` — no text shown. TTS had already spoken the first sentence.

---

## Fix

**D-6 block** (server.py ~7180): when `_was_dedup=True` and `_early_tts_sentence[0]` has content, set `response` and `_bubbles` from the early sentence instead of leaving both empty.

This keeps TTS and chat in sync: whatever TTS spoke also appears in the chat log. When early TTS has NOT fired (non-streaming path), the existing silent-turn behaviour is preserved.

---

## Files changed

| File | Lines | Change |
|---|---|---|
| `server.py` | 7180-7204 | D-6: recover early TTS sentence as chat text on repetition-suppressed turns — 24 lines added, 3 removed |

---

## Commit

`536df84` — `TEXT-REPLY-BUG: recover early-TTS sentence as chat text on repetition-suppressed turns`

---

## Verification status

⚠️ **Requires live session** — repetition suppression is probabilistic (only fires on exact identical consecutive responses). Cannot verify in a unit test without mocking the streaming path and elo_response_gate together. Board/David must verify in a live session by:
1. Saying the same thing twice in quick succession (e.g. "hey" → "hey")
2. Confirming second turn shows text in DISENELO Presence chat

---

## Notes

- The commit at `59cea79` (previous session) suppressed inner_thought TTS on silent/suppressed turns. That guard is still correct — inner thought now fires normally on the recovered response.
- The `_tts_text` variable (set at line 6985, before D-6) remains `""` for the suppressed turn — the main TTS at line 7033 does not re-fire. Only the inner thought TTS fires, as expected.
- `elo_response_gate` docstring says "never returns empty" but returns `""` at line 1010 — that's a docstring bug, not functional. No change made.
