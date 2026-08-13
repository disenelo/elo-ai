# WP-G Executive Faculty — Current Reality Review

**Status:** REVIEW COMPLETE — 1 gap, 1 boundary violation
**Audit date:** 2026-07-12

---

## Faculty location

| File | Role | Frozen? |
|---|---|---|
| `runtime/executive.py` | Core decision engine: tone, action, max_sentences | ✓ FREEZE_V1_LOCK |
| `runtime/server.py` | Calls executive.decide(); applies stabilisation override | No |
| `runtime/spine/spine.py` | Calls _executive_faculty(); reads pre-made decision; capability selection | No |

The Executive faculty is split across **three files**, only one of which is frozen.

---

## What Executive correctly does

- `executive.decide(attention, session, relationship)` → `{action, tone, max_sentences, stabilise, rationale}`
- 5 tones: SILENCE-AWARE, DIRECT, JOYFUL, WITTY, CHILDLIKE-WISE
- 10 CAL actions: answer, build, connect, celebrate, reflect, ground, challenge, witness, silence, navigate
- Stabilisation flag: when `attention.emotional_context.inferred_state == "overwhelmed"`, sets `stabilise: True`

---

## Invariant 05 — Executive owns the final decision

**Status: VIOLATED (split ownership)**

### V1 — Stabilisation override strips fields (HIGH)

In `server.py`, when `exec_decision["stabilise"] == True`, the server applies an override:

```python
if exec_decision.get("stabilise"):
    exec_decision = {"action": "ground", "tone": "SILENCE-AWARE", "max_sentences": 2, "stabilise": True}
```

This **replaces the entire exec_decision dict**, discarding:
- `rationale` — the Executive's reasoning (lost)
- `confidence` (if present) — (lost)
- Any diagnostic fields the frozen executive returned

The override is correct in spirit (overwhelmed user → ground) but wrong in implementation: it silently destroys Executive output rather than extending it.

**Fix:** Extend rather than replace:
```python
if exec_decision.get("stabilise"):
    exec_decision = dict(exec_decision)  # preserve all fields
    exec_decision.update({
        "action": "ground",
        "tone": "SILENCE-AWARE",
        "max_sentences": 2,
        "overridden_by_safety": True,
        "original_action": exec_decision.get("action"),
        "original_tone": exec_decision.get("tone"),
    })
```

### V2 — Capability selection in spine.py (HIGH)

`spine.py:194–204` selects which capabilities to enable based on intent and agent availability. This is an **Executive decision** (what eLo can do this turn) that has migrated into spine assembly:

```python
# spine.py ~line 194
_caps = _select_capabilities(intent, agents)
```

The spine should only assemble and deliver. Capability selection (what tools/agents eLo is authorised to use this turn) is a decision, not assembly.

**Note:** `runtime/executive.py` is FROZEN. Capability selection cannot be moved into it without violating the freeze. Resolution options:
1. Create `runtime/spine/executive_extension.py` — capability selection delegated from Executive's decision, pre-call — called from spine but logically owned by Executive
2. Accept as a spine responsibility with a formal note that it is delegated from Executive context

---

## Gaps Found

### G1 — Executive rationale not propagated to diagnostics (LOW)

`exec_decision["rationale"]` is computed by executive.py but discarded at the stabilisation override step (V1 above). Even without stabilisation, the rationale is not logged to `logs/pending_commits.jsonl` or surfaced in the admin panel. It exists only in the response dict, which is not persisted.

---

## Summary Table

| Expectation | Reality | Match? |
|---|---|---|
| Executive is sole cognitive decision-maker | ✓ (with exceptions: stabilise override, capability selection in spine) | ⚠️ |
| 5 tones available | ✓ SILENCE-AWARE, DIRECT, JOYFUL, WITTY, CHILDLIKE-WISE | ✓ |
| 10 CAL actions | ✓ | ✓ |
| Stabilise override applied when overwhelmed | ✓ Applied, but strips Executive rationale | ⚠️ |
| Capability selection owned by Executive | ✗ Lives in spine.py | 🔴 |
| Executive output preserved through override | ✗ Full dict replacement | 🔴 |
| FREEZE_V1_LOCK respected | ✓ core executive.py untouched | ✓ |
