# WP_G — Executive Faculty Gap Analysis

**Status:** REVIEW COMPLETE — 2 HIGH violations
**Proof document:** `engineering/proofs/06_executive_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| Executive is the sole cognitive decision-maker | ⚠️ Core: ✓. Stabilisation override: replaces dict. Capability selection: in spine | 🔴 GAP |
| Executive output preserved through pipeline | ✗ Stabilisation override replaces entire dict | 🔴 GAP |
| Capability selection owned by Executive layer | ✗ `_select_capabilities()` in spine.py | 🔴 GAP |
| 5 tones: SILENCE-AWARE, DIRECT, JOYFUL, WITTY, CHILDLIKE-WISE | ✓ | ✓ Match |
| 10 CAL actions | ✓ | ✓ Match |
| Stabilisation override triggers on overwhelm | ✓ Applied correctly | ✓ Match |
| FREEZE_V1_LOCK respected | ✓ core executive.py untouched | ✓ Match |
| Executive rationale propagated | ✗ Discarded by stabilisation override | ⚠️ |

---

## Gaps requiring implementation

### GAP 1 — Stabilisation override strips Executive output (🔴 HIGH)

**What exists:** `server.py` — when `exec_decision["stabilise"] == True`:
```python
exec_decision = {"action": "ground", "tone": "SILENCE-AWARE", "max_sentences": 2, "stabilise": True}
```

This replaces the entire dict. All fields from the frozen `executive.py` output are discarded:
- `rationale` — the Executive's reasoning, lost
- Any diagnostic or confidence fields, lost

**What architecture expects:** The override changes the action and tone (correct), but the Executive's original reasoning should be preserved as an audit trail. The override should extend, not replace.

**Resolution:**
```python
if exec_decision.get("stabilise"):
    exec_decision = dict(exec_decision)  # preserve all original fields
    exec_decision.update({
        "action": "ground",
        "tone": "SILENCE-AWARE",
        "max_sentences": 2,
        "overridden_by_safety": True,
        "original_action": exec_decision.get("action"),
        "original_tone": exec_decision.get("tone"),
    })
```

**Implementation scope:** `server.py` (~5 lines changed)

---

### GAP 2 — Capability selection in spine, not Executive (🔴 HIGH)

**What exists:** `spine.py:194–204` `_select_capabilities(intent, agents)` — determines what tools eLo can use this turn. This is a **decision**, not an assembly step.

**What architecture expects:** The Executive layer decides capability authorisation. The spine assembles and delivers.

**Constraint:** `runtime/executive.py` is FROZEN. Cannot add capability selection there.

**Resolution:**
- Create `runtime/spine/executive_extension.py`
- Move `_select_capabilities()` into it as `select_capabilities(intent, agents, exec_decision)`
- Spine.py imports from executive_extension and calls it explicitly after `_executive_faculty()`
- The module docstring makes clear: "Executive-delegated capability selection — not a spine decision. Authorised by exec_decision output."

**Implementation scope:** New file `runtime/spine/executive_extension.py` (~30 lines), `runtime/spine/spine.py` (replace inline call with import)

---

## What already satisfies the architecture

- 5 tones: Correct and frozen
- 10 CAL actions: Correct and frozen
- Stabilisation trigger (overwhelmed state): Correct
- Executive called before spine assembly: Correct
- Executive does not generate text: Correct
- FREEZE_V1_LOCK: Respected

---

## Implementation priority order

1. **GAP 1 first** — the dict replacement is a data loss issue. Preserving rationale is important for diagnostics and the 01_runtime_ownership_proof.md.
2. **GAP 2 second** — create executive_extension.py and move capability selection. Cleans up spine architecture.

---

## Invariants unblocked

| Invariant | Status Now | Status After |
|---|---|---|
| 05 — Executive owns final decision | ⚠️ PARTIAL (override strips output, capability in spine) | ✓ (after GAP 1 + GAP 2) |
| Executive output audit trail preserved | ✗ | ✓ (after GAP 1) |
