# WP-D Memory Faculty — Current Reality Review

**Status:** REVIEW COMPLETE — significant gaps
**Audit date:** 2026-07-12

---

## Faculty location

Memory Faculty is **scattered across 8 modules** with no unified entry point:

| Module | Responsibility |
|---|---|
| `memory/state_manager.py` | Session state persistence (elo_state.json) |
| `memory/memory_pack_builder.py` | Memory aggregation at session start |
| `memory/vault_layer.py` | Tiered vault writes (SPOT_CODES + summary + deep) |
| `memory/obsidian_loader.py` | Vault reader — ONLY file that reads obsidian_vault/ |
| `memory/significance_engine.py` | 9-dimension importance scoring |
| `memory/journal_router.py` | Significance-driven routing (runtime/obsidian/github) |
| `memory/embedding_store.py` | Semantic embeddings — **implemented but unused** |
| `continuity/` | Session continuity — separate system, not merged |

**No `_memory_faculty()` function exists in spine.py.** Memory is referenced in the spine header but never implemented as a faculty call.

---

## Invariant 11 — Memory updated exactly once per cycle

**Status: PARTIALLY VIOLATED**

- Write ordering is correct: attention (read) → state_manager.update → journal_router (vault)
- No circular overwrites or conflicts ✓
- BUT: `_memory_pack` is built **once at session start** and never refreshed
- Information written to vault in turn N is not visible to attention until next session
- journal_router.route() is a second write target per turn (runtime state + vault), not one unified write

---

## Violations

### V1 — No _memory_faculty() in spine (HIGH)

Spine header documents Memory Faculty in the call order. The actual spine code has no `_memory_faculty()` function. Memory logic is called directly from server.py (lines 710–712) at session start, never from the spine per-turn.

### V2 — Memory pack stale mid-session (MEDIUM)

`_memory_pack` built at server.py:712, never rebuilt. After vault writes (journal_router → vault_layer), the in-memory pack used by attention.compute() is stale. New notes are only visible next session.

**Fix:** Rebuild or partial-invalidate `_memory_pack` after Obsidian writes with significance > 0.70.

### V3 — Semantic embeddings unused (MEDIUM)

`memory/embedding_store.py` pre-computes embeddings at session start (if OPENAI_API_KEY set). `search()` is never called by attention.py or any consumer. Dead code path that wastes API tokens.

**Fix:** Integrate into `attention.compute()` scoring (replaces/supplements keyword-only scoring), or remove.

### V4 — Session continuity split (MEDIUM)

`memory/state_manager.py` holds raw history (emotional_history, session_summaries). `continuity/continuity_engine.py` derives meaning from that history (theme, direction, project). The two systems coexist without merging — both write to vault independently.

**Fix:** Merge continuity derivation into state_manager, or formally designate one as the canonical session continuity layer and have the other defer to it.

---

## Data ownership map (confirmed)

| Data Object | Writer | Reader | Notes |
|---|---|---|---|
| elo_state.json | state_manager.save() only | server.py globals | Single writer ✓ |
| obsidian_vault/ | vault_layer + state_manager + vault_writer | obsidian_loader ONLY | Read-segregation enforced ✓ |
| memory_pack.json | memory_pack_builder.build() | (offline reference only) | Not used at runtime |
| embedding_cache.json | embedding_store.warm() | embedding_store.search() | Unused path |

---

## What Memory Faculty correctly does NOT do

- Does not decide which facts to surface ✓
- Does not decide when to recall ✓
- Does not generate text ✓
- Does not route traffic ✓

All correct. The violations are about consolidation and freshness, not about boundary crossing.
