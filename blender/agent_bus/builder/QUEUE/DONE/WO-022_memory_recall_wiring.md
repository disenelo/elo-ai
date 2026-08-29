# WO-022 — Wire memory recall into conversation (Tier 2)

> **⚡ VERIFY FIRST** — `DAVID_APPROVED.md` records this as "green+tested" 2026-08-10. Tests exist: `tests/test_wo022_memory_recall.py` · `tests/test_wo022_037_memory_recall_e2e.py`. **Run them before any implementation.** If all pass → return result card with test evidence and close. If any fail → implement the fix described below.



**Full WO:** `engineering/work_orders/WO-022_Memory_Recall_Wiring.md`
**Priority:** P1 · **Status:** READY · **Owner:** Builder
**From:** Board — Tier 2 dispatch 2026-08-29 (Presentable v1 daily-use baseline)

## The gap
When David asks "what do you remember / tell me something from your memory," eLo returns the canned stats line (`server.py:1025-1031`) or a generic web fact — NOT actual vault records. Storage works (753+ records), retrieval functions exist (`memory_engine.retrieve_structured()`, `memory_engine.retrieve()`), recall intent is detected (`attention.py:35`) — but they're not connected for a recall REQUEST.

## What to build
1. **Route recall intent → real retrieval**: call `retrieve_structured(query)` and compose answer from returned records, not the stats line. Stats line = fallback when nothing matches, not default answer.
2. **Ground "from your memory" vs general knowledge**: must pull from vault, not web/general.
3. **Kill verbatim repeat**: canned stats line repeating identically → loop-filter miss. On repeat, force retrieval-backed answer.

`executive.py` — **check FREEZE_V1_LOCK boundary**. If recall routing requires executive.py changes, scope to server.py / memory_engine.py only and note the gap.

**Return:** `DONE/FROM_BUILDER_WO-022_memory_recall_result.md` · ATs · commit

*Board · 2026-08-29*
