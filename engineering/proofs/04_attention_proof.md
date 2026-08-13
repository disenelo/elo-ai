# WP-E Attention Faculty — Current Reality Review

**Status:** REVIEW COMPLETE — Gap Analysis stage
**Audit date:** 2026-07-12
**Architecture reference:** WP_E_ATTENTION_FACULTY.md

---

## Faculty Location

- **Primary file:** `core/attention.py` (331 lines)
- **Public API:** `compute(user_input, memory_pack, session_state, loop_detected=False) → dict`
- **Pure function:** No side effects, no I/O, no external calls

---

## AttentionSnapshot Structure

```python
{
    "intent":                 str,   # 7-class: inquiry|creation|emotional|recall|simplify|conversation|stabilise
    "high_priority_memory":   list,  # score >= 8, capped at 4
    "medium_priority_memory": list,  # score 4–7, capped at 3
    "low_priority_memory":    list,  # score < 4
    "emotional_context": {
        "energy":           float,   # 0.0–1.0
        "tension":          float,   # 0.0–1.0
        "closure":          str,     # "open" | "closed"
        "inferred_state":   str,     # overwhelmed|stressed|energised|low-energy|present
        "valence":          str,     # positive_high|positive_low|neutral|negative_low|negative_high
        "momentum":         str,     # building|stable|declining|stuck
        "mirror_intensity": float,   # 0.3 (fixed)
    }
}
```

---

## Call Sites

| File | Line | Context |
|---|---|---|
| `server.py` | 810 | Main request handler — always before Executive |
| `main.py` | CLI | Interactive terminal mode |
| `training/generator/batch_runner.py` | — | Offline batch processing |
| `blender/blender_bridge.py` | — | Blender integration (empty pack) |

**Pattern confirmed:** Attention computed once per turn, before Executive, before LLM call. ✓

---

## Invariant 04 Compliance

**Invariant:** Attention Faculty never acts on its own output.

**Status: COMPLIANT ✓**

- Does not route traffic ✓
- Does not generate text ✓
- Does not trigger actions ✓
- Does not modify session state ✓
- Does not make decisions ✓
- Pure computation function only ✓

---

## Violations Found

### V1 — AttentionSnapshot mutated downstream (MEDIUM)

`server.py` lines 916–921 mutate `high_priority_memory` after `attention.compute()` returns:

```python
_why = _entity_why(raw) or _get_viewpoint(raw)
if _why and _action in ("answer", "connect", "reflect"):
    attention_model = dict(attention_model)                     # shallow copy
    attention_model["high_priority_memory"] = [_why] + _hp     # mutation
```

- Creates a shallow copy — `emotional_context` dict still references the original
- Prepends an entity-extracted "why" to high_priority_memory
- Occurs after attention but before prompt building

**Nature:** Data structure hygiene issue, not an architectural violation. Attention doesn't act on its own output — server.py does. But the output is no longer immutable.

### V2 — Exec decision injected into AttentionSnapshot (LOW)

`server.py` lines 940–942 add `_exec_decision` to the AttentionSnapshot before passing to spine:

```python
_attention_with_exec = dict(attention_model)
_attention_with_exec["_exec_decision"] = exec_decision
```

This creates an undocumented field on the snapshot. The spine reads it at `spine.py:162`. The field is not part of the AttentionSnapshot spec.

### V3 — Entity injection logic lives in server.py (MEDIUM)

The rule "if action is answer/connect/reflect, prepend entity context to high_priority_memory" belongs conceptually to the Attention Faculty but is implemented in server.py. High-priority memory construction is split:
- Base scoring: `attention.py`
- Entity injection: `server.py`

---

## Gaps Found

### G1 — Architecture doc is a stub (HIGH for process)

`docs/architecture/04_attention_faculty.md` — STATUS: PENDING. No formal spec exists.

### G2 — Momentum and valence do not persist across turns (LOW)

Both reset each turn. No cross-turn trajectory tracking. `state_machine.py` tracks `emotional_state` and `stability` separately, which partially compensates.

---

## Summary Table

| Expectation | Reality | Match? |
|---|---|---|
| Intent classification | ✓ 7-class, keyword-based, in attention.py | ✓ |
| Memory scoring and ranking | ✓ Semantic + keyword, HIGH/MED/LOW tiers | ✓ |
| Emotional state inference | ✓ Energy, tension, closure, valence, momentum | ✓ |
| AttentionSnapshot immutable | ✗ Mutated in server.py (entity injection + exec inject) | ⚠️ |
| Attention does not act on own output | ✓ Pure computation only | ✓ |
| Logic owned by Attention Faculty | ⚠️ Entity injection in server.py | ⚠️ |
| Architecture doc exists | ✗ Stub only | 🔴 |
| Momentum persistent across turns | ✗ Resets each turn | ⚠️ |

---

## Recommended Resolutions

1. **Document the entity injection contract** — add a comment in server.py explaining why the injection happens there (needs entity extraction context that isn't available inside attention.py). Mark `_why` injection as intentional and describe the implicit contract.
2. **Document `_exec_decision` injection** — it is a spine convenience, not an Attention field. Should be explicit.
3. **Write `04_attention_faculty.md`** — formal spec for the Attention Faculty.
4. **Momentum persistence** — defer to WP-D (Memory Faculty) which should own cross-turn emotional history.
