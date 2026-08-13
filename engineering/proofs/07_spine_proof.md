# WP-H Spine — Current Reality Review

**Status:** REVIEW COMPLETE — HIGH severity issues
**Audit date:** 2026-07-12

---

## Spine location

- Primary: `runtime/spine/spine.py`
- Supporting: `runtime/spine/plan.py` (CognitivePlan dataclass)
- Faculties called from: `runtime/spine/` directory

---

## What the Spine should do

The Spine is **assembly only**. It calls faculties in order, collects their outputs, passes them to the Executive, and packages the result as a `CognitivePlan`. It makes **no decisions** of its own.

---

## Faculty call order — declared vs actual

### Declared (spine.py header docstring):
1. Language Faculty
2. Attention Faculty
3. Memory Faculty
4. Relationship Faculty
5. Executive Faculty
6. Capability Faculty
7. Embodiment Faculty

### Declared (spine.py function comment block):
1. Language → Meaning
2. Attention → AttentionSnapshot
3. Relationship → Context
4. Executive → Decision
5. Embodiment → CognitivePlan

### Actual call order (from code, lines ~29–220):
1. `_language_faculty()`
2. `_attention_faculty()` (calls `attention.compute()`)
3. `_relationship_faculty()`
4. `_executive_faculty()` — reads pre-made decision (passed in, not computed here)
5. `_select_capabilities()` — capability selection (not a faculty call, but a decision step)
6. `_embodiment_faculty()` — builds CognitivePlan

**Discrepancy count: 3**
- Memory Faculty appears in header docstring but not in actual call sequence
- Capability Faculty appears in header but is actually `_select_capabilities()` (decision logic, not faculty)
- Call order between header and function comment is inconsistent (Attention before/after Relationship varies by source)

---

## Violations Found

### V1 — Spine makes a capability decision (HIGH)

`_select_capabilities(intent, agents)` at spine.py:194–204 is a **decision** (what tools eLo is permitted to use this turn), not an assembly step. This belongs to the Executive layer.

The spine should receive capability authorisation from Executive, not compute it. Current code creates a second implicit decision-maker at the assembly layer.

**Resolution:** Create `runtime/spine/executive_extension.py` for capability delegation. OR: formally document `_select_capabilities()` as "Executive-delegated" and enforce it never branches on cognition.

### V2 — Executive responsibility fragmented (HIGH)

The Executive decision is made in three locations:
1. `runtime/executive.py` (core: tone, action, sentences) — FROZEN
2. `server.py` (stabilisation override) — replaces dict
3. `spine.py` (`_executive_faculty()` — loads pre-made decision + selects capabilities)

This fragmentation means no single file owns the complete Executive output. Changes to Executive behaviour require auditing three files.

**Resolution:** The stabilisation override should be consolidated. Since executive.py is frozen, the override can live in a clearly marked `runtime/spine/executive_extension.py` with explicit comments tracing back to executive.py.

### V3 — Memory Faculty missing from spine call sequence (HIGH)

The spine header claims Memory Faculty is called. The actual code has no `_memory_faculty()` call. Memory is loaded at session start in server.py and injected as a parameter — the spine never refreshes it.

**Resolution (per WP-D):** Add `_memory_faculty()` to spine.py that:
- Checks if significant vault writes have occurred this turn
- Refreshes the memory pack if significance > 0.70
- Returns the (possibly refreshed) memory pack to subsequent faculties

### V4 — Faculty order inconsistency across documentation (MEDIUM)

- `spine.py` header docstring: Language → Attention → Memory → Relationship → Executive → Capability → Embodiment
- `spine.py` function comments: Language → Meaning → Attention → Relationship → Executive → Embodiment
- Actual call order: Language → Attention → Relationship → Executive → Capabilities → Embodiment

All three disagree. The docstring is the authoritative spec; the code is the ground truth. Pick one.

---

## CognitivePlan — confirmed fields

```python
@dataclass
class CognitivePlan:
    response: str
    action: str
    tone: str
    max_sentences: int = 3
    motion: dict = field(default_factory=dict)
    expression: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)
    gaze: dict = field(default_factory=dict)
    agents_used: list = field(default_factory=list)
    rationale: str = ""
```

**Status:** Structure is correct and matches architecture spec. All embodiments consume this correctly.

---

## Invariant 14 Compliance — Spine assembles, never decides

**Status: VIOLATED (V1, V2)**

The spine currently makes at least one decision (`_select_capabilities()`) and is the site of the fragmented Executive override path. True assembly-only status requires resolving V1 and V2.

---

## Summary Table

| Expectation | Reality | Match? |
|---|---|---|
| Faculty call order documented and correct | ✗ Three conflicting sources | 🔴 |
| Spine does not make decisions | ✗ Capability selection in spine | 🔴 |
| All faculties called per cycle | ✗ Memory Faculty missing from spine | 🔴 |
| CognitivePlan structure correct | ✓ Matches spec | ✓ |
| Executive fragmentation resolved | ✗ Three files own Executive logic | 🔴 |
| Embodiment delivery correct | ✓ CognitivePlan consumed correctly | ✓ |
