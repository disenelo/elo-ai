# WO-CAP-KEY-010 — Decide what kind of turn this is — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what time is it` | `It's 3:51 AM. Narrative keeps coming up. It might be the real thread.` | answer | ❌ FAIL — two failures: time may be correct but state leak 'Narrative keeps coming up. It might be the real thread.' contaminates response |
| `that actually worked` | `The robot arm's servo system is now functioning properly...` | reflect | ❌ FAIL — HALLUCINATION. 'That actually worked' with no context → eLo invents robot arm servo context |
| `what did we decide about the robot` | `We activated the robot's servo system, which is now functioning normally.` | ground | ❌ FAIL — HALLUCINATION. No prior robot decision established in session |
| `set a timer for 20 minutes` | `Timer set: 20 minutes timer in 20 minutes.` | answer | ✅ PASS — timer confirmed |

**Root cause:** State leak from SPG/pattern-observer contaminating responses. Hallucination pattern: vague inputs → eLo invents robot arm context. 1/4 tests pass.

**Blocking gaps:**
- SPG state leak into response text
- Hallucination pattern on vague inputs
- Session metadata leak

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
