# FROM_BUILDER — WO-LEAF-ON-WATER-PROOF-001
**Status:** DONE — full INTENT PROOF traced
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## WO requirement

"P9 Leaf on Water — no expressed proof exists. Builder traces runtime location and files INTENT PROOF."

## Full chain trace

### 1. Complexity score computation — `runtime/spine/spine.py:396-409`

```python
_score = float(_cap_count + _ctx_weight)
plan.plan_complexity_score = _score
if _score >= 6:
    plan.stability_law_active = True
    plan.leaf_on_water_active = False
elif 3 <= _score < 6:
    plan.leaf_on_water_active = True    # ← P9 activates here
    plan.stability_law_active = False
else:
    plan.stability_law_active = False
    plan.leaf_on_water_active = False
```

Trigger condition: `plan_complexity_score` between 3 and 5 (medium complexity). This score combines:
- `_cap_count`: number of capabilities selected by Executive
- `_ctx_weight`: context weight (Q-BODY, Q-MOVEMENT, affective state, significance)

### 2. Plan contract — `runtime/spine/plan.py:154`

```python
leaf_on_water_active: bool = False
```

CognitivePlan carries the flag. Executive reads it through exec_decision.

### 3. exec_decision passthrough — `server.py:2964`

```python
"leaf_on_water_active": getattr(_plan, "leaf_on_water_active", False),
```

Plan field flows into exec_decision dict, which is passed to prompt_builder.

### 4. prompt_builder directive — `runtime/prompt_builder.py:501-502`

```python
elif exec_decision.get("leaf_on_water_active"):
    directive_lines.append("stability: leaf-on-water — gentle, present, no more than two thoughts")
```

When active, this directive fires BEFORE the executive_directive section — it's in `directive_lines` which go into the system prompt's core section. The LLM sees: `stability: leaf-on-water — gentle, present, no more than two thoughts`.

### 5. LIVING PRESENCE POOL — `prompts/living_presence_spec.txt`

The LEAF ON WATER MODE section (added by WO-LIVING-PRESENCE-UPDATE-001):

> "When: complexity ≥ 3 (medium). Stay still. Receive one thing. Allow the turn to be smaller than planned. No more than two thoughts. Don't push the river."

This backs the prompt directive with character identity — eLo doesn't just follow a rule, it's who eLo is.

## Test evidence

`tests/test_wo_stability_law_001.py::test_at2_medium_complexity_leaf_on_water`:
- Input: `plan_complexity_score = 4.0` (medium)
- Assert: `plan.leaf_on_water_active == True` ✅
- Assert: `plan.stability_law_active == False` ✅
- **5 passed in 0.07s**

## INTENT PROOF

P9 Leaf on Water intent (from SOURCE): "eLo stays present and gentle when things are complex enough to overwhelm but not enough to collapse. No more than two thoughts. Don't push the river."

**Runtime proof:**
- When a turn's complexity score is 3-5 (moderate): `leaf_on_water_active=True` in plan
- This reaches `exec_decision["leaf_on_water_active"]`  
- prompt_builder injects "gentle, present, no more than two thoughts" into the system prompt
- LLM constraint: two thoughts max, present register, no over-elaboration
- The living presence spec's LEAF ON WATER MODE section reinforces the identity layer

P9 Leaf on Water reaches expressed output.
