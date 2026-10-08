**WO:** SPG-BACKFILL · **Seat:** builder2 · **Priority:** P0
**Reserved?** no

## Goal
4+ months of conversation data in interactions.json processed into SPG significance patterns. Currently SPG has no historical signal — ROOT-4.

## What exists
`interactions.json` (gitignored, always present) — full history of David's messages and eLo's responses.
Builder 1 is processing the same file into WKG (facts/knowledge). Coordinate: Builder 2 takes significance patterns — emotional weight, repetition, corrections, escalations, topics David returns to.

## Scope — exactly this, nothing more
- Read interactions.json
- For each exchange: score significance using existing SPG scoring logic
- Write SPG records for high-significance turns
- Do not duplicate what Builder 1 is writing into WKG
- Date-range coordination: process full history, deduplication by turn ID

## Files to touch
`faculties/spg/` (all) · `interactions.json` (read only)

## Test
`python3 -m pytest tests/ -k "spg" -v`
After backfill: SPG should contain patterns. Query for David's most repeated topics.

## Done when
SPG populated from historical data. Significance patterns queryable. Test green. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David says to eLo: "What topics do I keep coming back to?"
> eLo should reference SPG-derived patterns from the actual history.

## Result
- commit: `d5aab22` · `efe3cd3` · `f79d868`
- test: `pytest -k spg` — 158 passed
- notes: **DUPLICATE RE-FILE.** This card was completed and moved to
  `BUILT/0004_spg_interactions_backfill.md` at 2026-10-07 ~13:56, before the
  Board's "0004 disappeared from queue" note was written — it had not
  disappeared, it was in BUILT. The BUILT copy carries the full result and the
  live turn. Nothing re-run; this copy is reconciled, not rebuilt.
  Range: 2026-06-06 → 2026-10-06, 3,324 entries. Graph 3,330 → 3,333 nodes,
  9 live claim-keyed nodes preserved.
