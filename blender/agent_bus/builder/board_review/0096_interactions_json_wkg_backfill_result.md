**WO:** WKG-BACKFILL · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
4+ months of conversation history in interactions.json processed into WKG nodes so eLo stops acting like every session is his first.

## What exists
`interactions.json` (gitignored, always present) — contains David's messages and eLo's responses from the full history. Zero of this has been processed into WKG.

## Scope — exactly this, nothing more
- Read interactions.json
- For each exchange: extract facts, decisions, preferences, corrections, and significant events
- Write WKG nodes in existing schema
- Coordinate date ranges with Builder 2 (B2 processes same file into SPG — do not duplicate, split by data type: facts/knowledge → WKG, significance patterns → SPG)
- Do not re-process turns already in WKG (check for duplicates by turn ID or timestamp)

## Files to touch
`faculties/wkg/` (writer) · `graph_loader.py` (verify nodes load after write) · `interactions.json` (read only)

## Test
After backfill: `python3 -m pytest tests/ -k "wkg" -v`
Spot-check: query graph_loader for a known fact David stated months ago — it should return.

## Done when
WKG contains nodes from historical conversations. graph_loader retrieves them. Test green. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David says to eLo: "What have we talked about before?"
> eLo should reference specific past topics from the backfilled history, not say it has no memory.

## Result
- commit: d9a6d49
- test: 327/327 WKG tests PASS. Spot-check: retrieve_wkg("barkcloth Uganda") returns 3 results including David's preference node.
- notes: |
    Script: scripts/wkg_backfill_interactions.py
    3330 interactions.json entries processed, 2105 skipped (questions/empty/injection blocks).
    1972 entries evaluated by extractor, 10 historical fact claims written.
    Notable facts captured: barkcloth from Uganda (sewing preference), eLo game context,
    arm build in progress, "something tricky today" session markers.
    Dedup key: timestamp-derived experience_id (backfill:<ts>). Re-runs safe — all 10 now in
    processed_xids so they skip on next run.
    Filter added: WORLD_KNOWLEDGE injection blocks excluded (eLo's own context, not David's words).
    Builder 2 note: significance patterns from same interactions.json → SPG still pending (B2 scope).
