# FROM_BUILDER — WO-MEMORY-TURN-TYPES Result

**WO:** WO-MEMORY-TURN-TYPES  
**Commit:** 93cd876  
**Date:** 2026-08-30  
**Status:** DONE — All ATs PASS

---

## What was done

Closed the memory write-path gap from WO-067 (root cause: `memory_categories: []` on most turns — field never populated at spine level).

### Files changed

1. **`memory/category_tagger.py`** (new)
   - `tag_turn(turn, intent_output, cognitive_state) -> list[str]`
   - Wraps `core.memory_engine._classify_memory_categories()`
   - Filters output to the 10 canonical categories: identity · relationship · preferences · plans · commitments · projects · decisions · experiences · contextual_state · learning
   - Strips legacy keys (`creative`, `world`, `user`) from canonical output

2. **`runtime/contracts.py`**
   - Added `memory_categories: tuple = field(default_factory=tuple)` to `CognitiveState`

3. **`runtime/spine/spine.py`**
   - `assemble_cognitive_state()` now calls `tag_turn()` on `raw_input` (wrapped in try/except for safety) and passes `memory_categories=_mem_categories` to `CognitiveState`

---

## AT results (`tests/test_wo_memory_turn_types.py`)

- AT-1 ✅ `memory/category_tagger.py` exists with callable `tag_turn()`
- AT-2 ✅ "I prefer X to Y" → `memory_categories: ["preferences"]`
- AT-3 ✅ clothing recommendation → `memory_categories: ["contextual_state", "preferences"]`
- AT-4 ✅ deadline/project/commit turn → `memory_categories: ["plans", "commitments", "projects"]`
- AT-5 ✅ `CognitiveState.memory_categories` non-empty for matching turns (via `assemble_cognitive_state`)
- AT-6 ✅ `write_interaction` triggered for tagged turns (vault entry confirmed)
- AT-7 ✅ py_compile clean on all 3 modified files

Full suite: **100 failed** (same pre-existing baseline as HEAD~1). 0 new failures from this WO.

---

## Notes

- The existing server.py memory tagging path (`_classify_memory_categories` inline in turn loop) remains functional and unchanged. The new spine-level path is the canonical source for `CognitiveState.memory_categories` — future Executive/faculty reads should use this field rather than calling `_classify_memory_categories` directly.
- Legacy categories (`creative`, `world`, `user`) still exist in `_CATEGORY_SIGNALS` for retrieval compatibility but are excluded from the canonical `tag_turn()` output.
