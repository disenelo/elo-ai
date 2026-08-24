# FROM ARCHITECT — 2026-08-21 — `SPG-001` Semantic Point Graph V1

**Card:** `engineering/work_orders/WO-SPG-001_Semantic_Point_Graph_V1.md`
**Spec:** `docs/architecture/SEMANTIC_POINT_GRAPH_v1.md`
**PRIMARY SOURCE — read this first, it is verbatim:**
`docs/architecture/_intake/SOURCE_2026-08-21_DAVID_semantic_point_graph.md`

## Start now, no authorisation needed (read-only)

**Step 1** — resolve **30 core point addresses** onto nodes that already exist: the 17 entities in
`relationships/world_graph.json` + 13 of the 16 concepts in `relationships/concepts.json`. Band them per the
spec §1.1. **Report the 30 ids + `canonical_ref`s before writing anything.** `identity/world_graph.json` is
RETIRED (Vol XXIV §1.6 Ruling A) — do not read it.

**Step 2** — settle two UNKNOWNs, D3-option-A style, before any write:
- **U-1** `memory/embedding_cache.json` is 42 bytes (empty) and `embedding_store.search()` never flushes.
  Does `warm()` persist 30 point texts at boot? **What happens with no `OPENAI_API_KEY`?** The design must
  degrade to keyword resolution and still pass AT-1..AT-7. Report which path is live.
- **U-2** does `runtime/capabilities/genome.py::_validate_genome`'s `_CONSTITUTIONAL_TERMS` gate reject a
  genome whose `purpose` mentions memory or learning? Word it as *retrieval + salience* and report.

**UNKNOWN stays UNKNOWN** until evidence settles it or David rules. Do not assume either.

## Steps 3–10 need one line from David

`ADR-Exec-008 §4` says *"no new Faculty… no implementation authorised."* David's directive is later material
asking for exactly this. The one-line lift is in
`docs/architecture/RULING_BRIEF_2026-08-21_semantic_point_graph.md` §1. **He is the only person who can
write it, and he is present.** If it is already there when you read this, build straight through.

## The five things I will reject on sight

1. **A second store.** Points are addresses onto existing canonical nodes. The overlay carries salience and
   provenance only — **delete it and nothing true is lost** (AT-11). Vol XXIV §1.1.1 · `LEARNING_LOOP_v1` §2.
2. **A weight moved by text.** Co-occurrence proposes at `strength 0.0 / status: unverified`, excluded from
   retrieval scoring. Only a verified ACK'd `OutcomeRecord`, in the integration window, in
   `faculties/learning/`, moves a strength. `ADR-Exec-005` D1/D2/D6.
3. **A second co-occurrence pass.** `core/memory_engine._build_concept_pairs()` (L722) already exists — it
   becomes the candidate proposer. Same for `world/world_state.update_world_state()` (the reinforcement
   shape), `self/lesson_store.py` (the ±0.15 / −0.20 / −0.02 constants — **copy, do not invent**),
   `core/visual_memory._layout()` (the relaxation loop), and
   `memory/obsidian_loader._extract_links()` (already-parsed `[[wikilinks]]`, currently untraversed).
4. **A parallel retrieval injector.** Extend `knowledge/graph_loader.retrieve()` / `build_context()`.
   Do not import the faculty from `core/kernel.py` — the kernel calls no engines.
5. **A `why` written after the fact.** It is assembled *during* the traversal from the edges actually walked.
   Model-generated → RED (AT-10, `CT4V-08`).

## Frozen surfaces — AT-12 asserts you did not touch them

`prompts/` · the 9 CAL actions · the 5 voice tones · attention's intent/valence/momentum + HIGH/MEDIUM/LOW
tiers · `relationships/world_graph.json` entity count (**zero new entities in V1**) · `runtime/executive.py`
beyond the one 2026-08-21 keyhole (asking the Learning Faculty — do not widen it) · the visualiser
(`brain_state.json` gets **nothing** from this card; that is a separate later WO).

## Report back

Step 1's 30 ids · U-1 and U-2 as VERIFIED or UNKNOWN · AT-13's **measured** latency (it replaces my
`≤20 ms` ESTIMATE) · and **AT-7 with both halves proven**: the graph retrieves a memory sharing no content
word with the query, **and** `vault_layer.lookup()` misses that same query. That one test is the whole idea —
if it goes green at 30 points, 300 is engineering.

Finished things and blockers only. No `written` / `scaffolded` / `partial` (Rule 4j).
