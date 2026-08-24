# WO-SPINE-001 — integrate_session()
**Priority:** P1 — BUILD AFTER WO-WKG + WO-SPG complete
**Authority:** `_intake/SOURCE_2026-08-22_CA_build_directive_full_queue.md`
**Date:** 2026-08-22

---

## Problem

`compress_session()` compresses session information without actually integrating it. Session data is lost rather than consolidated into the cognitive state.

## What to build

Replace `compress_session()` with `integrate_session()` per the canonical contract (Vol XVII / `17_memory_update.md` / Volume_V/06).

`integrate_session()` must:
- Identify what was actually learned this session
- Integrate new knowledge into the appropriate memory layer (episodic / semantic / procedural)
- Update significance weighting
- Not merely summarise or compress — actually integrate

## Acceptance

- Session ends → `integrate_session()` runs
- Post-session memory contains integrated content, not a compressed dump
- `compress_session()` is removed or clearly deprecated
- Integration result is queryable in the next session

## Hard constraints

- Do not redesign the memory architecture
- Do not change WKG or SPG
- Implement against the existing `integrate_session()` contract on disk

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** `runtime/reflection_faculty.py` — `integrate_session()` with significance gate. `memory/consolidation_faculty.py` — wired at session end. `memory/vault_layer.py` — `compress_session()` deprecated. `tools/truth_sync.py` — calls `integrate_session()`, not `compress_session()`.

**Acceptance:** `tests/test_spine001_integrate_session.py` — 17/17 passed. Session integration runs with significance threshold; below-threshold sessions skipped; compress_session in vault_layer.py has deprecation notice; no new code imports it from vault_layer; server.py does not call compress_session.
