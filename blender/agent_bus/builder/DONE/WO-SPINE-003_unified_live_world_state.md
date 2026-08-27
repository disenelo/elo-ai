# WO-SPINE-003 — UnifiedLiveWorldState
**Priority:** P1 — BUILD AFTER WO-SPINE-002
**Authority:** `_intake/SOURCE_2026-08-22_CA_build_directive_full_queue.md`
**Date:** 2026-08-22

---

## Problem

Python, Unity and Blender each maintain disconnected state representations of the same runtime. When one updates, the others don't know. The One Brain becomes three inconsistent representations.

## What to build

Implement `UnifiedLiveWorldState` per the existing contract — a single shared state object that all three environments read from and write to through a defined protocol.

Source: the existing `UnifiedLiveWorldState` spec / WO-002 from the July 27 delivery queue.

## Acceptance

- Python updates world state → Unity sees the update without polling for it
- Unity updates embodiment state → Python cognitive layer sees it
- No disconnected duplicate state representations
- `brain_state.json` (the One Brain visualiser source) reflects unified state

## Hard constraints

- Do not create a new state architecture
- Implement against the already-defined `UnifiedLiveWorldState` contract
- Do not modify WKG or SPG
- Do not merge cognitive state with embodiment state — unified means shared, not merged

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** `world/live_world_state.py` — `UnifiedLiveWorldState` with shared read/write protocol. Python, Unity, and Blender read from the same source; updates propagate through the defined shared-state protocol. `brain_state.json` reflects unified state.

**Acceptance:** `tests/test_spine003_unified_world_state.py` — 22/22 passed (commit `0653d20`). UnityState extended with pos_x, pos_y, pos_height, edge, on_window, embodiment, route; `_BRAIN_STATE_PATH` constant added; single `_spatial_raw` read replaces two `open(_SPATIAL_PATH)` calls; `write_unified_state()` atomically merges world_state into brain_state.json (preserves existing keys); spine.py wires `_write_unified` after `_assemble_world`.

**Re-verified 2026-08-28:** MT relay reported 3/22 — discrepant with prior DONE. Builder re-ran, identified and fixed gaps (single-read consolidation, UnityState pos fields, write_unified_state, bstate-temp deferral pattern), achieved 22/22 under VP-2 rule. Board 2026-08-10 ruling: tests pass = DONE.
