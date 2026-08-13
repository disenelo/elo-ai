# WP_H — Spine Implementation Plan

**Status:** READY FOR REVIEW — has cross-WP dependencies
**Gap Analysis:** `WP_H_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/07_spine_proof.md`

---

## Scope

Four changes. Two depend on other WPs completing first.

---

## Step 1 — Fix faculty call order docstring (no dependencies)

**File:** `runtime/spine/spine.py`

Update the module docstring to reflect the **authoritative** faculty call order:

```
Faculty call order:
    1. Language Faculty     — normalise, repair, intent, register
    2. Attention Faculty    — snapshot: intent, memory, emotional context
    3. Memory Faculty       — refresh memory pack if significant vault writes occurred
    4. Relationship Faculty — rapport, tier, register (read from Language)
    5. Executive Faculty    — tone, action, max_sentences (via executive.py + extension)
    6. Capabilities         — authorised tools this turn (via executive_extension.py)
    7. Embodiment Faculty   — CognitivePlan assembly
```

Remove any conflicting comment blocks elsewhere in the file that describe a different order.

**Note:** The actual call order in code is:
`Language → Attention → Memory → Relationship → Executive → Capabilities → Embodiment`

If the current code has a different order (e.g., Memory missing), updating the docstring is the target state; the code will match after Steps 2 and 3.

---

## Step 2 — Move capability selection to executive_extension.py

**Dependency:** WP-G Step 2 must be complete (executive_extension.py must exist).

**File:** `runtime/spine/spine.py`

Find `_select_capabilities()` function definition. Remove it from spine.py.

Add import:
```python
from runtime.spine.executive_extension import select_capabilities as _select_capabilities
```

Update call site to pass `exec_decision`:
```python
caps = _select_capabilities(intent, agents, exec_decision)
```

---

## Step 3 — Add _memory_faculty() to spine call sequence

**Dependency:** WP-D Step 1 must be complete (`_memory_faculty()` implemented).

**File:** `runtime/spine/spine.py`

The `_memory_faculty()` function is implemented in WP-D Step 1. Here, wire it into the spine call sequence:

```python
# After _language_faculty(), before _attention_faculty():
memory_pack = _memory_faculty(raw, session_state, current_memory_pack)
```

Confirm `current_memory_pack` is available at this point in the spine (passed in from server.py as a parameter).

---

## Step 4 — Verify Executive fragmentation resolved

After WP-G and WP-D are implemented:

- `runtime/executive.py` — core decision (frozen) ✓
- `runtime/spine/executive_extension.py` — capability selection (delegated) ✓
- `server.py` — stabilisation override (preserve-and-extend, not replace) ✓
- `runtime/spine/spine.py` — no decision logic remaining ✓

Add a comment to `runtime/executive.py` header (only the docstring/header, not the frozen logic):
```
# Extensions: runtime/spine/executive_extension.py
# Override: server.py _process_turn() stabilisation block
```

---

## Step 5 — Regression check

- Confirm spine runs without import errors after executive_extension.py import
- Confirm capability selection passes through agents on normal turns
- Confirm capability selection returns [] on ground/silence turns
- Confirm memory faculty fires per turn with the correct pack
- Confirm faculty call order in docstring matches code order exactly

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- `prompts/` — FREEZE_V1_LOCK
- CognitivePlan structure
- Any embodiment delivery logic

---

## Cross-WP dependencies

| Step | Depends On |
|---|---|
| Step 2 (move capabilities) | WP-G Step 2 (executive_extension.py created) |
| Step 3 (add memory faculty) | WP-D Step 1 (_memory_faculty implemented) |

---

## Implementation order

```
Step 1 — Fix docstring [~20 lines changed]   ← no dependencies, do first
    ↓
[Wait for WP-G Step 2 to complete]
    ↓
Step 2 — Move capabilities to executive_extension.py import [~10 lines]
    ↓
[Wait for WP-D Step 1 to complete]
    ↓
Step 3 — Wire _memory_faculty() into spine call sequence [~5 lines]
    ↓
Step 4 — Verify fragmentation resolved; add comment to executive.py header
    ↓
Step 5 — Regression test
    ↓
WP_H DONE
```
