# 00_WO-096B — 🔴 **P0. WO-095 shipped and the learning loop does NOTHING.**

**WO:** WO-096B · **Seat:** builder · **Priority:** P0 — ahead of everything
**Reserved?** no · **Gate?** none
**Found by:** Architect implementation-readiness verification, 2026-08-13. All facts [VERIFIED] against HEAD.

## The situation
WO-095 (`0a202f0`) landed `self/lesson_store.py` (511 lines) and was marked DONE. The read path is real.
**But eLo still cannot learn anything, and the ledger has not moved.** 378 rows, **378 of them
`status: candidate`**, zero confirmed — three days after the WO closed. Four separate defects, each of
which alone would be fatal.

## Defect 1 — 🔴 nothing ever calls `promote_pass`. The loop has no engine.
[VERIFIED] `recall()` filters `status == "confirmed"` (`self/lesson_store.py:343`). The only thing that can
create a `confirmed` lesson is `promote_pass` (`:251-260`). **Grep: its only caller is
`tests/test_wo095_learning_loop.py`.** So `recall()` returns `[]` in production, forever, and the
`[LEARNED HEURISTICS]` block in `runtime/prompt_builder.py:299-314` is always empty.
**Fix:** call `promote_pass` from the real turn loop (end-of-turn or the continuation tick — your call,
state which you chose and why in the outbox).

## Defect 2 — 🔴 the promotion gate can never open, even once #1 is fixed
[VERIFIED] `lesson_store.py:264` requires `scope == "preference"` **and** non-null `proposes`.
The only writer, `runtime/reflection_faculty.py:83-87`, emits `scope` ∈ {`behaviour`, `capability`,
`relationship`} and `:111` sets `"proposes": None`. **The producer and the consumer disagree on the
contract.** Nothing can ever satisfy the gate.
**Fix:** reconcile the two. Do NOT just widen the gate to let everything through — decide which scopes are
promotable and what evidence each needs, and make the writer emit it. Say what you decided.

## Defect 3 — 🔴 the ACK hook writes to a lesson key that does not exist
[VERIFIED] `server.py:2652-2657` computes
`lesson_key("behaviour", "Sitting with David confirmed by body ACK.", "met")` → `c8d3d97e0f45b903`.
**That key appears ZERO times in the ledger** (the only key present is `99ae9fcf7d4231eb`). So
`record_outcome` returns `{}` and the evidence is silently discarded — **the one place a verified outcome
enters the system is a no-op.**
Worse: the 15 s timeout path (`server.py:2687-2692`) carries the **same dead key** with
`verified=True, contradicting=True` — so if the key were ever fixed without fixing this, **a timeout would
actively weaken the lesson.** Fix both together.
**Rule 1 alarm (mandatory):** `record_outcome` must **not** silently return `{}` on an unknown key. Log it,
or fail. This defect existed only because absent and broken looked identical.

## Defect 4 — 🔴 tests write into the real growth journal
[VERIFIED] `_append_metrics` (`lesson_store.py:496-497`) writes to the module-level `_METRICS` constant and
**ignores the `ledger_path` override the tests pass**. The 69 rows in `self/journals/growth_metrics.jsonl`
are test artifacts, not production runs. **Any metric read off that file today is fiction.**
**Fix:** honour the override; then quarantine or delete the polluted rows and say which you did.

## Also in scope — `migrate_pre_v1()` has no production caller
377 pre-v1 rows still sit in the live ledger; `self/lessons_ledger_pre_v1.jsonl` doesn't exist. Run it once
behind a guard, or wire it into startup.

## Test (without David)
- `promote_pass` runs in the real loop — assert the ledger gains a `confirmed` row from a seeded lesson
  with real evidence, **through the live path, not by calling the helper directly.**
- Producer/consumer contract test: a lesson written by `reflection_faculty` is **eligible** for promotion.
- `record_outcome` with an unknown key **raises or logs loudly** — assert the alarm, not silence.
- `_append_metrics` honours `ledger_path`; a test run leaves the real journal byte-identical.
- End-to-end: seeded verified outcome → promotion → `recall()` returns it → it appears in
  `[LEARNED HEURISTICS]` in the built prompt. **That chain is the actual Done bar.**

## Done when
All five green, committed, hash to outbox. **State in the outbox how many lessons reached `confirmed` on a
real run** — if the answer is zero, it is not done.
