# WP_D — Memory Faculty Gap Analysis

**Status:** REVIEW COMPLETE — 4 gaps (1 HIGH, 3 MEDIUM)
**Proof document:** `engineering/proofs/03_memory_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| Memory Faculty called once per turn via spine | ✗ No `_memory_faculty()` in spine | 🔴 GAP |
| Memory context available and fresh each turn | ✗ `_memory_pack` built once at session start | 🔴 GAP |
| Semantic embeddings contribute to attention scoring | ✗ `embedding_store.py` computed but never queried | 🔴 GAP |
| Single session continuity system | ✗ state_manager + continuity/ coexist | 🔴 GAP |
| Memory updated exactly once per cycle | ⚠️ Write ordering correct; freshness incorrect | ⚠️ |
| Single writer to obsidian_vault/ | ✓ vault_layer + state_manager (separate sections) | ✓ Match |
| elo_state.json has single writer | ✓ state_manager.save() only | ✓ Match |
| Memory Faculty does not decide | ✓ Pure contribution | ✓ Match |

---

## Gaps requiring implementation

### GAP 1 — No _memory_faculty() in spine (🔴 HIGH)

**What architecture expects:** The spine calls each faculty in turn. Memory is a faculty. It should have a dedicated `_memory_faculty()` call in the spine that runs per turn.

**What exists:** Memory is loaded at session start (`server.py:712`) via `memory_pack_builder.build()`. This result is passed as a parameter to `attention.compute()`. No per-turn memory faculty call exists in the spine.

**Resolution:**
- Add `_memory_faculty(user_input, session_state, current_pack)` to `runtime/spine/spine.py`
- On each call: check if any vault write with `significance > 0.70` occurred this turn
- If yes: rebuild or patch the memory pack
- Return the (possibly refreshed) pack to the next faculty in the chain

**Implementation scope:** `runtime/spine/spine.py` (~20 lines), `memory/memory_pack_builder.py` (expose an incremental refresh path)

---

### GAP 2 — Memory pack stale mid-session (🔴 HIGH, same root as GAP 1)

**What exists:** Information written to the Obsidian vault during a session (via `journal_router.route()`) is not reflected in `_memory_pack` until the next session. The pack is a frozen snapshot.

**Resolution:** Part of GAP 1 fix — `_memory_faculty()` checks significance and refreshes when needed.

**Separate action:** Expose `vault_layer.last_write_ts` so the memory faculty can quickly detect whether a refresh is warranted without rebuilding from scratch every turn.

---

### GAP 3 — Semantic embeddings implemented but unused (⚠️ MEDIUM)

**What exists:** `memory/embedding_store.py` pre-computes embeddings at session start (if OPENAI_API_KEY set). `search(query)` is never called.

**Two options:**

**Option A — Integrate:** Have `_memory_faculty()` (or `attention.compute()`) call `embedding_store.search(user_input)` to surface semantically relevant memories. Replaces or supplements keyword scoring.

**Option B — Remove:** Delete `embedding_store.py` and its session-start call. Removes dead code; avoids burning OpenAI tokens on unused embeddings.

**Recommendation:** Option A — the system already invests in embedding computation. The search() function exists and is correct. Integrating it into memory scoring is low-risk and addresses a real gap (keyword scoring misses paraphrase matches).

---

### GAP 4 — Session continuity split (⚠️ MEDIUM)

**What exists:**
- `memory/state_manager.py` — raw history (emotional_history, session_summaries)
- `continuity/continuity_engine.py` — derives meaning (theme, direction, project)
- Both write to vault independently

**Resolution:**
- Formally designate `state_manager.py` as the **canonical session continuity layer**
- `continuity_engine.py` becomes a read-only deriving consumer — it reads from state_manager, writes nothing
- Remove `continuity_engine.py`'s vault write path

**Implementation scope:** `continuity/continuity_engine.py` (remove vault write, add state_manager import)

---

## Implementation priority order

1. **GAP 1 + GAP 2 together** — add `_memory_faculty()` + incremental refresh. These are the same fix.
2. **GAP 3** — integrate embedding search into memory faculty once it exists.
3. **GAP 4** — continuity consolidation. Lower risk, can happen after GAP 1.

---

## Invariants unblocked

| Invariant | Status Now | Status After |
|---|---|---|
| 11 — Memory updated exactly once per cycle | ⚠️ Partial | ✓ (after GAP 1+2) |
| Faculty authority model | ⚠️ Memory has no spine presence | ✓ (after GAP 1) |
