# WO-RS-001 — Implement Epistemic Grounding / Provenance
**Status: ✅ CLOSED — RS-GRND-01 already complete, 16/16 acceptance tests passed**
**Authority:** `_intake/SOURCE_2026-08-22_CA_build_directive_full_queue.md`
**Do not rebuild. Do not re-run. Move to WO-RS-002.**
**Priority:** P0 — BUILD NOW
**Source contract:** `docs/architecture/cards/RS-GRND-01_epistemic_grounding_v3.md`
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Date:** 2026-08-22

---

## Objective

Implement the RS-GRND-01 v3 contract exactly. No new design. No new gates. No new reviews.

## What to build

Add to the runtime:
- `EpistemicClass` — enum for GENERATED / RETRIEVED / REMEMBERED / CANONICAL / CURRENT_STATE / VERIFIED
- `PersistenceClass` — enum for the persistence level of each context item
- `AuthorityLevel` — enum for the authority level of each context item
- `ContextItem` — structured wrapper: content + epistemic_class + persistence_class + authority + provenance (origin, storage path, retrieval timestamp)
- `ExecutionTrace` — execution metadata captured before generation: what fired, in what order, with what inputs
- `CapabilityRecord` — record of which capability was invoked and why

Convert existing retrieval outputs into `ContextItem` objects before they enter `_assemble_prompt()`.

Preserve provenance through the full chain: `origin → storage → retrieval → assembly`.

Vault writes: add frontmatter fields:
```
epistemic_class: generated
session_id: <current session id>
```
Leave ALL existing vault notes untouched — no migration.

`_assemble_prompt()`: consume structured provenance. Render provenance only at the final model boundary as the `[EXECUTION — THIS TURN]` block from the actual runtime trace.

## Acceptance

Run **AC-GR1 through AC-GR12** from `RS-GRND-01_epistemic_grounding_v3.md`.

If a test fails: fix the implementation within this WO's scope. Do NOT create an architectural review.

Report: changed files, test results, pass/fail per AC-GR line.

## Hard constraints — do NOT touch

- WKG
- SPG
- CAL
- `canonical_identity.md`
- memory architecture
- retrieval filters
- prompt hacks
- old vault notes (no migration)
- any new policy/gate system

---

**Next card after this passes:** WO-RS-002.
