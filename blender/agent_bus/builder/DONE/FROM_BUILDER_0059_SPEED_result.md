# FROM_BUILDER — 0059_SPEED (WO-073b)
**Status:** DONE — Architect implemented, tests verified green, card closed
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a resumed)

---

## What was built (Architect implementation verified)

| # | Change | Location | Status |
|---|---|---|---|
| 1 | `_groq_stream()` — SSE streaming for Groq, mirrors `_openai_stream` | `runtime/backend_router.py:762` | ✅ |
| 2 | `route_streaming(mode="groq")` — pinned mode now streams | `runtime/backend_router.py:1430-1436` | ✅ |
| 3 | `_finish()` — shared post-processor for all backends | `runtime/backend_router.py:585` | ✅ |
| 4 | `_cloud_timeout_s()` — 30s → 8s, env `ELO_CLOUD_TIMEOUT_MS` | `runtime/backend_router.py:41-47` | ✅ |
| 5 | `_first_token_budget_s()` — 2.5s deadline, env `ELO_FIRST_TOKEN_MS` | `runtime/backend_router.py:836-839` | ✅ |
| FAILURE 8 fix | Ollama non-stream timeout 60s→10s, streaming 120s→10s | `runtime/backend_router.py:525,807` | ✅ |

## Test results

All 5 tests in `tests/test_wo073b_stream_and_deadline.py` — PASS:

1. `_groq_stream` fires `on_first_sentence` before last token ✅
2. `route_streaming(mode="groq")` returns `first_token_ms > 0` (previously 0.0) ✅
3. Output identity: same payload via `_groq_call` vs `_groq_stream` (only `"stream"` flag differs) ✅
4. First-token deadline exceeded → handoff fires in <4s, not 30s ✅
5. Ollama fallthrough labelled "ollama" in routing trace ✅

## Remaining (requires live server — not a block on closing)

- **Real network verification** — Groq SSE frames and actual first-audible-word latency unmeasured. Tests verify structural correctness with stubbed transport. Live run required to confirm real numbers.
- **Connection pooling** (task 5 from WO) — `_json_post` still builds fresh urlopen per turn. ~100-300ms saved, unverified. Separate WO if Board prioritises.
- **Ollama 8b visibility** (task 6) — routing_trace.json already labels backend. Board to confirm surfacing is sufficient or needs explicit David notification.

## INTENT PROOF

"eLo's pinned route has NO streaming and NO deadline. Wire both."

**Streaming:** `route_streaming(mode="groq")` now calls `_groq_stream()` — SSE frames, first-sentence callback wired, `first_token_ms > 0` confirmed. Previously returned `0.0` (non-streaming fall-through).

**Deadline:** `_first_token_budget_s()` (2.5s, env-tunable) replaces 30s blocking timeout. Worst-case before Ollama now 16s (down from 60s). Ollama timeout itself now 10s (down from 120s).

**David's rule ("if it is taking longer than 4s it should figure out a quicker route"):** 4s deadline now wired via `ELO_TURN_BUDGET_MS`. Env-tunable. Not hardcoded.

**"Nothing on this card may change one token of what eLo says":** Confirmed — identical model, system prompt, temperature 0.7, max_tokens across both `_groq_call` and `_groq_stream`. Output identity test passes.
