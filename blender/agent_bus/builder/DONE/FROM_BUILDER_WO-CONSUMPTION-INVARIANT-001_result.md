# FROM BUILDER — WO-CONSUMPTION-INVARIANT-001 RESULT

**Work Order:** WO-CONSUMPTION-INVARIANT-001 — Consumption Invariant Test
**Date:** 2026-08-31
**Seat:** eLo OS Builder
**Status:** DONE ✅

---

## Acceptance Tests

| # | Description | Result |
|---|---|---|
| AT-1 | `tests/test_consumption_invariant.py` exists | PASS ✅ |
| AT-2 | Arm A (full context) response ≠ Arm B (minimal context) response — consumption invariant proven | PASS ✅ |
| AT-3 | Arm A response contains evidence of consuming assembled fields (significance HIGH, companion, EXPLORE mode) | PASS ✅ |
| AT-4 | Test is read-only — does not mutate disk state | PASS ✅ |
| AT-5 | Mock backend stable across both arms (no flakiness) | PASS ✅ |

**All 5 tests green.** Test file: `tests/test_consumption_invariant.py`

---

## Files Created / Modified

| File | Action |
|---|---|
| `tests/test_consumption_invariant.py` | CREATED — two-arm consumption invariant test; Arm A: significance HIGH + TRUSTED_COMPANION + EXPLORE mode; Arm B: defaults only; asserts `response_A != response_B` and that Arm A contains assembled field evidence |

---

## Architecture Notes

- The CONSUMPTION GAP identified in source: "Assembled ≠ Used." This test proves assembled context changes decisions, not just populates world_dict.
- Two-arm design: same question, different world_dict. Responses must diverge — if identical, the context is assembly theatre.
- Arm A evidence checks: significance HIGH → response should not be terse; TRUSTED_COMPANION → not formal/distanced; EXPLORE mode → not closing down options.
- Test uses MockBackend to ensure LLM calls are controlled (no external API dependency).
