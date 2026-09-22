# WO-CAP-COG-005 — Result: Mathematics

**Date:** 2026-09-22  
**WO:** WO-CAP-COG-005  
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §5`  
**Seat:** Builder  
**Status:** IN PROGRESS — RUN 1 score: 9/32 PASS  

---

## What was done

Ran a 32-question multi-turn test covering every §5 Mathematics sub-domain:  
Basic math · Algebra · Geometry · Trigonometry · Calculus · Statistics · Discrete/Sets · Applied · Tool use  

Post-P0 code (commits 88f8414 + b1af7c2). Server: Ollama backend (mistral-nemo:12b).

---

## Coverage — 32 §5 source items

| Item | Verdict |
|---|---|
| arithmetic | ❌ FAIL |
| fractions | ❌ FAIL |
| percentages | ✅ PASS |
| ratios | ❌ FAIL |
| units/conversions | ✅ PASS |
| estimation/order-of-magnitude | ✅ PASS |
| equations | ❌ FAIL |
| simultaneous equations | ❌ FAIL |
| logarithms | ❌ FAIL |
| exponents | ❌ FAIL |
| sequences | ❌ FAIL |
| area | ❌ FAIL |
| volume | ❌ FAIL |
| angles | ❌ FAIL |
| coordinates | ❌ FAIL |
| sine/cosine | ❌ FAIL |
| triangles (trig) | ❌ FAIL |
| radians | ✅ PASS |
| derivatives | ❌ FAIL |
| integrals | ✅ PASS |
| rates of change | ❌ FAIL |
| mean/median/mode | ❌ FAIL |
| standard deviation | ✅ PASS |
| probability | ❌ FAIL |
| Bayesian reasoning | ✅ PASS |
| sets | ❌ FAIL |
| combinatorics | ❌ FAIL |
| Boolean algebra | ✅ PASS |
| physics (applied) | ❌ FAIL |
| finance | ❌ FAIL |
| 3D modelling | ✅ PASS |
| tool use (calculator) | ❌ FAIL |

**RUN 1: 9/32 PASS**

---

## Failure patterns

| Pattern | Items | Count |
|---|---|---|
| Formula-only (no computed answer) | M4, M12, M13, M14, M15, M17, M21, M24, M26, M29 | 10 |
| Contamination cascade | M7, M9, M16, M27 | 4 |
| Calculator routing misfire | M1, M2, M10 | 3 |
| Truncation (incomplete response) | M8, M11, M19 | 3 |
| Tool use failure (wrong answer) | M32 | 1 |
| No answer | M30 | 1 |
| Partial answer only | M22 | 1 |

---

## Files changed

None. This WO is diagnostic/evidence only. Fixes require a separate engineering pass.

---

## Full evidence

`engineering/evidence/CAP/COG/WO-CAP-COG-005_evidence.md`

---

## Run history

| Run | Score | Notes |
|---|---|---|
| RUN 1 | 9/32 | Post-P0 baseline. Formula-only pattern dominant (10 fails). Contamination cascade (4 fails) same structural bug as COG-004. |

*Builder · 2026-09-22*
