# WO-B1-0118 — Reply latency: bring 20 s → 8 s
**Seat:** Builder 1  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11  
**Source:** Builder 3 measurement `TO_BOARD_2026-10-11_ELO-REPLY-LATENCY.md` + David: "that's Builder 1's to speed up"

---

## Measured facts (Builder 3, 2026-10-11)

| Turn | Model | Time |
|---|---|---|
| Alexa "open elo" (mistral-nemo:12b, no swap) | reply | **19.4 s** |
| Mac chat turns | qwen2.5-coder:14b reply | ~22–23.6 s |
| audit llm_latency_ms (every LLM turn 2026-10-08) | — | 21.6–23.3 s |

Target from card 0010: **under 8 s end to end.**

## Likely causes (B3 identified; B1 to confirm)

1. **Prompt size**: `ELO_OLLAMA_SP_MAX=12000` chars (~3,000 tokens) evaluated before every reply. Code comment itself estimates ~20 s prompt eval on a 12–14B model.
2. **Model size**: 12B/14B on Mac.
3. **Model swap** on chat turns: inner thought mistral-nemo ↔ reply qwen-coder, ~5–10 s reload per turn (`TO_BOARD_2026-10-08_OLLAMA-MODEL-SWAP.md`).
4. Inner thought pre-response (dd3aecf) adds up to 0.8 s wait (bounded by timeout_s=0.8 — acceptable).

## Options (B1's call, David's L3 if model change)

- **Trim system prompt** for spoken/Alexa turns — a short "voice mode" prompt. Ollama keeps prompt cache only if the prefix is identical between turns; trimming the SP for voice turns breaks the cache. B1 to weigh.
- **Keep reply model resident** (`keep_alive`) — stop per-turn swap. The model stays loaded; next turn hits cache.
- **Reduce SP for all turns** — cull dead context blocks that eLo doesn't need on every reply. No character impact, just token count.
- **`ELO_OLLAMA_SP_MAX` reduction** — lower the cap. Read current value from env; propose a new value to David.

## Done when

Builder 1 measures: end-to-end latency (David speaks → eLo first word) ≤ 8 s on at least 3 consecutive turns. File to Board with before/after timing log. Do not close until measured, not estimated.

## Constraints

- Read `ELO_OLLAMA_MODEL` from env; never hardcode.
- Do not touch `spine.py` or `backend_router.py` without Board co-ordination.
- No tests against live server during active David session.
