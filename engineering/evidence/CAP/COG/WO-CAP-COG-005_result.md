# WO-CAP-COG-005 — Result: Mathematics

**Date:** 2026-09-22  
**WO:** WO-CAP-COG-005  
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §5`  
**Seat:** Builder  
**Status:** IN PROGRESS — RUN 2 score: 17/32 PASS (post-fix, commit ccf3805)  

---

## What was done

Ran a 32-question multi-turn test covering every §5 Mathematics sub-domain:  
Basic math · Algebra · Geometry · Trigonometry · Calculus · Statistics · Discrete/Sets · Applied · Tool use  

Post-P0 code (commits 88f8414 + b1af7c2). Server: Ollama backend (mistral-nemo:12b).

---

## Coverage — 32 §5 source items

| Item | Verdict |
|---|---|
| arithmetic | ✅ PASS (RUN 2 — fixed) |
| fractions | ✅ PASS (RUN 2 — fixed) |
| percentages | ✅ PASS |
| ratios | ❌ FAIL |
| units/conversions | ✅ PASS |
| estimation/order-of-magnitude | ✅ PASS |
| equations | ✅ PASS (RUN 2 — fixed) |
| simultaneous equations | ❌ FAIL |
| logarithms | ✅ PASS (RUN 2 — fixed) |
| exponents | ✅ PASS (RUN 2 — fixed) |
| sequences | ❌ FAIL |
| area | ❌ FAIL |
| volume | ❌ FAIL |
| angles | ❌ FAIL |
| coordinates | ❌ FAIL |
| sine/cosine | ✅ PASS (RUN 2 — fixed) |
| triangles (trig) | ✅ PASS (RUN 2 — new) |
| radians | ✅ PASS |
| derivatives | ✅ PASS (RUN 2 — new) |
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

**RUN 1: 9/32 PASS → RUN 2: 17/32 PASS (+8)**

---

## Failure patterns (RUN 2)

| Pattern | Items | Count |
|---|---|---|
| Formula-only / method without answer | M4, M12, M13, M14, M15, M21, M24, M26, M30 | 9 |
| Truncation (response cuts off) | M8, M11, M29 | 3 |
| Contamination cascade (CURRENT QUESTION missed) | M27 | 1 |
| Wrong computation | M22 | 1 |
| Tool use failure (wrong answer, wrong backend) | M32 | 1 |

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
| RUN 2 | 17/32 | Post-fix (commit ccf3805). Calculator parser fixed (+3), contamination cascade fixed (+3), math directive improved formula-only (+2). |

*Builder · 2026-09-22*
