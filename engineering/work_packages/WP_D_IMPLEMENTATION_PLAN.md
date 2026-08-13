# WP_D — Memory Faculty Implementation Plan

**Status:** READY FOR REVIEW
**Gap Analysis:** `WP_D_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/03_memory_proof.md`

---

## Scope

Four changes. Priority order is fixed — GAP 1+2 first (they share a root cause).

---

## Step 1 — Add _memory_faculty() to spine.py + incremental refresh

**File:** `runtime/spine/spine.py`

Add a `_memory_faculty()` function called after language faculty, before attention faculty:

```python
def _memory_faculty(user_input: str, session_state: dict, current_pack: dict) -> dict:
    """
    Memory Faculty — checks if pack needs refresh after vault writes this turn.
    Returns the (possibly refreshed) memory pack.
    Called once per turn, before attention.compute().
    """
    from memory.vault_layer import last_write_significance   # see Step 1b
    from memory.memory_pack_builder import build as _rebuild

    sig = last_write_significance()
    if sig is not None and sig > 0.70:
        # A significant vault write happened — refresh the pack
        try:
            return _rebuild(session_state)
        except Exception:
            pass  # on failure, return current pack unchanged

    return current_pack
```

Update the spine call sequence to include this call:
```python
lang_result    = _language_faculty(raw)
memory_pack    = _memory_faculty(raw, session_state, current_memory_pack)  # ← ADD
attn_snapshot  = _attention_faculty(raw, memory_pack, session_state)
rel_result     = _relationship_faculty(lang_result, session_state)
exec_decision  = _executive_faculty(attn_snapshot, rel_result, session_state)
```

**Step 1b — Expose `last_write_significance` from vault_layer.py:**

**File:** `memory/vault_layer.py`

Add a module-level variable and accessor:
```python
_last_write_sig: float | None = None

def last_write_significance() -> float | None:
    return _last_write_sig

# In the vault write function, after scoring:
def write(entry: dict, significance: float) -> None:
    global _last_write_sig
    _last_write_sig = significance
    # ... existing write logic ...
```

**Note:** This is reset at session start (set to None) so the faculty only refreshes when a write occurs in the *current* turn, not stale writes from earlier.

---

## Step 2 — Integrate semantic embeddings into memory scoring

**File:** `memory/embedding_store.py` (existing, confirm `search()` is callable)

**File:** `core/attention.py`

In `compute()`, after building the initial memory scores (keyword/semantic scoring), call embedding search:

```python
from memory.embedding_store import search as _embed_search

def compute(user_input, memory_pack, session_state, loop_detected=False):
    # ... existing keyword scoring ...

    # Semantic embedding boost (if embedding store is warm)
    try:
        semantic_matches = _embed_search(user_input, top_k=3)
        for match in semantic_matches:
            # Boost memory score for semantically similar entries
            for mem in all_memories:
                if mem.get("id") == match.get("id"):
                    mem["_score"] = mem.get("_score", 0) + match.get("score", 0) * 0.3
    except Exception:
        pass  # graceful degradation — embeddings are enhancement, not required

    # ... rest of scoring and bucketing ...
```

**Note:** This requires that memory items have stable `id` fields and that `embedding_store.search()` returns `[{"id": ..., "score": float}, ...]`. Confirm the actual return signature before implementing.

---

## Step 3 — Consolidate session continuity

**File:** `continuity/continuity_engine.py`

- Remove vault write path from `continuity_engine.py`
- `state_manager.py` is the canonical session continuity layer
- `continuity_engine.py` becomes read-only: derives meaning, writes results back to `session_state` in memory only (not to vault)

Find all `vault_layer.write()` or `obsidian_loader` write calls in `continuity_engine.py` and remove them.

Add a comment at the top:
```
# CONTINUITY ENGINE — Read-only derivation.
# Derives theme/direction/project from state_manager history.
# Does NOT write to vault — state_manager.py is the canonical continuity writer.
# See: engineering/work_packages/WP_D_IMPLEMENTATION_PLAN.md Step 3
```

---

## Step 4 — Regression check

- Confirm memory faculty is called per turn with a new `_memory_faculty()` log line (add temporary print, remove after)
- Trigger a high-significance turn; confirm `last_write_significance()` returns > 0.70
- Confirm memory pack is rebuilt after the high-significance write
- Confirm embedding search doesn't crash when embeddings are cold (OPENAI_API_KEY not set)
- Confirm continuity_engine.py no longer writes to vault (check vault_layer call count stays same or decreases)

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- `prompts/` — FREEZE_V1_LOCK
- Memory data schemas in elo_state.json or obsidian_vault
- The significance scoring algorithm
- vault_layer.py write logic (only add last_write_significance export)

---

## Cross-WP dependency

WP-H GAP 2 (add `_memory_faculty()` to spine) is the same as Step 1 of this plan. WP-D owns the implementation; WP-H signs it off.

---

## Implementation order

```
Step 1a — Add _memory_faculty() to spine.py [~25 lines]
Step 1b — Expose last_write_significance in vault_layer.py [~8 lines]
    ↓
Step 2 — Integrate embedding search into attention.compute() [~15 lines]
    ↓
Step 3 — Remove vault write from continuity_engine.py [~5 lines removed]
    ↓
Step 4 — Regression test
    ↓
WP_D DONE — WP_H GAP 2 also satisfied
```
