# P1 TEXT-REPLY-BUG — Static Analysis + Fix
**WO:** FROM_ARCHITECT_2026-10-03_TEXT-REPLY-BUG.md
**Date:** 2026-10-05
**By:** Builder 1
**Commit (fix):** 86b46e0

---

## Root Cause 1 — FIXED: Silence gate race condition

**When:** Executive chose `_action == "silence"`.

**Bug:** `_early_tts` callback fires during streaming (line ~5981: `_voice_speak(sentence)`). This happens BEFORE the silence gate (line 7359) runs `response = ""; _bubbles = []`. Result: David hears audio, but no text bubble appears.

**Fix (commit 86b46e0):** Added guard at top of `_early_tts`:
```python
if str(_action or "").strip().lower() == "silence":
    return
```
`_action` is set at line 4012 (from `exec_decision.get("action", "reflect")`), before the streaming call at line 5984. The guard is safe and deterministic.

**Prior fixes already in place:**
- Line 5395-5398: `response = None` removed from system_action failure path (would null the JSON "response" field)
- Line 7389-7404: Repetition-suppression + early TTS mismatch recovery (uses `_early_tts_sentence[0]` as text when response gate suppresses)
- Line 7885-7888: Type guard — ensures `response` is always a string before HTTP return

---

## Root Cause 2 — OPEN: voice_rewrite latency

**When:** Every turn where `_needs_rewrite(candidate)` returns True.

**Effect:** voice_rewrite makes a SECOND LLM call (line 6836-6849) via `router_route(... action="voice_rewrite" ...)`. Early TTS fires immediately with the first sentence of the PRE-voice_rewrite response. Text bubble only appears after voice_rewrite completes (adds 1-3s with local Ollama).

**David observes:** "latency in DISENELO presence text reply" — hears eLo speak, then waits for text.

**No code fix here.** voice_rewrite is intentional. Options for Board consideration:
- Option A: Skip voice_rewrite in streaming mode (text and audio stay consistent; register gains sacrificed)
- Option B: Apply voice_rewrite pre-stream (raises per-turn latency everywhere)
- Option C: Accept: fast audio, slow text is the trade-off of streaming + register rewrite

---

## Root Cause 3 — OPEN: voice_rewrite produces governance text

**When (edge case):** voice_rewrite LLM call confabulates governance text ("WO-049" format). WO-049 scrub at line 6882-6891 replaces response with `"—"`. Unity displays `"—"` as text — not missing, but wrong.

**Frequency:** Low. Requires the voice_rewrite LLM to produce WO-format output, which the WO-049 guard catches.

**No code fix here.** WO-049 is already the correct guard. The symptom is `"—"` appearing in the chat bubble, not missing text.

---

## Text reply path summary (server.py)

```
streaming LLM → _early_tts fires (line 5981) → first sentence spoken
                ↓
full response assembled from stream
                ↓
voice_rewrite (second LLM call, lines 6836-6849)
                ↓
scrubs: _sanitise → WO-043 → WO-049 → WO-036b → D-3 → identity → NAME RULE → authority → response gate
                ↓
_bubbles = response.split("\n\n") (line 7156)
                ↓
guards: silence gate / pong leak / abort fragment / D-6
                ↓
return {"response": response, "bubbles": _bubbles, ...}  (line 7889-7897)
```

Unity reads `bubbles` for text display (`ParseResponseBubbles`). If `_bubbles = []`, no text appears.

---

## Acceptance test (live server required)

1. David sends any message → text appears in DISENELO Presence within latency window, every time.
2. Send message that triggers silence action → neither audio nor text fires.
3. Check logs for `NAME_RULE_SCRUB` warnings → "the user" never reaches David.

Builder 1 · 2026-10-05
