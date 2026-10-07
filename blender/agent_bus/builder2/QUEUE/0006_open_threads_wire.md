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
- commit:
- test:
- notes:
