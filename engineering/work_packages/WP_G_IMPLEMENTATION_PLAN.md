# WP_G — Executive Faculty Implementation Plan

**Status:** READY FOR REVIEW
**Gap Analysis:** `WP_G_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/06_executive_proof.md`

---

## Scope

Two bounded changes. Nothing touches FREEZE_V1_LOCK.

1. Fix stabilisation override — extend instead of replace
2. Create `executive_extension.py` and move capability selection into it

WP-H depends on Step 2 for its own GAP 1 fix.

---

## Step 1 — Fix stabilisation override in server.py

**File:** `server.py`

Find the stabilisation override block (currently replaces entire `exec_decision` dict):

**Current code (to replace):**
```python
if exec_decision.get("stabilise"):
    exec_decision = {"action": "ground", "tone": "SILENCE-AWARE", "max_sentences": 2, "stabilise": True}
```

**Replacement:**
```python
if exec_decision.get("stabilise"):
    exec_decision = dict(exec_decision)          # preserve all original fields from executive.py
    exec_decision.update({
        "action":             "ground",
        "tone":               "SILENCE-AWARE",
        "max_sentences":      2,
        "overridden_by_safety": True,
        "original_action":    exec_decision.get("action"),
        "original_tone":      exec_decision.get("tone"),
    })
```

**Result:** `exec_decision["rationale"]` and any other frozen Executive fields are preserved. The override is recorded with `overridden_by_safety: True` and original values for audit.

---

## Step 2 — Create executive_extension.py with capability selection

**New file:** `runtime/spine/executive_extension.py`

```python
"""
runtime/spine/executive_extension.py — Executive-Delegated Capability Selection

Capability selection is an Executive decision (what eLo is permitted to use this turn).
runtime/executive.py is frozen (FREEZE_V1_LOCK). This module is the designated extension
point for Executive-layer decisions that cannot go in the frozen file.

Architecture authority: WP_G_IMPLEMENTATION_PLAN.md, engineering/proofs/06_executive_proof.md
"""
from __future__ import annotations


def select_capabilities(intent: str, agents: list, exec_decision: dict) -> list:
    """
    Determine which capabilities eLo is authorised to use this turn.

    Delegated from Executive context: exec_decision["action"] and "tone" inform
    which tools are appropriate. Intent and proposed agents are inputs, not the authority.

    Returns: list of authorised capability names.
    """
    action = exec_decision.get("action", "answer")
    tone = exec_decision.get("tone", "DIRECT")

    # Silence-aware turns: no tools — eLo is present, not active
    if tone == "SILENCE-AWARE" or action == "silence":
        return []

    # Ground action: no external tools — eLo grounds without external data
    if action == "ground":
        return []

    # All other turns: pass through proposed agents (already vetted by agent_router)
    return [a[0] for a in agents if a]
```

**Update spine.py:**

Replace the inline `_select_capabilities()` call with:
```python
from runtime.spine.executive_extension import select_capabilities as _select_capabilities
```

And update the call site to pass `exec_decision`:
```python
caps = _select_capabilities(intent, agents, exec_decision)
```

---

## Step 3 — Regression check

- Confirm stabilisation override fires on overwhelmed input (result: `action=ground`, `tone=SILENCE-AWARE`)
- Confirm `exec_decision["rationale"]` is preserved after override
- Confirm `overridden_by_safety: True` is set when override fires
- Confirm capability selection returns `[]` for silence and ground actions
- Confirm capability selection passes through agents correctly on normal turns

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- `prompts/` — FREEZE_V1_LOCK
- Any LLM routing or response generation
- The 5 tones or 10 CAL actions
- Any other spine logic

---

## Implementation order

```
Step 1 — Fix stabilisation override in server.py [~5 lines]
    ↓
Step 2 — Create executive_extension.py; update spine.py import [~40 lines new, ~5 lines changed]
    ↓
Step 3 — Regression test
    ↓
WP_G DONE — WP_H GAP 1 can now proceed
```
