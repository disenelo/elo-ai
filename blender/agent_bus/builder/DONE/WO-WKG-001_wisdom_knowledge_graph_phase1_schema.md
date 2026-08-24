# WO-WKG-001 — Wisdom Knowledge Graph Phase 1 Schema
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — AUTHORISED 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** MEDIUM — not blocking Stage 2 R&D Waves 1–5  
**Programme:** WKG — separate track from Stage 2 R&D implementation queue  
**RTR:** RTR-034, RTR-035, RTR-036, RTR-037

---

## Context

The Wisdom Knowledge Graph is eLo's long-term knowledge architecture. It is the terminal store for the Experience DNA propagation chain:

```
spine.py → experience_id minted
→ Meaning Object
→ all faculties
→ Executive → capability → body → ACK
→ consequence consumers (autobiography, lesson_store, route_memory, ExecutionReport)
→ MemoryFaculty.submit() (sole writer)
→ vault_layer (event store) + lessons_ledger (lesson store)
→ WKG ← Phase 1 builds this terminus
```

WKG Phase 1 establishes the schema foundation. It does not build the knowledge corpus yet — that is Phases 2+. Without Phase 1, the experience chain has no long-term knowledge terminus, significance queries have no history to draw on, and cultural context cannot be stored.

**Source:** `_intake/SOURCE_2026-08-22_DAVID_wisdom_knowledge_graph_spec.md` (David L3, verbatim)

---

## Deliverables

### D-1 — Entity model
A canonical entity schema with at minimum:
- `entity_id` — stable UUID
- `entity_type` — e.g. PERSON, CONCEPT, PLACE, SYMBOLIC, CULTURAL, NUMERICAL, ASTRONOMICAL, BIOLOGICAL
- `label` — canonical name
- `aliases` — list of alternative names/spellings
- `description` — short plain-language description
- `created_at` — timestamp
- `source_ids` — list of source IDs that established this entity

### D-2 — Epistemic class system
Every claim in the WKG must carry an epistemic class. Canonical classes (from WKG spec source):
- `VERIFIED` — independently confirmed fact
- `HISTORICAL` — established historical record
- `SOURCE_ATTRIBUTED` — "source X claims Y"; not independently verified
- `SYMBOLIC` — symbolic/metaphorical interpretation
- `HYPOTHESIS` — proposed explanation, testable
- `SPECULATIVE` — possible but no strong evidence
- `DISPUTED` — contradictory sources exist
- `UNKNOWN` — insufficient information

**Key principle:** `SOURCE_ATTRIBUTED ≠ VERIFIED`. eLo may represent a claim without believing it. This distinction must be enforced at the schema level — not a convention.

### D-3 — Relationship type registry
Canonical relationship types (from WKG spec source):
`IS` · `PART_OF` · `DERIVED_FROM` · `REPRESENTS` · `SYMBOLISES` · `CORRESPONDS_TO` · `ASSOCIATED_WITH` · `CAUSES` · `INFLUENCES` · `CONTRADICTS` · `SUPPORTS` · `CHALLENGES` · `ANALOGOUS_TO` · `TEMPORALLY_PRECEDES` · `DERIVED_MATHEMATICALLY_FROM` · `OBSERVED_AS` · `PROPOSED_BY` · `INTERPRETED_AS` · `HYPOTHESISED_AS`

Stored as a registry (not hardcoded): `wkg_relationship_types.json` or equivalent.

### D-4 — Claim/triple model
A claim is a directed triple: `(subject_entity_id, relationship_type, object_entity_id)` with:
- `claim_id` — stable UUID
- `epistemic_class` — from D-2
- `source_ids` — what establishes this claim
- `confidence` — float 0.0–1.0 (1.0 = VERIFIED; lower for HYPOTHESIS, SPECULATIVE)
- `created_at` — timestamp
- `experience_id` — the eLo experience that introduced this claim (may be null for seed data)
- `contradicted_by` — list of claim_ids that contradict this claim

### D-5 — Source registry
Every source that feeds the WKG must be registered:
- `source_id` — stable identifier
- `source_type` — BOOK · CONVERSATION · EXPERIENCE · OBSERVATION · DERIVED · EXTERNAL
- `title` — human-readable
- `author` — if known
- `date` — if known
- `notes` — provenance notes

Initial sources to seed:
- `SOURCE-001`: Harry B. Joseph, *The Book of Wisdom* Vol I (primary corpus, Phase 2)
- `SOURCE-002`: eLo experience chain (ongoing — every experience_id is a source)
- `SOURCE-003`: David L3 design directives (architectural source — not world knowledge)

