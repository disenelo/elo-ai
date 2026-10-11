# WO-B2-0007 — SPG Backfill + Dream Scorer Fix
**Seat:** Builder 2  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## Item A: SPG Backfill

`interactions.json` contains 4+ months of David's conversation data. Process it into SPG significance nodes. Coordinate with Builder 1 on date ranges to avoid WKG duplication. David needs SPG patterns active and retrievable during the demo.

File to Board: how many nodes processed, sample nodes from the backfill, confirmation it's live.

## Item B: Dream Scorer — Fix Saturation

All 10 retained dreams score exactly 0.900. All three scorer terms saturate at 1.0 regardless of content. This is as useless as a constant. Redesign the scorer:
- Scores must be differentiated (range across the 10 retained dreams should span at least 0.3)
- Scores must reflect actual dream content quality variation
- File corrected scores for first 10 retained dreams to Board

## Item C: Dream Symbol Selection

All dreams themed "Moon" regardless of topic. Fix symbol selection to derive from actual dream content.

## Acceptance

Board sees: SPG node count, dream score spread (not flat 0.900), symbol variety across retained dreams.
