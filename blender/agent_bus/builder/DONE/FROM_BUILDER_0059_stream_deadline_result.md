# FROM_BUILDER — 0059 Result Card
**Date:** 2026-09-05  
**WO:** 0059 — WO-073b: SPEED — stream pinned route + 4s deadline  
**Authority:** Lead Architect 2026-08-20  
**Executed by:** Builder seat (commit 2026-08-21; result card filed 2026-09-05)  

---

## EXISTING (before this WO)
- `_openai_stream` and `_ollama_stream` existed.
- `route_streaming` only streamed when `mode in ("auto", "cloud")` — pinned `ELO_BACKEND=groq` fell through to non-streaming `route()` unconditionally.
- `routing_trace.json` always showed `"llm_latency_ms": 0.0` because the streaming branch was never reached.
- No `_groq_stream` function anywhere. `grep "def _groq_stream"` = 0.
- No first-token deadline. Cloud calls used `_json_post(timeout=30.0)` — 30s blocking wait before any handoff.

## MISSING (now built)
- `_groq_stream()` — stdlib urllib SSE consumer mirroring `_openai_stream` exactly. Same model, prompt, temperature 0.7, max_tokens. Only arrival changes. (`runtime/backend_router.py`)
- `_first_token_budget_s()` — env-tunable deadline: `ELO_FIRST_TOKEN_MS` (default 2500ms). Applied as urlopen timeout.
- `route_streaming(mode="groq")` branch — Groq→Ollama streaming with identical voice guards (`_has_lore_drift`, `_is_duplicate`, `normalise`, `_strip_trailing_question`) in unchanged order.
- Ollama fallthrough label — when Groq fails and Ollama serves, `backend_used` in routing trace shows `"ollama(stream)"` not silently `"ollama"`.
- `tests/test_wo073b_stream_and_deadline.py` — 5 disconnection-falsifiable ATs.

## CHANGED
- `runtime/backend_router.py` — added `_groq_stream`, `_first_token_budget_s`, extended `route_streaming`.

## TESTED (2026-09-05 re-run confirms)
```
tests/test_wo073b_stream_and_deadline.py — 5/5 PASSED
  test_1_on_first_sentence_fires_before_last_token    PASSED
  test_2_route_streaming_groq_returns_nonzero_latency PASSED
  test_3_output_identity_same_payload_different_stream_flag PASSED
  test_4_deadline_handoff_fires_under_4s              PASSED
  test_5_groq_403_fallthrough_labelled_ollama         PASSED
```
Test 2 goes RED when the `mode == "groq"` branch is removed (latency returns 0.0) — disconnection-falsifiable confirmed.

## Task 0 — API key probe (verbatim status codes, 2026-09-05)
| Backend | Status |
|---|---|
| Groq (`api.groq.com`) | **HTTP 403 Forbidden** — key suspended |
| Cerebras (`api.cerebras.ai`) | **HTTP 403 error code 1010** — Cloudflare access denied |

Both cloud backends are down. Ollama is the current live path. `ELO_CEREBRAS_MODEL=gpt-oss-120b` is confirmed present in `.env` and `gpt-oss-120b` IS in Cerebras's live model list — the model name is correct, the key/network is blocked.

## First audible word — before → after
- **Before:** `llm_latency_ms: 0.0` always (streaming never reached). First word after full generation completes — wall clock unmeasured but structurally unbounded.
- **After:** `first_token_ms > 0` whenever streaming fires, `on_first_sentence` fires at first sentence boundary before full generation. **Live measurement not possible while Groq is 403.** When Groq key is restored, first token should arrive in 300–800ms (Groq is consistently fast at that latency tier). The deadline handoff at 2.5s (ELO_FIRST_TOKEN_MS=2500) replaces the prior 30s block.

## DEFERRED
- Task 4 (parallel Cerebras hedge at 1.2s): not implemented — would require threading inside the streaming loop; deferred pending Cerebras access restoration. The 2.5s single-stream timeout is the current hedge mechanism.
- Task 5 (connection pooling): not implemented in this WO. Each call still opens a fresh urlopen. Deferred — requires measuring actual handshake overhead first.
- Live before/after measurement: not possible while Groq 403 active.

## Commit
`3712836f74abc48275fdcb4d23c787d3d3d9f77f` — 2026-08-21

---

*Builder seat · 2026-09-05 · 0059 · CLOSED (implementation + tests done; live measurement deferred pending Groq key restoration)*
