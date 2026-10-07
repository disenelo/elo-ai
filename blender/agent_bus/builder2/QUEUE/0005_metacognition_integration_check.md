**WO:** METACOGNITION-INTEGRATION-CHECK · **Seat:** builder2 · **Priority:** P1
**Reserved?** no

## Goal
WO-METACOGNITION-001 (commit 85cc8bf) and WO-UNLEARN-001 were built. Confirm self-improvement faculties are actually wired into live turns — not just built as standalone modules.

## Scope
1. Read `faculties/metacognition/` — find the entry point
2. Find where it is called from `server.py` or `spine.py` (if it isn't, that's the gap)
3. Confirm `self_improvement/` is triggered after each turn (or on the scheduled window)
4. Check `correction_store.py` — is it accumulating corrections from real turns?
5. Run existing metacognition tests

If NOT wired into live turns: spec the wire to Builder 1 (B2 does not touch server.py). File `FROM_BUILDER2_METACOGNITION-WIRE-SPEC_<date>.md` for Builder 1's queue.

## Files to touch
`faculties/metacognition/` (read) · `self_improvement/` (read) — audit only

## Done when
Wiring confirmed (or gap specced to B1). Test pass result recorded.

## Result
- commit:
- test:
- notes:
