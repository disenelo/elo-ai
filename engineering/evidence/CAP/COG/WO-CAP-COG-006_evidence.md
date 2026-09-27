# WO-CAP-COG-006 — Logic and reasoning — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if the motor is too heavy for the shoulder joint what are my options [mislabeled...` | `You've got a few options: reduce the motor size, move it to a lower part of the ...` | — | ✅ PASS — logical options, correctly lists alternatives |
| `if the motor is too heavy and moving it solves weight but loses torque what do i...` | `Seen. Let me think on that.` | reflect | ❌ FAIL — evasion. Tradeoff question (weight vs torque) requires engaging with constraint, not deferring. |

**Root cause:** One PASS (from mislabeled COG-004 test), one FAIL on direct logic test. Evasion pattern on complex tradeoff questions.

**Blocking gaps:**
- Evasion on constraint-tradeoff logic: 'Seen. Let me think on that' instead of engaging

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
