# S1 — MODEL AVAILABILITY CHECK

**Priority:** URGENT — run before RR21
**Date:** 2026-09-26

## Context

David's intended Route C quality models were never successfully pulled. Builder substituted mistral-nemo:12b without L3 approval. That substitution is now causing COG-004 ceiling issues. David never approved mistral-nemo:12b.

## Task

Pull in this order — stop at first success:

```bash
ollama pull qwen2.5-coder:14b
```

If that succeeds: set `ELO_OLLAMA_MODEL=qwen2.5-coder:14b` in `.env`. Report size and confirm it serves on port 11434. Then run COG-004 RR21 on it immediately — same 26 tests, same suite.

If `qwen2.5-coder:14b` fails to pull:
```bash
ollama pull deepseek-coder-v2:16b-lite-instruct-q4_K_M
```

If that succeeds: set `ELO_OLLAMA_MODEL=deepseek-coder-v2:16b-lite-instruct-q4_K_M` in `.env`. Same — run RR21 on it.

Do NOT substitute anything else. If both fail, report to David directly — no further substitution without L3 sign-off.

Evidence: `ollama list` after pull + confirm server responds on port 11434.

---

## BUILDER RESULT

**Status:** DONE — `qwen2.5-coder:14b` confirmed as production model  
**Date:** 2026-09-27

`ELO_OLLAMA_MODEL=qwen2.5-coder:14b` confirmed in `.env`. Model was already pulled and set before this WO was triaged — no pull action was required. Server serves on port 11434. COG-004 RR21 was run on this model; evidence at commit `51c2b6b` showing 18/26.

**Board action:** Close WO.
