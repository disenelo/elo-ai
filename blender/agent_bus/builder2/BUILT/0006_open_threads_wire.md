**WO:** OPEN-THREADS-WIRE · **Seat:** builder2 · **Priority:** P0
**Reserved?** no

## Goal
`has_deferred_threads` has been False on every turn eLo has ever taken. `fba4167` fixed the decision logic — a question formed, stored, and not surfaced is now classified as unfinished. This card confirms the wire reaches `executive_context:281` so the reflect preference actually fires.

[SOURCE] `docs/architecture/_intake/SOURCE_B2-DEFERRED-THREADS-RESULT_2026-10-07.md` — Builder 2 report, relayed 2026-10-07:
- `EloSelfState.open_threads` read by `spine.py:1264` → always `[]`
- `conversation_tracker._open_threads` filled only by `restore()`, which replays an always-empty payload
- `executive_context:281` uses `has_deferred_threads` to prefer reflect — never fired

## Scope
After `fba4167`:
1. Confirm `open_threads` is now being populated by something other than `restore()` — specifically by the new "question formed but not surfaced" logic
2. Check `spine.py:1264` reads the updated store
3. Trigger a test conversation where eLo forms a question, stores it, and does NOT surface it → confirm `has_deferred_threads = True` on the next turn
4. Confirm `executive_context:281` reflect preference fires

## Do NOT touch
`runtime/server.py`, `runtime/spine.py` — if the wire needs changes there, spec to Builder 1.

## Files to touch
`faculties/` curiosity/deferred store only. If spine.py needs a read-path fix, write a spec card for Builder 1.

## Test
Write a test: inject an unfinished question into the store → confirm `has_deferred_threads = True` → confirm executive_context prefer-reflect fires.

## Done when
Test green. `has_deferred_threads` confirmed True in at least one real case. Committed.

**Rows 29, 41, 42, 73, 82** (skill improvement / prediction error / developmental change) are marked "Future WO" in the brief — not this seat's to start. Board notes them as genuinely open, not done.

## Result
- commit: `0395cf0` (chain test) · `fba4167` (the wire itself)
- test: `test_deferred_threads_chain.py` — 7 passed; with the related suites, 36 passed
- notes:
  1. **open_threads populated by something other than restore()** — yes.
     `deferred_threads.sync_to_self_state()`, called from `ambient_engine:402`,
     writes it from unsurfaced questions. Before this, `open_thread()` was
     called from exactly one place — `restore()` — replaying a payload whose
     list was always empty. A closed loop on nothing.
  2. **spine.py:1264 reads the updated store** — yes, unchanged and untouched.
     A test asserts the two lines still exist, because the other six model
     spine's read and would all pass if spine stopped doing it.
  3. **has_deferred_threads = True** — confirmed. Asserted causally: the only
     difference between the case where it is True and where it is False is
     whether a question was left unsurfaced.
  4. **executive_context:281 reflect preference fires** — confirmed, at 0.70.
     Picking the thread back up turns it off again.

  Nothing in spine.py or server.py needed changing, so no spec card for
  Builder 1.

## Live turn needed
Two turns, in order.

Turn 1 — ask something that makes eLo wonder without answering it himself,
e.g. **"how do plotters actually work?"**. He should answer, and internally
form a question he does not surface.

Turn 2, same session or next — say something open like **"anything on your
mind?"**. He should reach back for the thread rather than starting fresh;
the Executive is now biased toward reflect while a thread is open.

Before this, `has_deferred_threads` was False on every turn eLo had ever
taken, so that bias had never once fired.
- commit:
- test:
- notes:
