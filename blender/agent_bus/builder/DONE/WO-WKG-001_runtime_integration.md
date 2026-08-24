# WO-WKG-001 — WKG Runtime Integration
**Priority:** P1 (after WO-RS-001..004 pass)
**Source:** existing ratified WKG architecture + `knowledge/wkg_schema.py` + `knowledge/graph_loader.py`
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Date:** 2026-08-22

---

## Objective

Move WKG from architectural definition into the live cognitive pipeline. Wire it so the Executive actually consumes structured WKG knowledge — not WKG text pasted into a prompt.

## What to wire

```
WKG
 ↓
retrieve structured claim
 ↓
provenance / authority / epistemic_class
 ↓
ContextItem       ← from WO-RS-001
 ↓
_assemble_prompt()
 ↓
Executive
```

WKG retrieval must return `ContextItem` objects (not anonymous strings) carrying:
- `epistemic_class`: one of VERIFIED / UNVERIFIED / SPECULATIVE / GENERATED / CONTRADICTED / UNKNOWN
- `authority` and `provenance` fields
- Vol XXIV `kind`/`confidence` mapping preserved

Use `knowledge/graph_loader.py:retrieve_wkg()` — it already exists. Wire it into the assembly path.

## Acceptance

- WKG claim appears in assembled prompt with its epistemic_class and provenance
- VERIFIED claim labelled VERIFIED; SPECULATIVE labelled SPECULATIVE
- No WKG content appears as an anonymous string in the prompt
- Existing Phase 1 tests still pass: 20/20 AT-W1..AT-W13
- Vol XXIV regression: 5/5

## Hard constraints — do NOT

- redesign WKG schema
- invent additional relationship types
- move personality or self-state into WKG
- use WKG as general memory (it is structured relational knowledge only)
- modify SPG to make this easier

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:**
- `knowledge/graph_loader.py` — `retrieve_wkg_context_items()`: maps WKG claims to `ContextItem` objects with `epistemic_class`, `authority`, `provenance`, `persistence_class`
- `server.py:2739` — WKG ContextItems retrieved per-turn, rendered via `_render_ctx_block()`, merged into `g_ctx` before model boundary

**Acceptance:** `tests/test_wkg001_context_items.py` — 25/25 passed. WKG claims appear in assembled prompt with epistemic_class and provenance. VERIFIED labelled VERIFIED; SPECULATIVE labelled SPECULATIVE. No anonymous strings.

**Regression:** WKG Phase 1 20/20 ✅ · Vol XXIV 5/5 ✅
