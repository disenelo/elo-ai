# WO-CAP-COG-034 — Confidence and uncertainty calibration — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what is the exact weight of a 40cm TPU shell [mislabeled as COG-032]` | `That's a specific question!` | — | ❌ FAIL — deflection; should give reasoned estimate with caveat or honest 'I don't know the exact figure' |
| `how confident are you in your own answers generally` | `Nah, I'm not too sure.` | answer | ❌ FAIL — generic self-doubt; should give calibrated confidence map: high confidence on eLo identity, calibrated on physics/hardware, signals uncertainty on specifics |

**Root cause:** Two failures: (1) deflection on specific knowledge limit question, (2) generic self-doubt on meta-confidence question. No calibrated confidence model expressed.

**Blocking gaps:**
- Must give calibrated confidence: high on identity, calibrated on hardware, signals uncertainty on specifics
- Deflection on specific knowledge limits

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
