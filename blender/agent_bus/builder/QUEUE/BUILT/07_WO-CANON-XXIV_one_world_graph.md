# 07_WO-CANON-XXIV_one_world_graph.md

**WO:** WO-CANON-XXIV · **Seat:** builder · **Priority:** P2 · **Reserved?** no
**Ruling A CLOSED 2026-08-10** — no longer gated.

## Goal
One world graph, not two. Knowledge carries confidence + evidence so eLo qualifies rather than asserts.

## Scope — exactly this (Ruling A)
1. **`relationships/world_graph.json` is CANONICAL** (it's what `knowledge/graph_loader.py` actually reads).
   Migrate anything unique out of `identity/world_graph.json`, then **retire** it. No second ontology.
2. Add **`confidence`** + epistemic **`kind`** + **`evidence[]`** to the knowledge retrieval contract
   (`strength` is salience, NOT confidence — keep them separate).
3. Ranked retrieval instead of the naive keyword match returning a flat string.
4. **Never backfill the graph's silence with the base LLM's general world-knowledge** (Verified Speech).

## Files likely touched
`knowledge/graph_loader.py` · `relationships/world_graph.json` · `identity/world_graph.json` (retire)

## Test (without David)
Assert one canonical graph path; assert retrieval returns ranked results carrying confidence + evidence;
assert an unknown fact yields "I don't have that" rather than an LLM-invented answer.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
Canon: `docs/architecture/Volume_XXIV/` · Ruling: `docs/architecture/CANON_RULINGS_2026-08-10.md`

## Result
- commit: 964228c
- test: 5/5 AT (canonical path, ranked retrieve() with confidence+kind+evidence, no backfill, identity/ retired, continuity wired)
