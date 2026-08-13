# WP_E — Attention Faculty Gap Analysis

**Status:** REVIEW COMPLETE — 3 violations, 2 gaps
**Proof document:** `engineering/proofs/04_attention_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| Intent classified in Attention Faculty | ✓ 7-class, in attention.py | ✓ Match |
| Memory scored and ranked in Attention Faculty | ✓ HIGH/MED/LOW tiers | ✓ Match |
| Emotional state inferred in Attention Faculty | ✓ Energy, tension, closure, valence, momentum | ✓ Match |
| AttentionSnapshot immutable after compute() | ✗ Mutated in server.py (entity injection + exec inject) | 🔴 GAP |
| All Attention logic owned by Attention Faculty | ✗ Entity injection lives in server.py | 🔴 GAP |
| Architecture doc exists | ✗ `docs/architecture/04_attention_faculty.md` is a stub | 🔴 GAP |
| Attention Faculty does not act on own output | ✓ Pure computation | ✓ Match |
| Momentum persists across turns | ✗ Resets each turn | ⚠️ |

---

## Gaps requiring implementation

### GAP 1 — AttentionSnapshot mutated post-compute (🔴 MEDIUM)

**What exists:** `server.py:916–921` — after `attention.compute()` returns, server.py:
1. Extracts entity context (`_entity_why` / `_get_viewpoint`)
2. Prepends it to `high_priority_memory`
3. Injects `_exec_decision` as an undocumented field on the snapshot

**Problem:** The snapshot is no longer the output of Attention Faculty — it is an augmented object assembled by server.py. This creates an implicit contract the faculty spec does not document.

**Resolution:**
- Document the entity injection as an intentional server-side augmentation in `server.py` (comment block explaining why entity context cannot go inside attention.py — it requires entity extraction that is not available there)
- Mark `_exec_decision` injection with an explicit comment: "Spine convenience field — not an AttentionSnapshot field"
- Add both fields to `CognitivePlan` dataclass as named fields so the implicit contract becomes explicit

**Implementation scope:** `server.py` (~10 lines of comments), `runtime/spine/plan.py` (add fields)

---

### GAP 2 — Entity injection logic lives in server.py (⚠️ MEDIUM)

**What exists:** The rule "if action is answer/connect/reflect, prepend entity context" is business logic for Attention Faculty but implemented in server.py. High-priority memory construction is split across two files.

**Resolution (pragmatic):**
- The entity extractor (`_entity_why`, `_get_viewpoint`) requires context that would be expensive to pass into attention.py
- Accept the split but document it formally: add a `# ATTENTION AUGMENTATION — see 04_attention_faculty.md §Entity Injection` comment block in server.py

**Full resolution (ideal):**
- Pass `_entity_why` result to `attention.compute()` as an optional `entity_context` parameter
- attention.py handles the prepend internally
- Keeps all Attention logic inside the faculty

**Recommendation:** Pragmatic path first (comments), then ideal path if WP-E gets a second pass.

---

### GAP 3 — Architecture doc is a stub (🔴 PROCESS)

`docs/architecture/04_attention_faculty.md` is "STATUS: PENDING".

**Resolution:** Write the formal spec. Should include:
- AttentionSnapshot spec (with entity injection documented as intentional)
- 7-class intent taxonomy with examples
- Memory scoring algorithm description
- Emotional state inference rules
- What Attention Faculty must never do

**Implementation scope:** New markdown file, ~150 lines.

---

## Low priority / deferred

### G4 — Momentum not persistent across turns (LOW)

`valence` and `momentum` reset each turn. `state_machine.py` partially compensates via `emotional_state` tracking. Deferred to WP-D (Memory Faculty should own cross-turn emotional trajectory).

---

## Implementation priority order

1. **GAP 3** — write the architecture doc. Unblocks everything else.
2. **GAP 1** — document entity injection + `_exec_decision` injection with explicit comment blocks.
3. **GAP 2** — pragmatic: comments; ideal: refactor entity injection into attention.compute() signature.

---

## Invariants unblocked

| Invariant | Status Now | Status After |
|---|---|---|
| 04 — Attention Faculty never acts on own output | ✓ Already clean | ✓ |
| Architecture documentation complete | ✗ Stub | ✓ (after GAP 3) |
