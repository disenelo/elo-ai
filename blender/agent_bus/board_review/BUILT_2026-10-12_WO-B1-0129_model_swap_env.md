# Board Review — WO-B1-0129: Model swap — pin inner thought to reply model
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

0118 latency fix reaches ~10s. Final 5s gap: Ollama reloads qwen2.5-coder:14b after inner thought loaded mistral-nemo:12b. Option 1 (Board recommendation): set `ELO_INNER_THOUGHT_MODEL=qwen2.5-coder:14b`.

---

## What was built

### Code already correct

`runtime/inner_thought_first.py` line 75 already reads:
```python
_MODEL = os.environ.get("ELO_INNER_THOUGHT_MODEL", "mistral-nemo:12b")
```

No code change needed — the env var path was already there.

### .env updated

Added to `~/elo-ai/.env`:
```
ELO_INNER_THOUGHT_MODEL=qwen2.5-coder:14b
```

`.env` is gitignored (contains API keys) — change is on disk, not in git. Board verifies in `.env` directly.

---

## Effect

After server restart: both inner thought and reply generation use `qwen2.5-coder:14b`. Ollama keeps the model warm between turns — no model reload overhead. Expected: `load_duration ≈ 0ms` in CT0031 log, total turn time ≤ 8s.

---

## Verification

3 consecutive turns after restart. CT0031 log lines should show:
- `load_duration` near 0ms (model already warm)
- `prompt_eval` ~250 tokens (0118 KV-cache path active)
- Total ≤ 8s

---

## Board decisions required

Confirm quality is acceptable with `qwen2.5-coder:14b` for inner thought. If inner thought quality degrades vs. mistral-nemo:12b, the fallback options remain:
- `ELO_INNER_THOUGHT_MODEL=mistral-nemo:12b` (separate model, 5s overhead)
- Skip inner thought for voice/Alexa turns (already done)

*Builder 1 · 2026-10-12*
