# FROM_BUILDER — WO-OVERLOAD-PROTOCOL-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

Overload detection + REDUCE TO ONE LINE response compression. When eLo detects cognitive overload, it collapses to one focus, one action, one direction.

### Overload conditions (three triggers)

```python
_overload = (
    (_ovl_sig >= 0.90)                              # significance overload
    or (_ovl_tension > 0.80 and _ovl_agency < 0.30) # tension + low agency
    or (_ovl_threads >= 3)                           # 3+ competing context threads
)
```

### When overload detected (`runtime/spine/spine.py`)

- `plan.overload_protocol = True`
- `plan.vessel_phase = "STABILISE"` (forced)
- `plan.stability_law_active = True`
- Logged at INFO with signal values

### Inner child runtime

When `vessel_phase == "FEEL"` and no overload: `plan.inner_child_mode_active = True`

### `runtime/spine/plan.py`

Two new fields:
- `overload_protocol: bool = False`
- `inner_child_mode_active: bool = False`

### `server.py`

Both fields in exec_decision.

### `runtime/prompt_builder.py`

Overload path injects:
```
OVERLOAD MODE: Reduce to ONE line. One focus. One action. One direction.
What is the next smallest usable action? What is true right now? What can be removed?
```

Inner child path injects:
```
inner-child active: Try it once. Move first, understand after. Small test is enough.
```

---

## Intent proof (source verbatim)

> "When overloaded, eLo should collapse: many ideas / competing branches / emotional noise / excessive options into: one focus / one action / one direction."

When David presents a complex multi-branch problem and significance is high (≥0.90), the prompt carries exactly this: ONE clear direction, no elaboration, no options list.

When eLo is uncertain and vessel=FEEL, the inner child fires: "Try it once. Move first." — this is the "Move first" language required by the WO spec.

---

## Test result

```
1565 passed, pre-existing failures unchanged
```

## Commit

`48962ef`
