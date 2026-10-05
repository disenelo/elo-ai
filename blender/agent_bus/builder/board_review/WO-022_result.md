# WO-022 — Memory Recall Wiring — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Status:** COMPLETE — 14/14 tests pass (pre-existing implementation verified)

---

## Gap closed

WO-022 spec described recall intent being detected but routing to a canned stats line ("Memory's running. N records. What do you want to pull up?") instead of real vault retrieval. Investigation confirms the fix was already applied: the stats-line path is dead code, and the real vault retrieval path is live.

---

## What was found

### Dead code (never called)
- `server.py:1811` — `_MEMORY_RECALL_TRIGGERS` — defined, never used
- `server.py:1821` — `_memory_recall_response()` — defined, never called

These are inert. They do not affect runtime behaviour.

### Live recall path (server.py:5670–5833)
1. `_MEMORY_QUERY_PHRASES` (line 5670) — expanded trigger set including `"what do you remember"`, `"from your memory"`, `"recall something"`, etc.
2. `from runtime.recall_intent import is_recall_query as _is_recall_query` (line 5692)
3. `_memory_query = _is_recall_query(_raw_l, _MEMORY_QUERY_PHRASES)` (line 5693)
4. `if _memory_query:` (line 5727) — gates vault retrieval path:
   - `vault_layer.recall_context(query)` → vault hits injected into system prompt
   - `vault_layer.lookup(query)` → named memory files retrieved
   - `core/memory_engine.retrieve()` and `retrieve_by_project("disenelo recent")` — recency retrieval
   - `memory.fact_store.facts_summary()` — fact store summary
5. Stats-line prohibition directive present in injected system prompt (AT-4 verified)

### Obsidian vault
1756 memory files present and non-empty — retrieval has real content to draw from.

---

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| AT-1 | Recall triggers detected (9 canonical phrases) | ✅ — `_MEMORY_QUERY_PHRASES` + `is_recall_query()` |
| AT-2 | "tell me something from your memory" detected | ✅ — `"from your memory"` in trigger set |
| AT-3 | Topic extraction skips fillers, produces useful vault query | ✅ — `_RECALL_SKIP` frozenset + min length 3 |
| AT-4 | Stats-line prohibition directive in server.py system prompt | ✅ — "Never say 'Memory" directive verified in source |
| AT-5 | Frozen kernel tests still green | ✅ — wo001, wo014, wo006 all pass |
| AT-1 (e2e) | MemoryFaculty.submit() routes correctly | ✅ |
| AT-2 (e2e) | vault.lookup() returns list of hits | ✅ |
| AT-3 (e2e) | retrieve_by_project + retrieve both return lists | ✅ |
| AT-4 (e2e) | bare recall flag → retrieve_by_project called | ✅ |
| AT-5 (e2e) | conversing field published to blender_state.json | ✅ |
| AT-6 (e2e) | Vault non-empty (1756 files) | ✅ |
| AT-7 (e2e) | py_compile clean on server.py | ✅ |

---

## Tests

`tests/test_wo022_memory_recall.py` — **5/5**  
`tests/test_wo022_037_memory_recall_e2e.py` — **9/9**  
Total: **14/14**

Note: these test files use `sys.exit()` at module level — run with `python3 tests/<file>`, not pytest.
