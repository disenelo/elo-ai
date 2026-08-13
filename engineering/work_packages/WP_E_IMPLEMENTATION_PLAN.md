# WP_E — Attention Faculty Implementation Plan

**Status:** READY FOR REVIEW
**Gap Analysis:** `WP_E_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/04_attention_proof.md`

---

## Scope

Three changes. Two are comment/documentation only. One is writing a new architecture doc.
No logic changes to attention.py.

---

## Step 1 — Document entity injection in server.py

**File:** `server.py`

Find lines ~916–921 where `attention_model["high_priority_memory"]` is mutated. Add comment block:

```python
# ── ATTENTION AUGMENTATION — Entity Injection ─────────────────────────────────────────
# Why here and not inside attention.py:
#   _entity_why() and _get_viewpoint() require the raw user input AFTER intent
#   classification — entity extraction needs intent context that is not available
#   inside attention.compute(). The augmentation is intentional and documented.
# Contract: only applied when action is answer/connect/reflect (informational turns).
# See: engineering/proofs/04_attention_proof.md § V1, WP_E_IMPLEMENTATION_PLAN.md
# ─────────────────────────────────────────────────────────────────────────────────────
_why = _entity_why(raw) or _get_viewpoint(raw)
if _why and _action in ("answer", "connect", "reflect"):
    attention_model = dict(attention_model)
    attention_model["high_priority_memory"] = [_why] + _hp
```

Find lines ~940–942 where `_exec_decision` is injected onto the snapshot. Add comment:

```python
# SPINE CONVENIENCE — _exec_decision injected here for downstream spine access.
# This is NOT an AttentionSnapshot field — it is a spine transport convenience.
# See: engineering/proofs/04_attention_proof.md § V2
_attention_with_exec = dict(attention_model)
_attention_with_exec["_exec_decision"] = exec_decision
```

---

## Step 2 — Write 04_attention_faculty.md

**New file:** `docs/architecture/04_attention_faculty.md`

Content: formal spec for the Attention Faculty. Must include:
- AttentionSnapshot spec (all fields with types and ranges)
- Entity injection — documented as intentional server-side augmentation
- `_exec_decision` field — documented as spine transport, not a faculty field
- 7-class intent taxonomy with examples
- Memory scoring algorithm (keyword + semantic, HIGH/MED/LOW tiers)
- Emotional state inference (energy, tension, closure, valence, momentum)
- What Attention Faculty must never do
- Cross-reference to `engineering/proofs/04_attention_proof.md`

---

## Step 3 — Regression check

- Confirm server.py runs without errors after comment additions
- Confirm attention.compute() still returns correct output structure
- Confirm entity injection still fires on answer/connect/reflect actions
- Confirm `_exec_decision` is present on the snapshot passed to spine

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- `core/attention.py` — no logic changes
- Any LLM routing or response generation
- Entity extraction logic (_entity_why, _get_viewpoint)

---

## Implementation order

```
Step 1 — Add comment blocks in server.py [~20 lines of comments]
    ↓
Step 2 — Write 04_attention_faculty.md [~150 lines new doc]
    ↓
Step 3 — Regression test
    ↓
WP_E DONE
```
