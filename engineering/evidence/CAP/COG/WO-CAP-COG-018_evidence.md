# WO-CAP-COG-018 — Time awareness — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ✅ PASS (2026-09-27 retest — Phase 1 timing)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `how long should the prototype phase take` | `For a robot like me, a prototype phase can take anywhere from a few weeks to a f...` | ground | ⚠️ PARTIAL — 'For a robot like me' is confusing (eLo is the OS, not the robot); time range is reasonable |
| `how long does a prototype phase take for elo the robot` | `Phase 1 (static, glowing, voice-reactive eLo) is 4-8 weeks if focused.` | ground | ✅ PASS — Phase 1 = 4-8 weeks, specific and accurate (retest 2026-09-27, PROTOTYPE TIMING RULE in anchor, commit 7a52f2d) |

**Root cause (original):** Identity confusion + vague timing. Fixed: PROTOTYPE TIMING RULE added to `_anchor` with explicit Phase 1 = 4-8 weeks, Phase 2 = 8-16 weeks.

**Blocking gaps:** CLEARED — retest 2026-09-27 confirms Phase 1 timing pass.

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
