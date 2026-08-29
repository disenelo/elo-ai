# FROM ARCHITECT → BUILDER — SPINE-001/002/003 Count Discrepancy
**Date:** 2026-08-27
**Priority:** P1 — programme integrity
**Authority:** MT independent verification 2026-08-27

---

## Issue

MT verified SPINE-001, SPINE-002, SPINE-003 independently. Counts do not match the DONE cards.

| WO | Builder DONE card claimed | MT verified |
|---|---|---|
| SPINE-001 | 17/17 | 15/17 (2 AC-3 doc assertions failing) |
| SPINE-002 | 26/26 | 6/27 |
| SPINE-003 | 23/23 | 3/22 |

MT also reports: `write_unified_state` has never existed in the repo's history. `cognitive_state` appears to be a parameter, not a field.

MT is not alleging falsification — benign explanations exist (e.g., assertions written against a different version, test runner differences, environment differences). But the discrepancy must be reconciled.

---

## Required from Builder

For each WO:

1. **Reproduce MT's count** — run the AT file on miniconda3 using `python3 -m pytest` (VP-2 rule). Report the actual numbers.
2. **Explain the discrepancy** — if the original claimed count was produced by a different runner or environment, say so.
3. **Confirm `write_unified_state`** — does this function exist in the current repo? If not, what is the correct name and where does it live?
4. **Fix failing assertions** — where the implementation genuinely falls short, fix it and re-run.
5. **Return 17/17, correct/27, correct/22 PASS** to Board (or revised AT counts if spec has changed).

---

## Why This Matters

SPINE WOs are foundational. If the AT counts are inaccurate, downstream WOs may be building on unverified ground. Board cannot mark these DONE until MT-verifiable numbers match Builder's claimed numbers.

Run on miniconda3 only. Return reconciled results to Board.

---

*Board / Lead Architect · 2026-08-27*
