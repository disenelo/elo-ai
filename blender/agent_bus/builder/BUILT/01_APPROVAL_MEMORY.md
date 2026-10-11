# 01_APPROVAL_MEMORY.md

**WO:** WO-APPROVAL-MEMORY · **Seat:** builder · **Priority:** P0 · **Reserved?** no

## Goal
David's approvals STICK. Right now he approves a WO and it re-appears as "still need David" forever —
because `continuation.py` recomputes `needs_david` from tier every run with NO memory of approvals.
This is the single most infuriating bug in the system for him.

## Scope — exactly this
- Read `engineering/work_orders/DAVID_APPROVED.md` (dated, append-only ledger of approved WO IDs).
- In the `needs_david` computation: **exclude every WO listed there.**
- Flip those board rows to `DONE ✅ David-approved` (same mechanism as `auto_close`, keyed off the ledger).
- Result: once approved, a WO closes and NEVER re-surfaces.

## Files likely touched
`company_runtime/continuation.py` · maybe `company_runtime/wo_test_runner.py`

## Test (without David)
New test: a WO present in `DAVID_APPROVED.md` does NOT appear in `needs_david`, and its board row reads DONE.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.

## Result
- commit: c157d36
- test: 5/5 AT (approved excluded from needs_david, board flipped DONE, no-test-file path, idempotent, parse formats)
