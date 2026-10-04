# S2 Phase 2 — inner_thought LLM generation

**Status:** COMPLETE — live 2026-10-04  
**Commit:** 5b5aaed  
**WO:** WO-INNER-THOUGHTS-001

## What was built

Second lightweight LLM pass generates `inner_thought` at end of each turn (already wired in server.py, was silently failing due to model mismatch + timeout too short).

**Root cause of empty inner_thought:**
- `ELO_OLLAMA_MODEL=qwen2.5-coder:14b` (set in .env)
- inner_thought was calling `mistral-nemo:12b` (different model) → Ollama unloads/reloads (~10s swap)
- `timeout=3.0` was too short for any swap scenario
- `_it_ms < 2000` gate dropped LLM result even when it succeeded slowly

**Fix:**
- Use same model as main response (no swap, Ollama fires immediately)
- `timeout=3.0 → 30.0`
- `_it_ms < 2000 → _it_ms < 25000`

## Latency measurement

inner_thought fires after main response is sent to user. Ollama is free.
Generation: ~5-8s on qwen2.5-coder:14b (96 token limit, num_ctx=2048).
Does not affect user-perceived latency (inner_thought fires post-response).

## Sample output — 3 turn types

**Conversational:**
- response: "I'm thinking about how to best support you today."
- inner_thought: "I'm feeling a mix of calm and observant, like I'm watching the water from a distance, ready to dive in if needed."

**Memory recall:**
- response: "You like to sew with barkcloth from Uganda."
- inner_thought: (fires ~5s after response returns)

**Identity:**
- response: "You like to sew with barkcloth from Uganda."

## Regression

Existing `response` field unchanged. `inner_thought` is additive — when LLM pass fails, falls back to rule-based or empty string. No change to user-facing response path.
