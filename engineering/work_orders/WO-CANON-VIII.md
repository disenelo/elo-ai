# WO-CANON-VIII — Memory Architecture: wire the single MemoryFaculty + reinforce()-on-retrieval

**Owner:** Builder (eLo OS — `memory/`). **Priority:** P2 — Horizon-2 (post-Presentable v1), Tier A.
**Status:** DONE — 2026-08-27 (18/18 ATs pass; Invariant 7 verified clean). **Closes:** Audit gaps #3/#4.

**Canon refs:** Volume VIII — Ch.1 `01_Memory_Architecture.md`, Ch.2 `02_The_Four_Memory_Types_and_Data_Shapes.md`,
Ch.3 `03_Consolidation_and_the_Forgetting_Curve.md`, Ch.4 `04_Sole_Writer_Retrieval_and_Boundaries.md`. Decision Log
D-F (Memory Faculty sole LTM writer, RATIFIED). Retire stub `17_memory_update.md`; make Vol VIII the memory root.

## Problem / Goal
The tiered vault, facts store, consolidation faculty and forgetting curve are LIVE (WO-011). Two wiring edges are
PENDING: (a) the **single logical `MemoryFaculty`** (candidate-in / decision-out) does not exist — `journal_router`
and consolidation call `write_memory` directly; (b) **`reinforce()` is not called on retrieval**, so the forgetting
curve runs without its counterforce. Goal: complete D-F by routing all writes through one owner, and wire
reinforce-on-use — both are wiring over LIVE code, not new subsystems.

## Scope to DoD (grounded in Ch.1–Ch.4)
- **Wire the single logical `MemoryFaculty.submit(candidate)` (Ch.4 §4.1.2):** route every `write_memory` caller
  (`memory/consolidation_faculty.py`, `runtime/reflection_faculty.py::integrate_session`,
  `memory/journal_router.py` → `tools/truth_sync.compress_to_obsidian`, `faculties/music_memory/storage.py`) through
  one owner that decides `{write | reinforce existing | drop}`, sets final weight, and calls
  `memory/vault_layer.py::write_memory` **once**. A `Memory Candidate` carries `source_faculty`, `content`,
  `proposed_type` (episodic|semantic|procedural|emotional), `proposed_weight` (0–9, a REQUEST), `significance`
  (`SignificanceProfile`), `verified`. The physical sole-writer chokepoint already holds; this adds the logical owner.
- **Wire `reinforce()`-on-retrieval (Ch.3 §3.4 / Ch.4 §4.2.4):** call `memory/consolidation_faculty.reinforce(spot)`
  for each record the Executive actually uses in a turn, from the retrieval path (`vault_layer.recall_context`/`lookup`),
  in the integration window (not the hot loop). This is the single missing edge that makes §3.4 real.
- **Preserve LIVE contracts (do not regress):** sole reader `memory/obsidian_loader.py` (kernel never sees vault
  paths/markdown, only the processed `MemoryPack` from `memory/memory_pack_builder.py`). Write atomicity: index row +
  summary note + deep note in one call, all-or-none; every note carries `type: memory-summary`/`memory-deep`
  frontmatter. Spot-code discipline: weight in the code AND frontmatter `weight:` AND body `**Weight:** N/9` stay in
  sync (`_update_weight_in_content`). Retrieval returns `{status: live|absent, results:[{memory, confidence, timestamp,
  source}]}` (confidence = weight/9, sorted weight-desc), never a bare string; vault-down → `status: absent`, proceed on
  memory_pack, flagged stale, never fabricate.
- **Consolidation cycle stays timed (never hot loop):** FORGET `apply_forgetting_curve()` → INTEGRATE
  `compress_session()` → `integrate_session(weight=7, tags=["consolidated","session-close"])` → PATTERN
  `_extract_patterns()`. Keep the LIVE curve constants (canon): `_IDENTITY_FLOOR=8`, `_DECAY_THRESHOLD=6`,
  `_DECAY_AGE_DAYS=14`, `_DECAY_STEP=1`, `_REINFORCE_STEP=1`, `_WEIGHT_CAP=9`, floor 1; `dry_run=True` audit hook.
- **Personality outputs are proposals only:** any trait-implying consolidation output → `VALIDATION_REQUIRED` proposal
  to Vol X / V Ch.7, never self-applied. Companion stores (`fact_store`, `memory_pack`) are caches, never sources of
  truth. Boundaries: WM (Vol VI), World State (Vol XV), Knowledge (Vol XXIV), Autobiographical Thread (Vol XXI) may not
  open their own permanent store — consolidation is the sole bridge.

## Definition of Done
- All durable writes flow through `MemoryFaculty.submit` → one `write_memory` call; no caller writes the vault directly.
- `reinforce()` fires on records the Executive uses; decay demonstrably countered on used memories.
- Retrieval returns confidence-annotated results; vault-down is honest; identity floor (weight ≥8) never decays.
- `17_memory_update.md` reference retired; Vol VIII is the memory root. Audit can mark Vol VIII COMPLETE.

## Tests to write (`tests/test_canon_viii_memory.py`)
- Ch.1: four types distinguished, weight not timestamp, episodic→semantic, atomic consolidation, identity never
  decays, no unvalidated trait shift, significance→consolidation→personality survives restart.
- Ch.3: timed only (never response path), atomic on failure (errors[] populated), identity floored (weight-9 aged 200d
  untouched), bounded decay (weight-4 aged 20d→3, never <1, never <14-day), episodic→semantic, dry_run writes nothing,
  **reinforce counters decay [was blocked on §3.4 — now the wiring under test]**, no unvalidated trait shift.
- Ch.4: one writer (bytes only via `vault_layer.write_memory`), **candidate decided by owner [the §4.1.2 wiring under
  test]**, confidence on recall (no bare string), meaning not keyword, vault-down honest, no neighbour store, thread
  reads never write.

## Dependencies + blocked-by
- **Blocked by:** — (none; runs behind Presentable v1). Note for CA: retire `17_memory_update.md` stub; decide whether
  procedural/emotional get first-class record-type codes (currently implicit) — flag, does not block the two wiring edges.
- Cross-volume: Vol V Ch.3/Ch.5/Ch.6/Ch.7; Vol VI (WM boundary above); Vol XV (World State beside); Vol XXIV (Knowledge
  beside, its only runtime writer is Consolidation); Vol XXI (Autobiographical Thread = derived read-only view).
- **Gate:** none blocking build. Reconcile FC-2 (9-dimension significance) at V Ch.5. Not David L3.

## Lane
Builder (Python — `memory/` single-owner wiring + reinforce-on-retrieval edge). Architect coordinates + retires the
`17_memory_update.md` reference (Markdown, Architect lane).
