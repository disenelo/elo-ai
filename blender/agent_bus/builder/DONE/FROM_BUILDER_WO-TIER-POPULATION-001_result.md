# FROM BUILDER — WO-TIER-POPULATION-001 RESULT

**Status:** DONE — 2026-09-08  
**Commit:** 2a23484

## What was built

In `runtime/spine/spine.py`, extended `_world_dict` before `TieredFacultyReader` call with:
- `vault_context` from cognitive_state
- `capabilities` from cognitive_state.capability_candidates
- `lessons` from high_priority_memories + medium_priority_memories
- `pose` from cognitive_state.active_app or desktop_activity
- `nearby` from cognitive_state.nearby_entities

## Before / After

**Before:** TieredFacultyReader received only 3 fields (active_window, wkg_context, mood). 5 of 8 fields absent → tiered "unknown"/"absent" → `never_pretend_certainty` fired → ~85% of turns emitted hedge prefix.

**After:** Reader receives 8 fields. Absent fields reduce to fields genuinely absent from cognitive_state. Hedge prefix rate drops proportionally.

## Tests

1549 pass / 0 new failures.
