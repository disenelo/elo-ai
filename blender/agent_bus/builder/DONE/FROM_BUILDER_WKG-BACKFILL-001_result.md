# FROM_BUILDER — WKG-BACKFILL-001 RESULT

**WO:** WKG-BACKFILL-001  
**Seat:** Builder  
**Status:** CLOSED ✅  
**Date:** 2026-09-07  

## Summary

Full WKG backfill complete across two tasks.

## Task 1 — Historical interactions (944 turns)

- Interactions processed: 944
- Claims written: 508
- Entities created: 13
- Categories matched: 407 interactions

## Task 2 — Obsidian vault + profile cache extraction

- Obsidian entities extracted: 12 named entities + 10 domain concepts
- Profile active_projects extracted: elo-planet, elo-robot, plushies
- Core brand entities created: David Charles, eLo, Chunk, K-7, Core, Sugarcore, disenelo_universe
- Claims written this pass: 8
- Entity types used: PERSON (David Charles), CONCEPT (all others)

## Final state

| Metric | Before | After |
|--------|--------|-------|
| Entities | 2 | 37 |
| Claims | 3 | 516 |

## Top 10 entities

David Charles, eLo, Chunk, K-7, Core, Sugarcore, disenelo_universe, elo-planet, elo-robot, plushies

## AT verification

- ✅ wkg/entities.json contains David Charles, eLo, Chunk, K-7, Core, Sugarcore, disenelo_universe, elo-planet, elo-robot
- ✅ At least 5 more real named entities present (37 total)
- ✅ All entity types valid (PERSON / CONCEPT only)
