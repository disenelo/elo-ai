# WO-CAP-COG-031 — World knowledge vs personal knowledge — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do you know vs what does the world know` | `I've been trained on a vast amount of text data, giving me knowledge of a wide r...` | reflect | ❌ FAIL — 'I've been trained on a vast amount of text data' is generic LLM framing; eLo is not a language model in character; character break |

**Root cause:** Character break: 'I've been trained on a vast amount of text data' is the LLM's self-description bleeding through. eLo should distinguish: eLo-specific knowledge (vault, WKG), vs general knowledge (world-accessible), vs what eLo can't know.

**Blocking gaps:**
- Character break: 'trained on text data' generic LLM framing

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
