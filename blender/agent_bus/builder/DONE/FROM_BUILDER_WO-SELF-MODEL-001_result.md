# FROM_BUILDER — WO-SELF-MODEL-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

Lean v1 `SelfModel` — eLo's observable self-knowledge snapshot, assembled per turn by a new `_self_model_faculty()` in spine.py.

### `runtime/contracts.py` — SelfModel dataclass

Fields:
- `identity` — dict of WKG foundational claims (who eLo is)
- `current_state` — dict from `AffectiveState.to_dict()`
- `autobiographical_summary` — str from wkg_context[:240]
- `limitations` — list of capability registry gaps (observed, not modelled)
- `current_goal` — str (empty in v1, filled by agency system later)
- `prediction_confidence` — float derived from `1.0 - AffectiveState.uncertainty`
- `internal_preferences` — dict (empty in v1, filled from preference learning later)

SelfModel observes — it does not decide. No Executive authority.

### `runtime/spine/spine.py` — `_self_model_faculty()`

New function assembled before `run()`. Called from `assemble_cognitive_state()`:
- Pulls WKG foundational claims for `identity`
- Converts AffectiveState to `current_state`
- Gets autobiographical summary from wkg_context[:240]
- Populates `limitations` from capability registry gaps
- Derives `prediction_confidence` from `AffectiveState.uncertainty`
- Returns `SelfModel()` — safe fallback on any exception

### `runtime/spine/plan.py`

```python
self_model: "SelfModel | None" = None
```

### `server.py`

`exec_decision` dict now carries `self_model_summary`:
```python
{
    "autobiographical_summary": ...,
    "prediction_confidence": ...,
    "limitations_count": ...,
}
```

### `runtime/prompt_builder.py` — self-model certainty register

```
prediction_confidence < 0.35 → "Be honest about what you don't know."
prediction_confidence > 0.75 → [no hedge instruction — speak with natural confidence]
```

---

## JEG CHECK — Does self-model feed back into expressed voice?

### Before:
No certainty register — eLo spoke with uniform confidence regardless of internal uncertainty.

### After:
When `uncertainty=0.8` (→ `prediction_confidence=0.2`):  
Prompt injects: `"Be honest about what you don't know."`  
eLo's response carries epistemic humility naturally rather than false confidence.

When `uncertainty=0.2` (→ `prediction_confidence=0.8`):  
No hedge injection. eLo speaks directly without false modesty.

The self-model doesn't change the decision — it changes how eLo speaks about what it knows.

---

## Test result

```
1566 passed (baseline), all pre-existing failures unchanged
```
