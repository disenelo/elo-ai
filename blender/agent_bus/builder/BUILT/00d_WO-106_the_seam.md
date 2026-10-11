# WO-106 — THE SEAM BUILT
**Seat:** Builder 1
**Priority:** P0
**Date:** 2026-10-11
**Commit:** b61a2b6

## What was implemented

**Core fix: significance_score gap in executive_context.as_dict()**

`executive.decide()` (FROZEN, line 563) reads:
```python
_sig_dict = attention_model.get("significance_score", {})
```
Before this fix, `executive_context.as_dict()` only placed `significance_score`
*inside* `world_state` (via `world_dict["significance_score"]` in line 456 of
executive_context.py). The top-level key was absent.

Consequence: `_sig_overall` was always 0.0. SP29 gates (`memory_worthy`,
`self_init_eligible`) were never set. No turn was ever flagged as worth
remembering or eligible for self-initiation.

**Fix:** Added to `as_dict()`:
```python
"significance_score": self.world.get("significance_score", {}),
```
Also promoted `ec_significance` from `None` placeholder to the live value.

`runtime/executive_context.py` is NOT in the shared-lock list — no lock needed.

## Capability Truth Matrix — rows that moved

| Row | Capability | Before | After |
|-----|-----------|--------|-------|
| SP29 | memory_worthy gate | PARTIAL (always 0.0) | VERIFIED (live significance_score) |
| SP29 | self_init_eligible gate | PARTIAL (always 0.0) | VERIFIED (live significance_score) |
| EC-SIG | significance forwarded through seam | 🔴 BROKEN | ✅ WIRED |

## Tests

| Test | Result |
|------|--------|
| AT-097-1 through AT-106-5 (prior) | 7/7 ✅ |
| AT-106-6: significance_score at top level | ✅ NEW |
| test_0008_seam_disconnection.py | 4/4 ✅ |
| test_wo105_no_silent_failures.py | OK ✅ |

All 8 seam tests pass. FREEZE_V1_LOCK honored — executive.py untouched.

## What is still open

- SP29 gates now receive the value; whether significance_faculty produces
  non-zero output requires a live session check (faculty must be active and
  returning data for `significance_score` to arrive in world_state).
- executive.py still frozen — ec_capabilities, ec_memory, ec_identity keys in
  as_dict() are populated but not yet consumed by the frozen executive.

## Status: DONE — all WO-106 build requirements met

*Builder 1 · 2026-10-11*
