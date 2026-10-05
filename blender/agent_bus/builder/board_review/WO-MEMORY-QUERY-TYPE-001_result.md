# WO-MEMORY-QUERY-TYPE-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Status:** COMPLETE — type_filter wired, 14/14 tests pass, commit 716ff5e

---

## Gap closed

`proposed_type` (episodic/semantic/procedural/emotional) was written to every vault record (encoded as t_code in the spot code) but retrieval never filtered by it. `vault_layer.lookup()` and `memory_faculty` had no type-aware query path.

---

## What was done

### Commit 716ff5e

**`memory/vault_layer.py`:**
- Added `_PROPOSED_TO_TCODE` mapping at module level:
  ```python
  "episodic" → "CV", "semantic" → "LN", "procedural" → "BL", "emotional" → "CN"
  "conversation" → "CV", "learn" → "LN", "build" → "BL", "connect" → "CN", ...
  ```
- Added `type_filter: str | None = None` parameter to `lookup()`
- Post-sort filter: splits spot on `·`, checks index 1 against `_want_tcode`
- Backwards-compatible: `type_filter=None` returns all types (existing callers unaffected)

**`memory/memory_faculty.py`:**
- Added `retrieve(query, type_filter=None, max_results=5)` — typed public query function
- Wraps `vault_layer.lookup()` with type_filter passthrough
- Callers: Executive, faculties that need episodic-only or semantic-only recall

---

## Acceptance — all pass

`tests/test_wo_memory_query_type.py` — 14/14:
- All 4 proposed_type names in `_PROPOSED_TO_TCODE`
- All 4 memory_type names in `_PROPOSED_TO_TCODE`
- episodic → CV, semantic → LN, procedural → BL, emotional → CN verified
- Filter returns only episodic (CV) records when `type_filter="episodic"`
- Filter returns only semantic (LN) records when `type_filter="semantic"`
- Zero cross-contamination between episodic and semantic result sets
- `type_filter="conversation"` (memory_type alias) same as `"episodic"`
- `retrieve()` passes type_filter through to lookup()
- `retrieve()` is importable and callable

---

## Files changed

| File | Change |
|------|--------|
| `memory/vault_layer.py` | +30 lines: `_PROPOSED_TO_TCODE` mapping, `type_filter` param + post-sort filter |
| `memory/memory_faculty.py` | +20 lines: `retrieve()` typed query function |
| `tests/test_wo_memory_query_type.py` | New — 14 acceptance tests |

**Commit:** `716ff5e`
