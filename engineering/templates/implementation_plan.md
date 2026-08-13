# Implementation Plan — [Work Package Name]

**Work Package:** WP_[X] — [Name]
**Engineer Role:** Runtime Engineer / Systems Integrator
**Date:**
**Status:** DRAFT / APPROVED

---

## 1. Objective

One sentence. What will exist at the end of this implementation that does not exist now?

---

## 2. Prerequisites

What must be done before the first line of code is written?

- [ ] Architecture Review complete
- [ ] Gap Analysis complete
- [ ] Runtime Design complete
- [ ] Frozen phases confirmed passing regression
- [ ]

---

## 3. Implementation Sequence

Ordered list. Each step is a discrete, testable unit of work. Do not combine steps.

| Step | Description | File(s) | Depends On |
|---|---|---|---|
| 1 | | | — |
| 2 | | | Step 1 |
| 3 | | | Steps 1, 2 |

---

## 4. Interfaces and Contracts

What are the exact inputs and outputs of each new component?

### [Component Name]

**Input:**
```
{
  "field": "type — description"
}
```

**Output:**
```
{
  "field": "type — description"
}
```

**Invariants:**
- This component never decides. It observes and reports.
- Empty input → empty output (no fallback behaviour).
- Never raises. All failures are silent and logged.

---

## 5. Runtime Flow

```
[Input Source]
      ↓
[Component A]
      ↓
[Component B — reads A output]
      ↓
[Executive — sole decision maker]
      ↓
[Output / Embodiment]
```

Describe any branching. Describe what happens when any component fails (silent? fallback? logged?).

---

## 6. Files Created or Modified

| File | Action | Purpose |
|---|---|---|
| `path/to/file.py` | CREATE / MODIFY | |

---

## 7. What Is Not Changing

Explicitly list what this implementation does NOT touch. This is as important as what it does touch.

- `runtime/executive.py` — FREEZE_V1_LOCK, not modified
- `prompts/` — FREEZE_V1_LOCK, not modified
-

---

## 8. Rollback Plan

If implementation fails validation, exactly what is reverted?

1. Delete or revert:
2. Restore from:
3. Confirm regression baseline passes.

---

## 9. Acceptance Criteria

This implementation is complete when:

- [ ]
- [ ]
- [ ] All existing regression tests pass
- [ ] No second decision-maker introduced
- [ ] Silence is valid output (nothing fires when input is empty)

---

## 10. Reviewer Sign-Off

| Role | Name | Date | Approved? |
|---|---|---|---|
| Architecture Engineer | | | |
| Runtime Engineer | | | |
