**WO:** SPG-LIVE-SCORING · **Seat:** builder2 · **Priority:** P1
**Reserved?** no

## Goal
Every new conversation turn adds significance data to the SPG. Backfill is done (3,309 turns). Live scoring is not active.

## Scope
Wire `faculties/spg/spg_faculty.py` to score each new turn as it completes. Per turn:
- Call `score_turn(turn_data)` (or equivalent)
- Append new signal to `data/spg_signals.jsonl`
- Update pattern nodes in `data/spg_graph.json` incrementally

The hook point is wherever turns are finalised — check if there's an existing post-turn hook in your faculty chain. If not, add one.

## Files
`faculties/spg/spg_faculty.py` · wherever turn completion is signalled in your lane

## Test
`python3 tests/test_spg_*.py` — existing pass. Add: mock a single turn → `spg_signals.jsonl` has one new entry.

## Done when
implemented + test green + committed.

## Result
- commit:
- test:
- notes:
