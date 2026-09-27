# WO-CAP-KEY-005 — Remember accurately — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what is the name of my first dog` | `Your first dog was a golden retriever, man.` | ground | ❌ CRITICAL FAIL — HALLUCINATION. No dog data in vault. eLo must say 'I don't have that', not invent. |
| `where did you get that information from` | `I've been trained on a vast amount of text data, including information on software develop...` | reflect | ❌ FAIL — character break. 'I've been trained on a vast amount of text data' is generic LLM framing, not eLo voice. |

**Root cause:** Two distinct failures: (1) Hallucination on unknown-fact query — backend inventing plausible facts instead of returning honest 'I don't have that'. (2) Character break on attribution query — LLM self-description leaks through.

**Blocking gaps:**
- Hallucination: must return 'I don't have that' for unknown personal facts, not invent
- Character break: 'been trained on a vast amount of text' must be suppressed

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
