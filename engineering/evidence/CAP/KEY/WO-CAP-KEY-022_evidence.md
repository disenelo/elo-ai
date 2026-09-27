# WO-CAP-KEY-022 — Track projects and tasks — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `plan out the next three steps for getting elo to phase 1` | `Fine-tune my language patterns and emotional resonance for the eLo universe. You sound dif...` | build | ❌ FAIL — (1) state leak 'You sound different when talking about robot' injected; (2) plan wrong domain (should be physical build steps for Phase 1 robot) |

**Root cause:** State leak from pattern observer contaminating planning response. Phase 1 robot = static glowing eLo that speaks — plan should include: hardware list, chassis fabrication, NeoPixel wiring, Pi setup, voice integration. Instead returns language-tuning steps.

**Blocking gaps:**
- State leak contaminating response
- Plan domain wrong — not Phase 1 robot build steps

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
