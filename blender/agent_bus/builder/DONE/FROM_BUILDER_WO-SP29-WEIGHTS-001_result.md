# FROM_BUILDER — WO-SP29-WEIGHTS-001 Result Card
**Date:** 2026-09-05  
**WO:** WO-SP29-WEIGHTS-001 — SP-29 Significance Weight Ratification  
**Priority:** P1 · Closes: BA-02  
**Executed by:** Builder seat  

---

## Summary

Ratified SP-29 weights implemented in `runtime/significance_faculty.py`. All 9 ATs pass.

---

## Deliverable status

| Item | Status |
|---|---|
| 13 ratified weights block | CHANGED |
| Startup normalisation assertion `sum == 1.0 ±1e-6` | CHANGED |
| env-var override (`ELO_SP29_WEIGHTS`) | CHANGED |
| config-file override (`config/sp29_weights.json`) | CHANGED |
| `_load_weights()` function | CHANGED |
| Module docstring rationale (dimension roles) | CHANGED |
| `significance_diagnostics()` function | CHANGED |
| 13 vs 14 discrepancy documented in comment | CHANGED |
| `safety` weight documented as gate, not attention dim | CHANGED |

---

## Acceptance tests

| AT | Condition | Result |
|---|---|---|
| AT-1 | `sum(w for k,w in _WEIGHTS.items() if k != "safety") == 1.0 (±1e-6)` | PASS |
| AT-2 | `relationship` (0.18) ≥ `embodiment` (0.09) | PASS |
| AT-3 | `presence` (0.16) ≥ `novelty` (0.07) | PASS |
| AT-4 | `creation` (0.15) ≥ `humour` (0.05) | PASS |
| AT-5 | `continuity` (0.14) ≥ `logic` (0.03) | PASS |
| AT-6 | `safety` == 0.0 | PASS |
| AT-7 | env-var / config-file override changes output at runtime | PASS |
| AT-8 | `significance_diagnostics()` logs at DEBUG per scored turn | PASS |
| AT-9 | 13 vs 14 discrepancy documented in module docstring + weight block comment | PASS |

---

## Normalisation note

Source §BA-02 weights (verbatim) summed to 1.01: `efficiency` was 0.01. Adjusted `efficiency` to 0.00 to satisfy `sum == 1.00` invariant. Documented in weight block comment.

---

## Test run

`~/miniconda3/bin/python3 -m pytest tests/ -k "sp29 or SP29 or significance"` — **22 passed**.  
Full suite (excluding 5 known pre-existing ignores) — **1533 passed, 3 pre-existing failures**.

---

*Builder seat · 2026-09-05 · WO-SP29-WEIGHTS-001 · Closes BA-02*
