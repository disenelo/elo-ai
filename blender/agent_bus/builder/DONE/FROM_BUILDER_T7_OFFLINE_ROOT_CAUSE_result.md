# FROM BUILDER — T7 Mock Fallback ("running offline") — ROOT CAUSE FIXED

**Date:** 2026-09-12 (§91 continued)
**Status:** DONE — ROOT CAUSE FOUND AND FIXED — LIVE VERIFIED
**Files changed:**
- `server.py` (world-graph gate: stop mutating `raw`)
- `runtime/backend_router.py` (ollama timeout: 10s → 45s; num_ctx: 8192 → 16384)

---

## David's question

"Why would eLo say he's running offline?"

---

## Full Root Cause Chain

There were TWO compounding bugs, not one:

### Bug 1: `raw` mutation (masked the real bug)

`server.py:2578` — the world-graph gate overwrote `raw` (the user's actual message) with a
`[WORLD_KNOWLEDGE...]` prefixed string. This caused `response_gate` to log "check-1: low
input→response overlap (0.00)" (comparing enriched raw vs real response). This was a WARNING
only — not the suppression cause.

**Fixed:** `_world_graph_ctx` variable now holds the WKG content. Injected into `g_ctx` (system
prompt) at line ~3285. `raw` remains the original user message throughout the turn.

### Bug 2: Ollama 10s timeout fires on every turn (ACTUAL cause of mock fallback)

`_ollama_stream` and `_ollama_call` both had `timeout=10.0` (or `min(10.0, ...)`).

The system prompt is ~5500 tokens (living_presence_spec.txt alone = 5434 tokens). Ollama's
prompt evaluation for a 5500-token prompt on llama3.1:8b takes **15-27 seconds** on local CPU.

The 10s socket timeout fires BEFORE the first streaming chunk arrives → exception raised →
fallback to `route()` → `_ollama_call` also has 10s timeout → also fails → `_mock_fallback()`.

`_mock_fallback` checks `_is_factual_request(user_input)`: pattern `r"\bwhat is\b"` matches
"what is elo planet like..." → returns `_HONEST_DEGRADATION_MSG` = "I can't reason through
that right now — I'm running offline."

**Fixed:** Timeout raised to 45s when no cloud keys are set (local-only mode). `num_ctx` raised
8192 → 16384 to accommodate the full prompt without truncation.

---

## Live Evidence (direct route_streaming test)

```
System: 21849 chars (~5462 tokens)
User: 84 chars
Time: 19.5s
Backend: ollama(stream)
Response: "A quiet Tuesday on eLo planet... It's as if the air is filled with the gentle hum of curiosity.
           The skies are a soft, pale blue, like the color of a worn notebook page."
```

Response gate: passed (not suppressed). "running offline" eliminated.

---

## What remains

- `backend_router.py` timeout is conditional on `_has_cloud = any cloud keys set`. When David
  adds Groq/OpenAI keys, the old 10s timeout restores for cloud calls. Ollama stays at 45s only
  in pure-local mode.
- First turn after server restart is slow (~20s) due to prompt eval. Subsequent turns benefit
  from ollama's KV cache. This is a hardware constraint — not fixable without reducing the
  system prompt or upgrading hardware.

*Builder · 2026-09-12 · §91 continued*
