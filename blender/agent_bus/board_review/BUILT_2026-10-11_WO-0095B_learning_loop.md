# Board Review — WO-095: Learning Loop (Read Side)
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Build the missing **read side** of the learning loop:
- `self/lesson_store.py` (NEW) — reader with `record_outcome()`, `promote_pass()`, `recall()`, `stats()`
- Dedup via `sha1(scope|statement|cause)` — fixes the 374-duplicate-row bug
- `OutcomeRecord` emitted at `server.py` ACK points (`sit_complete`, `move_complete`, `exit_complete`)
- `significance_engine.evaluate()` gains optional `outcome=` param (back-compat)
- `cognitive_snapshot.build_snapshot()` gains `lessons` (≤3, ≤240 chars)
- `prompt_builder.py` bounded hint block injected
- Pre-v1 ledger rows archived to `lessons_ledger_pre_v1.jsonl`

---

## Implementation status

Already landed. Per card Result section:
- **commit:** `0a202f0`
- **tests:** 10/10 AT green (promote on evidence, snapshot read-through, reward ACK-vs-unverified,
  identity isolation, dedup, back-compat, stats, response-path gate, regression, pre-v1 migration)

---

## Tests — `tests/test_wo095_learning_loop.py`

| # | Test | Result |
|---|------|--------|
| AT-1 | Promotes on 3 verified / 2 sessions; stays candidate otherwise | ✅ |
| AT-2 | Confirmed lesson appears in CognitiveSnapshot.lessons + built prompt; ≤3 / ≤240 | ✅ |
| AT-3 | ack_received vs timeout → different rewards; unverified → zero learning update | ✅ |
| AT-4 | No identity write; kernel hash unchanged; over-MAX_STEP/floor-breaching rejected | ✅ |
| AT-5 | Repeat strengthens; no duplicate row | ✅ |
| AT-6 | Contradiction demotes/retires; nothing deleted | ✅ |
| AT-7 | stats() moves correctly; identity_stability rise = alarm | ✅ |
| AT-8 | Dream reinforce +1 once; no-op on unknown SPOT; never creates | ✅ |
| AT-9 | promote_pass() never in the response path | ✅ |
| AT-10 | journal_router + significance_faculty regression clean | ✅ |

---

## Board decisions required

None. FREEZE_V1_LOCK files untouched. No new commit needed.

*Builder 1 · 2026-10-11*
