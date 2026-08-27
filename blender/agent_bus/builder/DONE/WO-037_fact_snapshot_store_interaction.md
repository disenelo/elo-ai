# WO-037 — Memory FACT SNAPSHOT: store_interaction() implemented

**Status:** DONE  
**Closed:** 2026-08-27  
**Seat:** SEAT-ENG-001 (Builder)

---

## What was missing

`store_interaction()` was absent from `core/memory_engine.py`. The function was named in
`tests/test_wo022_037_memory_recall_e2e.py` AT-1 (and cascaded to AT-2/AT-3), and was the
last open gap in WO-037 after the server write-back was wired (2026-08-03).

The server write path had migrated to `MemoryFaculty.submit()` (Vol VIII Invariant 7), writing
to the vault — but `interactions.json` was no longer receiving raw turn records. The FACT
SNAPSHOT requirement (discrete, queryable interaction log) was unmet.

## Fix

Added `store_interaction(user, response, action, project_tag)` to `core/memory_engine.py`
(after `_load_store()`). It:
- Appends a raw record `{user, response, action, project_tag, concepts, timestamp}` to
  `memory/interactions.json`
- Calls `_update_session(record)` to keep `session.json` current
- Uses `_detect_concepts()` to populate the concepts field for retrieval scoring

## Evidence

```
~/miniconda3/bin/python3 tests/test_wo022_037_memory_recall_e2e.py

  ✅ AT-1: store_interaction() persisted to interactions.json
  ✅ AT-2: retrieve('vinyl record player') finds the stored interaction
  ✅ AT-3: retrieve_by_project finds recent turn; bare keyword query does not
  ✅ AT-4 [retrieve_by_project imported as _mem_recency]
  ✅ AT-4 [bare recall flag assigned]
  ✅ AT-4 [retrieve_by_project called for bare recall]
  ✅ AT-5: conversing field published to blender_state.json each turn
  ✅ AT-6: interactions.json live (last modified 0.0h ago)
  ✅ AT-7: py_compile clean on server.py

WO-022/037 e2e  9 passed  0 failed
```

## WO-037 acceptance met

1. ✅ Write-back LANDED (wired 2026-08-03 — `interactions.json` / `session.json` update on turns)
2. ✅ FACT SNAPSHOT: `store_interaction()` writes discrete interaction records; `retrieve()` surfaces
   them by keyword; `retrieve_by_project()` surfaces most-recent turns for bare recall.

**WO-037 is DONE.**
