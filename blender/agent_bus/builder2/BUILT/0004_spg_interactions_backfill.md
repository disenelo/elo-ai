**WO:** SPG-INTERACTIONS-BACKFILL · **Seat:** builder2 · **Priority:** P0
**Reserved?** no

## Goal
4+ months of full conversation data sits in `interactions.json` (gitignored, always present). It contains David's messages AND eLo's responses. Feed it through the SPG significance pipeline to build pattern history from real data.

[CLAUDE.md 2026-10-06] "Contains both David's messages and eLo's responses. Builder 2 processes into SPG (significance patterns). Coordinate on date ranges to avoid duplication with Builder 1's WKG processing."

## Scope
1. Read `interactions.json` — understand the record format
2. Determine which entries have already been processed (check SPG store for existing entries — avoid double-processing)
3. Batch-process unprocessed entries through `faculties/spg/` significance scorer
4. Write pattern results to SPG graph store
5. Report: number of entries processed, date range covered, top significance patterns found

## Coordinate with Builder 1
Builder 1 processes `interactions.json` → WKG (knowledge nodes). Use date range markers to avoid overlap:
- Check if Builder 1 has a processed-up-to cursor; use the same or adjacent range
- File `FROM_BUILDER2_SPG-BACKFILL-DATE-RANGE_<date>.md` to board_review with the range you processed

## Files to touch
`faculties/spg/` (write) · `interactions.json` (read only)

## Test
After processing: `python3 -m pytest tests/ -k "spg"` — confirm existing SPG tests still pass

## Done when
All unprocessed entries scored + written + test green + date range filed. Commit in Result.

## Result
- commit: `d5aab22` (incremental path + range report) · `efe3cd3` (original backfill)
- test: `pytest -k spg` — **158 passed**
- notes:
  - Live graph: **3,330 → 3,333 nodes, 13,203 → 13,210 edges**. Full history
    was already loaded by `efe3cd3`; this run added the 3 turns since.
  - **Double-processing was a real hazard, not a formality.** `build()`
    constructs a FRESH graph, so re-running it would have discarded the 9
    live claim-keyed nodes written by `record_claim` since the first pass —
    silently. `update()` adds instead, and verifies those 9 survive.
  - Range filed: `board_review/FROM_BUILDER2_SPG-BACKFILL-DATE-RANGE_2026-10-07.md`
    — 2026-06-06 → 2026-10-06, all 3,324 entries.
  - **No range split needed with Builder 1.** SPG writes `data/spg_graph.json`,
    WKG writes `memory/wkg/*`. Disjoint stores, both can read the same file.
  - Top patterns: robot 243 · ping 153 · working 139 · today 100 ·
    building 86 · game 79 · world 77 · planet 77.
  - **Warning passed to Builder 1:** 1,076 of 3,324 `user` fields are the
    assembled prompt, not David — a `[WORLD_KNOWLEDGE ...]` block with his
    words after "User asked:". Scored raw, the top patterns come back as
    *world, asked, user, answer, knowledge, confidence, verified* — the graph
    measuring its own scaffolding. Stripped before scoring here; WKG will hit
    the same thing reading the same file.

## Live turn needed
Say to eLo: **"what do I keep coming back to?"**

Expect him to name his own recurring threads — the robot, the game, eLo-Planet,
building and testing — rather than generic topics or a list read off a prompt.
Before this card the graph held 3 nodes and 0 edges, so he had nothing to
answer from.

Weaker but faster check: **"what have we been working on for the last few
months?"** — the span should reach back to June, not just this session.
