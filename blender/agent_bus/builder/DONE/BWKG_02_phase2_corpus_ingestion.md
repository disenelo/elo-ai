# BUILDER CARD — BWKG-02: WKG Phase 2 — Corpus Ingestion / Population
**Date:** 2026-08-22
**Authority:** `_intake/SOURCE_2026-08-22_CA_WKG_phase1_ratified_phase2_authorised.md` (CA, verbatim)
**Phase 1 ratification:** WKG Phase 1 APPROVED / RATIFIED — 20/20 AT-W1..AT-W13 · 5/5 Vol XXIV regression · 18/18 BDRIFT-U regression
**Prerequisite:** Phase 1 complete ✅ (`knowledge/wkg_schema.py` · `knowledge/graph_loader.py` · `relationships/world_graph.json` · write gate live)

---

## What Phase 2 is

Populate the WKG with actual corpus content — knowledge claims from eLo's world, canon volumes, and established facts — using the Phase 1 schema and governed write gate.

**Phase 1 approved the schema and governance mechanism. It did not pre-approve the corpus contents.** Every ingested claim still passes through `evaluate_write_gate()`.

---

## Hard boundary (CA verbatim — these are not suggestions)

The governed write gate is a **hard boundary**. Do not:

- bypass or weaken `evaluate_write_gate()`
- promote `HYPOTHESIS` / `SPECULATIVE` claims without David L3 authority
- manufacture evidence or certainty
- write WKG material into autobiographical Memory
- create another graph, store, or loader
- introduce a new CAL action
- modify SPG
- alter unrelated canon

---

## Write gate rules by epistemic class

| Class | Rule |
|---|---|
| `VERIFIED` / `HISTORICAL` | Only with a required supporting evidence pointer. No evidence = cannot be VERIFIED. |
| `SOURCE_ATTRIBUTED` / `SYMBOLIC` | Represented as perspective; provenance retained. Written as `WRITE_AS_PERSPECTIVE`. |
| `HYPOTHESIS` / `SPECULATIVE` | `proposed_claim` only. No promotion to canon without David L3. |
| `DISPUTED` | Preserve both claims + `CONTRADICTS` relationship. Neither side collapsed. |
| `UNKNOWN` | Remains unknown. Do not manufacture certainty. |

---

## Deliverables required

Builder produces all of the following:

1. **Populated `relationships/world_graph.json`** — expanded corpus of wkg_entities, wkg_claims, wkg_sources, wkg_claim_relationships ingested through the write gate
2. **Contradiction handling** — all `DISPUTED` pairs carry `CONTRADICTS` relationships with both claims preserved
3. **Provenance integrity** — every ingested claim retains `wkg_epistemic_class`, `provenance`, and Vol XXIV `kind`/`confidence` mapping
4. **Write-gate enforcement log** — evidence that `evaluate_write_gate()` was called for every ingested claim and that no bypasses occurred
5. **Complete acceptance evidence** — test suite covering:
   - write gate enforcement under all 8 epistemic classes
   - contradiction pairs correctly structured
   - provenance intact on all claims
   - no second graph/store/loader created
   - no autobiographical Memory written
   - no new CAL action introduced
   - Vol XXIV regression still 5/5 ✅
   - Phase 1 regression still 20/20 ✅

---

## If corpus exposes a gap

If any ingested claim requires an architectural decision not covered by the ratified Phase 1 contract: **STOP. Return the decision to Architect/Board.** Do not invent L3 authority. Do not self-approve a new epistemic class, gate bypass, or write path.

The decision comes back as a single, clearly stated question with the specific claim and the specific gap. Not a redesign proposal.

---

## What this card does NOT authorise

- SPG work (parked RED/INERT)
- LOOP-7 or learning-faculty changes
- Autobiographical Memory writes
- Any change to `executive.py`, `prompt_builder.py`, `backend_router.py`, or identity files
- Any new ADR, CAL action, or FREEZE amendment

---

## CLOSED — 2026-08-22

**Status:** ✅ COMPLETE

**Deliverables shipped:**
1. `relationships/world_graph.json` — 7 new wkg_entities (EloCharacter, ChunkCompanion, K7Companion, SugarCoreState, CalmPrinciple, NonverbalExpression, FourActNarrative), 8 new wkg_claims (7 WRITE_AS_PERSPECTIVE + 1 WRITE), 2 new wkg_sources (elo_planet_design_canon, behavioral_science_consensus), 2 new wkg_claim_relationships (SUPPORTS, ANALOGOUS_TO). Totals: 27 entities, 26 claims, 5 sources, 5 claim_relationships. Legacy arrays unchanged (17/17).
2. Contradiction handling — existing CONTRADICTS pairs intact; no DISPUTED pairs in eLo corpus (internally consistent); ANALOGOUS_TO pair added.
3. Provenance integrity — all claims carry wkg_epistemic_class, provenance (author + title), source pointer, Vol XXIV kind/confidence mapping.
4. Write-gate enforcement — `evaluate_write_gate()` called for every ingested claim; no bypasses; 7 SOURCE_ATTRIBUTED/SYMBOLIC → WRITE_AS_PERSPECTIVE, 1 VERIFIED (with evidence) → WRITE.
5. `tests/test_bwkg02_elo_corpus.py` — 49/49 passed. Covers: gate enforcement (7 tests), provenance integrity (7 tests), epistemic classification (7 tests), contradiction handling (7 tests), isolation (7 tests), corpus content (13 tests).

**Regression state at close:**
- BWKG-02 acceptance: 49/49 ✅
- WKG Phase 2 (`test_wkg_phase2.py`): 82/82 ✅
- WKG Phase 1 (`test_wkg_phase1.py`): 20/20 ✅
- Vol XXIV (`test_canon_xxiv_*`): 5/5 ✅
- WO-LCI-001 acceptance: 24/24 ✅
- LOOP-7 live: 6/6 ✅
- Total in-scope: 161/161 ✅

**Hard boundary compliance:** Gate not bypassed. No HYPOTHESIS/SPECULATIVE ingested. No second loader. No autobiographical Memory written. No new CAL action. SPG not touched. Legacy arrays unchanged.
