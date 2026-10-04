# WO-095 Learning Loop — Close the Read Side — Result Card

**Builder:** Builder 1
**Date:** 2026-10-05
**Status:** COMPLETE — 10/10 ATs pass (2 failing fixed this session)

---

## What was fixed

`memory/significance_engine.py` line 257:
- `evaluate(outcome=None)` was setting `scores["reward"] = 0.0` in the no-outcome branch
- Spec (AT-3, AT-6) requires `"reward" not in scores` when no outcome supplied — back-compat with pre-WO-095 9+overall key shape
- Fix: removed `scores["reward"] = 0.0` from the `else` (no-outcome) block
- With an outcome supplied, `reward` key is still correctly present and non-zero for verified ACKs

## What was verified

`self/lesson_store.py` + `memory/significance_engine.py`:
- Lesson promotes on 3 verified episodes / 2 sessions → confirmed status
- 2 eps / 1 session → stays candidate (threshold correct)
- Confirmed lesson appears in CognitiveSnapshot.lessons + prompt; ≤3/≤240-char bound enforced
- Verified ACK → reward>0; unverified outcome → reward≤0.30 (significance only)
- No outcome → no reward key (9+overall key shape preserved)
- Promote path writes nothing to identity (kernel hash, vault bytes, exec/prompts intact)
- Repeat episodes strengthen existing row; no duplicate appended
- `significance_engine.evaluate()` back-compat: same 9+overall keys, same range
- `stats()` counts update on promotion; reinforcement_ratio > 0; alarm flag present
- `promote_pass` not in significance_engine/prompt_builder (clean separation)
- `journal_router` · `significance_faculty` · `reflection_faculty` compile clean
- Pre-v1 rows archived cleanly; v1 ledger untouched; idempotent

## ATs

- AT-1 ✅ lesson promotes on 3 verified eps / 2 sessions
- AT-2 ✅ confirmed lesson in recall + prompt; ≤3/≤240-char bound
- AT-3 ✅ (FIXED) verified ACK → reward>0; unverified → reward≤0.30; no outcome → no reward key
- AT-4 ✅ learning writes nothing to identity
- AT-5 ✅ repeat episodes strengthen existing row; no duplicate
- AT-6 ✅ (FIXED) significance_engine.evaluate() back-compat — no outcome → same 9+overall keys
- AT-7 ✅ stats() counts; reinforcement_ratio > 0; alarm field present
- AT-8 ✅ promote_pass not in significance_engine/prompt_builder; all files compile clean
- AT-9 ✅ journal_router + significance_faculty + reflection_faculty compile clean
- AT-10 ✅ pre-v1 migration clean; v1 ledger untouched; idempotent

**Run:** `python3 tests/test_wo095_learning_loop.py` → **10/10 passed**

## Files changed

- `memory/significance_engine.py`: removed `scores["reward"] = 0.0` from no-outcome `else` branch
