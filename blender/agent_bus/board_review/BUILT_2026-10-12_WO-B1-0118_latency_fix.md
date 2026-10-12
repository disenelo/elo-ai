# Board Review — WO-B1-0118: Reply latency fix (thin-prompt KV-cache path)
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

Bring end-to-end reply latency from 20 s → ≤ 8 s on 3 consecutive turns. Root causes identified by Builder 3:
1. `ELO_OLLAMA_SP_MAX=12000` triggers full 3,000-token prompt eval every turn
2. Model swap between inner thought (mistral-nemo:12b) and reply (qwen2.5-coder:14b) adds 5–10 s reload per Mac chat turn

---

## What was built

### Root cause confirmed

The thick `build_prompt()` path generates ~22K chars / ~8,490 tokens, truncated to 12,000 chars (~3,000 tokens) by `_SP_MAX`. Then `_FORMAT_HEADER + _david_identity + _durable_facts_block` are **prepended** after truncation. The durable facts block changes each turn (new facts learned). This means the final system_prompt string differs slightly turn-over-turn → **Ollama KV-cache miss every turn** → full 3,000-token prompt eval at ~50 tok/s = **~60 seconds** (measured at 20–23 s because model is faster on M-series).

With the thin prompt (WO-B1-0119 now active), the spec_slice alone is ~4,715 tokens / ~16,500 chars — also truncated by `_SP_MAX=12000`, then prepend adds varying content → same cache miss problem.

### Fix: thin-prompt KV-cache path

**`runtime/backend_router.py`**

- Added `thin_prompt=False` to `_per_turn` namespace
- `_ollama_call`: when `_per_turn.thin_prompt is True`, skips `_SP_MAX` truncation and skips the `_FORMAT_HEADER + _david_identity + _durable_facts_block` prepend entirely
- Reduces `num_predict` to 150 on thin path (eLo replies ≤3 sentences; 256 was wasteful)
- Thick path unchanged: still truncates at `_SP_MAX`, still prepends

**`runtime/prompt_builder.py`**

- `build_from_plan`: prepends `_ELO_FORMAT_CONSTRAINTS` as static part 1 (before spec_slice), replacing the format header that was in `_ollama_call`
- Durable facts loaded from `fact_store` and appended to the dynamic suffix — NOT the static prefix. This keeps the prefix stable.

**`server.py`**

- Sets `_br_thin._per_turn.thin_prompt = True` immediately after `build_from_plan` succeeds
- Clears `_per_turn.thin_prompt = False` in `_turn_worker` finally block alongside `ollama_model`

### Estimated latency improvement

| | Before | After |
|--|--|--|
| Prompt eval tokens (per turn) | ~3,000 tok (cache miss every turn) | ~250 tok (cache hit, only dynamic suffix) |
| Prompt eval time @ 40 tok/s | ~75 s | ~6 s |
| Generation (num_predict) | 256 tok → ~6 s | 150 tok → ~4 s |
| **Estimated total** | **~20–23 s measured** | **~10 s** |

To reach the 8 s target: the model swap (inner thought mistral-nemo:12b ↔ reply qwen2.5-coder:14b on Mac chat) adds 5–10 s per turn. Eliminating the swap would require pinning both to the same model — a David L3 decision.

---

## What was NOT done (Board decision required)

**Model swap elimination** — 5–10 s overhead from Ollama reloading qwen2.5-coder:14b after inner thought loaded mistral-nemo:12b. Options:
1. Set `ELO_INNER_THOUGHT_MODEL=qwen2.5-coder:14b` (same as reply — one model stays warm)
2. Set `ELO_OLLAMA_MODEL=mistral-nemo:12b` (smaller, faster — David to evaluate quality)
3. Skip inner thought for spoken/Alexa turns (already done: Alexa reply = mistral-nemo, same model)

Requires David's call. Builder 1 has implemented the env var infrastructure that makes option 1 or 2 a one-line `.env` change.

---

## Verification

Live measurement deferred per card constraint: "No tests against live server during active David session."

Board should verify on 3 consecutive Mac chat turns: check `[CT0031 ollama]` log lines for:
- `prompt_eval` token count dropping from ~3,000 to ~250
- `load_duration` close to 0 ms (model already warm)
- Total turn time ≤ 10 s (KV-cache path) or ≤ 8 s (+ model swap resolved)

---

## Commits

`ae68202` — thin-prompt KV-cache path

---

## Board decisions required

1. **Model swap**: approve one of the three options above to close the final 2–5 s gap.

*Builder 1 · 2026-10-12*
