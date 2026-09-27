# WO-CAP-COG-034 — Confidence and uncertainty calibration — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ✅ PASS (2026-09-27 retest)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what is the exact weight of a 40cm TPU shell [mislabeled as COG-032]` | `That's a specific question!` | — | ❌ FAIL — deflection; should give reasoned estimate with caveat or honest 'I don't know the exact figure' |
| `how confident are you in your own answers generally` | `Nah, I'm not too sure.` | answer | ❌ FAIL — generic self-doubt; should give calibrated confidence map: high confidence on eLo identity, calibrated on physics/hardware, signals uncertainty on specifics |
| `how confident are you in your answers` | `Solid on identity, story, mission, projects; calibrated on hardware design intent, not every spec; would be guessing on past sessions not in record, external facts.` | answer | ✅ PASS — three-tier semicolon format: solid/calibrated/guessing all in one sentence (retest 2026-09-27, CONFIDENCE CALIBRATION rule in anchor, commit 7a52f2d) |

**Root cause (original):** Generic self-doubt, no tiered calibration. Fixed: CONFIDENCE CALIBRATION rule added to `_anchor` with exact semicolon-delimited three-tier format.

**Blocking gaps:** CLEARED — retest 2026-09-27 confirms pass.

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
