# WO-CAP-COG-031 — World knowledge vs personal knowledge — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ✅ PASS (2026-09-27 retest)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do you know vs what does the world know` | `I've been trained on a vast amount of text data, giving me knowledge of a wide r...` | reflect | ❌ FAIL — 'I've been trained on a vast amount of text data' is generic LLM framing; eLo is not a language model in character; character break |
| `what do you know vs what does the world know` | `I know what you've shared directly — projects, vision, DISENELO, this OS; broader knowledge I carry — design, code, culture, the 4-act story, robotics, engineering; and the external world — everything, searchable, impersonal, not uniquely mine.` | reflect | ✅ PASS — three-layer distinction, no LLM framing, no 'trained on text data' character break (retest 2026-09-27, KNOWLEDGE DISTINCTION RULE strengthened with explicit LLM-framing block, commit 6805f62) |

**Root cause (original):** Strong parametric LLM self-description bleeding through. Fixed: KNOWLEDGE DISTINCTION RULE updated with explicit 'NEVER say I was trained on text data or any variant.'

**Blocking gaps:** CLEARED — retest 2026-09-27 confirms pass.

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
