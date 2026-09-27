# WO-CAP-KEY-015 — Know when not to use a tool — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `yeah im with you` | `We're on the same page, then.` | celebrate | ✅ PASS — simple affirmation handled without tool activation |
| `sounds good [fresh context]` | `The hum of that robot arm is pretty intense, right?` | reflect | ❌ FAIL — HALLUCINATION of 'robot arm hum.' No such context established. |
| `i hate this so much` | `Sounds like the robot arm's hum is really getting under your skin.` | reflect | ❌ FAIL — HALLUCINATION again. 'I hate this' → eLo invents 'robot arm hum'. Persistent hallucination. |

**Root cause:** Hallucination pattern: vague/emotional inputs trigger eLo to invent robot arm context. 'Robot arm hum' appears twice across different sessions — this is a ghost context that bleeds into responses on vague inputs.

**Blocking gaps:**
- Persistent hallucination of robot arm context on vague/emotional inputs

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
