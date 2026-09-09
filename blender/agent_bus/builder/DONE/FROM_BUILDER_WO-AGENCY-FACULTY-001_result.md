# FROM_BUILDER — WO-AGENCY-FACULTY-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

`_agency_faculty()` as a proper decision-shaping faculty. Agency is no longer a single field in significance_faculty — it is a computed value from multiple signals that actively shapes how eLo engages.

### `_agency_faculty()` — `runtime/spine/spine.py`

```python
def _agency_faculty(affective_state, execution_report, capability_count, relationship_mode) -> float:
    _base = AffectiveState.agency           # affective ground
    _er_boost = 0.12 if execution_report.completed else 0.0  # success from last turn
    _cap_boost = min(0.15, capability_count * 0.03)           # more tools = more agency
    _rel_mod: established/close → +0.08; new/in_conflict → -0.08
    return clamp(0.0, 1.0, base + boosts + modifiers)
```

Called twice per turn:
1. At `assemble_cognitive_state()` — initial computation with available signals
2. After `_conversation_faculty()` — refined with live ExecutionReport and actual plan capabilities

### Chain: CognitiveState → CognitivePlan → exec_decision → prompt_builder

- `runtime/contracts.py` — `agency_level: float = 0.6` in `CognitiveState`
- `runtime/spine/plan.py` — `agency_level: float = 0.6` in `CognitivePlan`
- `server.py` — `agency_level` in exec_decision
- `runtime/prompt_builder.py`:
  - `agency >= 0.75` → "Agency: high — initiate, propose, take the lead."
  - `agency <= 0.30` → "Agency: low — check in, defer, ask rather than assume."

---

## Intent proof

**High agency turn** (e.g., established relationship + just completed an action successfully):
- `agency_level ≈ 0.85`
- Prompt: "Agency: high — initiate, propose, take the lead. eLo has something to offer here."
- eLo proposes something David didn't ask for. Takes initiative.

**Low agency turn** (e.g., new relationship + execution failed + no capabilities available):
- `agency_level ≈ 0.25`
- Prompt: "Agency: low — check in, defer, ask rather than assume. eLo is uncertain of its ground."
- eLo asks rather than assumes. Checks before acting.

---

## Test result

```
1565 passed, pre-existing failures unchanged
```

## Commit

`515c21a`
