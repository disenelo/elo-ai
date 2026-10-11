# Board Review — WO-096B: Fix the inert learning loop
**Date:** 2026-10-11
**Builder:** Builder 1
**Commits:** f94c6a2 (all 4 defects) · f0c99f3 (SPOT episode_ref) · c93dab8 (batch corrections)
**Status:** READY FOR BOARD REVIEW

## Summary

All 4 defects from the Architect's 2026-08-13 audit fixed:

**Defect 1 — promote_pass never called in production:**
`_maybe_run_promote_pass()` called at end of every turn (every `_PROMOTE_INTERVAL=10` turns)
in server.py lines 9620 + 9688. Runs in a daemon thread — never blocks a response.

**Defect 2 — promotion gate can never open:**
`ensure_lesson()` and `record_outcome()` now use scope `"behaviour"` — which `promote_pass`
accepts. `reflection_faculty.py` scopes reconciled so that lessons it writes ARE eligible
for promotion. `_try_personality_delta` gate still requires `scope=="preference"` (unchanged
— personality evolution is stricter than promotion).

**Defect 3 — ACK hook writes to a non-existent lesson key:**
`server.py:5329-5343` now calls `ensure_lesson("behaviour", _SIT_STMT, "met")` before
`record_outcome()`. The row is guaranteed to exist before evidence is recorded.
`record_outcome` now warns loudly on unknown key instead of returning `{}` silently.

**Defect 4 — tests write to real growth journal:**
`_append_metrics` honours `ledger_path` override — when a temp ledger path is given
(test runs), metrics go beside it, not into the real journal. 69 polluted rows quarantined
via `migrate_pre_v1()`.

## AT Results

| Suite | Result |
|---|---|
| `test_wo096b_learning_loop_live.py` | ✅ 6/6 PASS |
| `test_wo095_learning_loop.py` | ✅ 10/10 PASS |
| `test_learning_loop_leak.py` | ✅ 16/16 PASS |
| `test_d3_lesson_reaches_executive.py` | ✅ 7/7 PASS |

Board to formally close.

*Builder 1 · 2026-10-11*
