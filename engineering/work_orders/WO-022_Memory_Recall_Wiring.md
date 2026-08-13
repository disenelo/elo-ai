---
id: WO-022
title: "Debug: memory RECALL not wired to conversation — stores but doesn't retrieve on ask"
owner_seat: SEAT-ENG-003 (Memory Systems) / Builder
occupant: Builder (Python)
priority: P1
reason: "Live test (David 2026-07-31): asked 'what do you remember / tell me something from your memory' → eLo returned the canned vault-stats line (twice) or a generic web fact (Garrett Morgan), NOT actual memories. The vault HAS 753 records; retrieval isn't surfacing them into the response. This is the architecture gap David flagged."
review_required: L1 → L3
risk: none (diagnostic + wiring)
status: READY
created: 2026-07-31
---

# WO-022 — Wire memory recall into conversation

**The gap (grounded in code):** storage works, retrieval exists, but they're **not connected to the
recall intent** in the response path.

- ✅ **Storage works** — `server.py:1025` reports real stats ("753 records in the vault, 10 structured
  notes"). Memory is alive.
- ✅ **Retrieval functions exist** — `core/memory_engine.py`: `retrieve()` (259), `retrieve_by_project()`
  (284), `retrieve_structured()` (507); `memory/embedding_store.py:search()`; and `core/behavior_engine.py`
  `_recall_from_memory()` (714).
- ✅ **Recall intent is detected** — `core/attention.py:35` matches `remember` / `last time` / `before`.
- ❌ **They're not wired together for a recall REQUEST.** When David asks *"what do you remember / from
  your memory,"* the response returns the **canned stats line** (`server.py:1025-1031` "Memory's running.
  N records… What do you want to pull up?") — the same line **fired verbatim twice** — or the CAL diverts
  to a generic fact / associative frame, instead of calling `retrieve_structured()` and surfacing an
  actual memory.

## What to build
1. **Route the `recall` intent → real retrieval.** On a recall request, call
   `memory_engine.retrieve_structured(query)` / `retrieve(query)` and **compose the answer from the
   returned records**, not the canned stats line. The stats line is a *fallback when nothing matches*,
   not the default answer.
2. **Ground "from your memory" vs general knowledge.** "Tell me something from *your memory*" must pull
   from the vault, not web/general knowledge (the Garrett Morgan reply was general knowledge, not recall).
3. **Kill the verbatim repeat.** The canned stats line repeating identically = a loop-filter miss
   (`core/kernel.py` loop detection) — on repeat, force a different, retrieval-backed answer.

## Acceptance
- [ ] "What do you remember from last week / from your memory?" → surfaces **actual vault records**
      (with enough specificity to be recognisably *recall*), not the stats line or a generic fact.
- [ ] The stats line appears only as a genuine no-match fallback, never twice in a row.
- [ ] Recall requests route to `memory_engine.retrieve*`, verified with a trace.

## Handback
Trace: recall intent → retrieve_structured → records → composed answer. → COMPLETION_LOG → David L3.
Architecture note: this closes the Vol VIII **retrieval-into-conversation** gap (store ✅, recall ❌ → ✅).
Relates to WO-020 (loop-filter / CAL).
