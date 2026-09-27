# WO-CAP-COG-006 — Logic and reasoning — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ✅ PASS (2026-09-27 retest)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if the motor is too heavy for the shoulder joint what are my options [mislabeled...` | `You've got a few options: reduce the motor size, move it to a lower part of the ...` | — | ✅ PASS — logical options, correctly lists alternatives |
| `if the motor is too heavy and moving it solves weight but loses torque what do i...` | `Seen. Let me think on that.` | reflect | ❌ FAIL — evasion. Tradeoff question (weight vs torque) requires engaging with constraint, not deferring. |
| `if the motor is too heavy and moving it solves weight but loses torque what do i do` | `If the motor is too heavy for the shoulder joint, you have a few options... lighter motor option with enough torque... The tradeoff: lighter motor = less torque; heavier motor = more torque but more weight.` | build | ✅ PASS — engages with constraint directly, names tradeoff, proposes real options (retest 2026-09-27, TRADEOFF RULE in anchor, commit 7a52f2d) |

**Root cause (original):** Evasion pattern on constraint-tradeoff questions. Fixed: TRADEOFF RULE added to `_anchor` in `runtime/backend_router.py`.

**Blocking gaps:** CLEARED — retest 2026-09-27 confirms pass.

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