### D-6 — Query interface (read-only)
A minimal Python interface for querying the WKG. Must support at minimum:
- `get_entity(entity_id)` → entity record
- `get_claims_about(entity_id)` → list of claims where subject or object = entity_id
- `get_claims_by_type(entity_id, relationship_type)` → filtered claims
- `search_entities(label)` → entity lookup by label or alias
- `get_epistemic_class(claim_id)` → epistemic class for a given claim
- `get_source(source_id)` → source record

No write path yet — MemoryFaculty sole-writer contract governs writes; the write interface is Phase 2.

### D-7 — MemoryFaculty write stub
A stub write path that MemoryFaculty can call to record a claim into the WKG from a processed experience. Not the full write pipeline — a stub that:
- accepts `(subject_entity_id, relationship_type, object_entity_id, epistemic_class, source_id, experience_id)`
- creates a claim record
- writes to the WKG store

This ensures the experience chain has a WKG terminus before Phase 2 populates the corpus.

---

## Storage

The WKG Phase 1 schema may be implemented as:
- JSON files (simplest — consistent with existing elo_spatial.json, vault_layer pattern)
- SQLite (acceptable if Builder judges this better for query performance)

Board preference: JSON for Phase 1 (schema exploration); migrate to SQLite in Phase 2 if needed. Builder may propose an alternative with rationale.

Suggested file locations:
- `memory/wkg/entities.json` — entity store
- `memory/wkg/claims.json` — claim store
- `memory/wkg/sources.json` — source registry
- `memory/wkg/relationship_types.json` — relationship type registry
- `runtime/wkg_faculty.py` — query interface + write stub

---

## Acceptance Tests

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | Entity creation | Can create an entity with all required fields; entity_id is stable UUID |
| AT-2 | Epistemic class enforcement | Cannot create a claim without an epistemic class; VERIFIED ≠ SOURCE_ATTRIBUTED at the schema level |
| AT-3 | Claim triple | Can create (Sun, SYMBOLISES, consciousness, SOURCE_ATTRIBUTED, SOURCE-001) with correct fields |
| AT-4 | Contradicted claim | Can mark a claim as contradicted_by another claim_id |
| AT-5 | Query: get_entity | Returns entity record for a known entity_id |
| AT-6 | Query: get_claims_about | Returns all claims for a known entity |
| AT-7 | Query: search_entities | Returns entity match for known label |
| AT-8 | MemoryFaculty write stub | MemoryFaculty can call the write stub with a valid experience_id; claim appears in claims store |
| AT-9 | Source registry | Source-001 and Source-002 exist in source registry after init |
| AT-10 | Experience chain terminus | Running the existing consequence chain against a test turn produces a WKG claim record via the write stub |

---

## What Is NOT in This WO

- Harry B. Joseph corpus ingestion — Phase 2
- Cultural context corpus — Phase 2+
- Full MemoryFaculty → WKG write pipeline — Phase 2
- Significance faculty → WKG query interface — after SP-29 is built
- Reflection faculty → WKG query interface — future

---

## Builder Notes

- Do not modify Executive, spine.py, or FREEZE_V1_LOCK
- Do not modify living_presence_spec.txt
- This WO runs on a separate track — it does not block and is not blocked by Stage 2 R&D Waves 1–5
- Check RTR entries RTR-034 through RTR-037 before any design decision that touches knowledge storage

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — AUTHORISED 2026-08-24*

---

## Result — Builder 2026-08-24

**Commit:** b9e26f9  
**Tests:** AT-1 through AT-10 — **10/10 PASS**

| Deliverable | File | Status |
|---|---|---|
| D-1 Entity model | `memory/wkg/entities.json` + `wkg_faculty.create_entity()` | ✅ |
| D-2 Epistemic class system | `_EPISTEMIC_CLASSES` frozenset + ValueError enforcement | ✅ |
| D-3 Relationship type registry | `memory/wkg/relationship_types.json` (19 types) | ✅ |
| D-4 Claim/triple model | `memory/wkg/claims.json` + `wkg_faculty.record_claim()` | ✅ |
| D-5 Source registry | `memory/wkg/sources.json` (SOURCE-001/002/003 seeded) | ✅ |
| D-6 Query interface | `wkg_faculty.get_entity/get_claims_about/get_claims_by_type/search_entities/get_epistemic_class/get_source` | ✅ |
| D-7 MemoryFaculty write stub | `wkg_faculty.record_claim()` — sole-writer contract preserved | ✅ |

**Disconnection-falsifiable:** tests patch `wkg._WKG_DIR` to temp dir; live store untouched during test run.  
**Builder notes:** Executive, spine.py, FREEZE_V1_LOCK, living_presence_spec.txt — not touched.
