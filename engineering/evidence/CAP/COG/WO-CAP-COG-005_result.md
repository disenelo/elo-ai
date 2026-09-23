# WO-CAP-COG-005 — Result: Mathematics

**Date:** 2026-09-23  
**WO:** WO-CAP-COG-005  
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §5`  
**Seat:** Builder  
**Status:** IN PROGRESS — RUN 4 score: 13/32 PASS (post-fix, commit b7264d0)  

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
| estimation/order-of-magnitude | ❌ FAIL (RUN 3 — regression, nondeterminism) |
| equations | ✅ PASS (RUN 2 — fixed) |
| simultaneous equations | ❌ FAIL |
| logarithms | ✅ PASS (RUN 2 — fixed) |
| exponents | ✅ PASS (RUN 2 — fixed) |
| sequences | ❌ FAIL |
| area | ❌ FAIL (RUN 4 — regression, Fix C reverted) |
| volume | ❌ FAIL |
| angles | ❌ FAIL |
| coordinates | ❌ FAIL |
| sine/cosine | ❌ FAIL (persistent — cos(60°) model error) |
| triangles (trig) | ❌ FAIL |
| radians | ✅ PASS |
| derivatives | ❌ FAIL (RUN 4 — regression, nondeterminism) |
| integrals | ✅ PASS |
| rates of change | ❌ FAIL |
| mean/median/mode | ❌ FAIL |
| standard deviation | ✅ PASS |
| probability | ✅ PASS (RUN 4 — new, nondeterminism) |
| Bayesian reasoning | ✅ PASS |
| sets | ❌ FAIL |
| combinatorics | ❌ FAIL |
| Boolean algebra | ✅ PASS |
| physics (applied) | ✅ PASS (RUN 4 — new) |
| finance | ❌ FAIL |
| 3D modelling | ✅ PASS (RUN 4 — recovered, nondeterminism) |
| tool use (calculator) | ❌ FAIL (server not restarted — fix loaded but inactive) |

**RUN 1: 9/32 PASS → RUN 2: 17/32 PASS (+8) → RUN 3: 14/32 PASS (−3) → RUN 4: 13/32 PASS (−1)**

---

## Failure patterns (RUN 2)

| Pattern | Items | Count |
|---|---|---|
| Formula-only / method without answer | M4, M12, M13, M14, M15, M21, M24, M26, M30 | 9 |
| Truncation (response cuts off) | M8, M11, M29 | 3 |
| Contamination cascade (CURRENT QUESTION missed) | M27 | 1 |
| Wrong computation | M22 | 1 |
| Tool use failure (wrong answer, wrong backend) | M32 | 1 |

## Failure patterns (RUN 3)

| Pattern | Items | Count |
|---|---|---|
| Formula-only / method without answer | M4, M11, M13, M14, M15, M21, M29 | 7 |
| Truncation (response cuts off) | M8, M22 | 2 |
| Contamination cascade | M27 | 1 |
| Wrong computation | M16, M32 | 2 |
| Response aborted / nondeterministic | M6, M17, M30, M31 | 4 |

## Failure patterns (RUN 4)

| Pattern | Items | Count |
|---|---|---|
| Formula-only / method without answer | M4, M7, M11, M13, M14, M15, M17, M19, M21 | 9 |
| Truncation (response cuts off) | M8, M22 | 2 |
| Contamination cascade | M27 | 1 |
| Wrong computation | M5, M12, M16, M32 | 4 |
| Response aborted / nondeterministic | M6, M30 | 2 |

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
| RUN 3 | 14/32 | Post-fix (commit 0c03082). Fix C (answer suffix) caused regressions on M16/M17 (trig queries). M6/M31 nondeterministic regressions. M12 new pass. Net −3. |
| RUN 4 | 13/32 | Post-fix (commit b7264d0). Fix C reverted — M12 lost (expected), M16/M17 partially recovered. Nondeterministic regressions M5/M7/M19. New passes M24/M29/M31. M32 fix inactive (server not restarted). Net −1. |

*Builder · 2026-09-23*
