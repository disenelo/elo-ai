# FROM_BUILDER — WO-SP29 Result

**WO:** WO-SP29 — Wire Significance Faculty into Cognitive Spine  
**Commit:** 6e7e710  
**Date:** 2026-08-30  
**Status:** DONE — All ATs PASS (6/6)

---

## What was done

Closed the gap: `compute_significance()` existed and was called in `executive_context.py` but its output never reached `CognitiveState` or `executive.py`. Self-initiation and memory gates had no faculty backing.

### Files changed

1. **`runtime/contracts.py`**
   - Added `significance_score: float = 0.0` to `CognitiveState` (after `memory_categories`, before `assembly_confidence`)

2. **`runtime/spine/spine.py`** (`assemble_cognitive_state()`)
   - Calls `compute_significance()` via `world.world_delta.compute_delta()` (same pattern as `server.py:_world_event_thought`)
   - Stores `_sig_result["overall"]` as `significance_score` on `CognitiveState`
   - Wrapped in try/except; falls back to `0.0`

3. **`runtime/executive.py`** (`decide()`)
   - Reads `significance_score` from `attention_model` (dict from `ExecutiveContext.world_dict`)
   - Adds `"memory_worthy": _sig_overall >= 0.72` to return dict
   - Adds `"self_init_eligible": _sig_overall >= 0.90` to return dict

---

## AT results (`tests/test_wo_sp29_significance.py`)

- AT-1 ✅ `assemble_cognitive_state()` populates `significance_score` (observed: 0.0308 for empty world_delta — [ESTIMATE] weights)
- AT-2 ✅ `significance=0.05` → `memory_worthy=False`
- AT-3 ✅ `significance=0.95` → `self_init_eligible=True`, `memory_worthy=True`
- AT-4 ✅ SP-31 thresholds unchanged (0.72 / 0.90); `may_self_initiate()` interface intact
- AT-5 ✅ `CognitiveState.significance_score` field exists with default 0.0
- AT-6 ✅ py_compile clean on all 3 modified files

Full suite: **100 failed** (same pre-existing baseline). 0 new failures.

---

## Notes

- WO card's class path (`faculties/significance/significance_faculty.py`, class `SignificanceFaculty`) was wrong. Actual: `runtime/significance_faculty.py`, function `compute_significance(world_delta, elo_self_state)`. Wired to actual interface.
- With [ESTIMATE] uniform weights, all text-only turns score ≈ 0.031 overall — well below both thresholds. This is expected pending David L3 D-gate weight decision.
- `memory_worthy` and `self_init_eligible` are now on the executive return dict; `server.py` memory write path can be updated to gate on `plan` executive flags in a future WO.
- SP-31 world-event path (`_world_event_thought()`) already called `compute_significance()` independently — unchanged.

*Board / Lead Architect acting as Builder · 2026-08-30*
