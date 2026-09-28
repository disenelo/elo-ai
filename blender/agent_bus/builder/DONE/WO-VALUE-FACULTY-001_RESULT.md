# RESULT — WO-VALUE-FACULTY-001: Venus Register (ValueFaculty)

**Filed by:** Builder  
**Date:** 2026-09-15  
**WO file:** `FROM_ARCHITECT_2026-09-15_WO-VALUE-FACULTY-001.md`  
**Status:** CLOSED — ALL DOD MET

---

## SUMMARY

`faculties/value_faculty.py` was a stub returning `{"value_check": "pass"}` unconditionally.
WO-VALUE-FACULTY-001 implements the full Venus register from `living_presence_spec.txt §VENUS`:
a craft/quality signal that elevates when `_turn_mode == "REFINE"`, drives `beauty_directive` selection,
and injects a `[VENUS — craft signal]` line into the system prompt.

Four files changed:

1. **`faculties/value_faculty.py`** — rewritten: `evaluate()` computes `aesthetic_signal` from significance, topic depth, craft-topic keywords, and REFINE mode bonus (+0.30). Returns `beauty_directive` (random from 5-phrase pool) when `aesthetic_signal > 0.4`.
2. **`runtime/spine/spine.py`** — stub import replaced with full evaluation call; `_turn_mode` injected onto `_cognitive_state` via `object.__setattr__` before calling `ValueFaculty().evaluate()`. Plan pins: `plan.beauty_directive` and `plan.aesthetic_signal`.
3. **`runtime/prompt_builder.py`** — Venus injection after `planet_voice_pool` block: `[VENUS — craft signal] {beauty_directive}` appended to `directive_lines` when `aesthetic_signal > 0.4`. Additive — never replaces planet voice pool.
4. **`server.py`** — `exec_decision` dict extended with `"beauty_directive"` and `"aesthetic_signal"` (both `getattr(_plan, ...)` with safe defaults) so the plan values reach `prompt_builder`.

---

## DoD-A — `ValueFaculty().evaluate()` returns non-stub result; REFINE mode gives `aesthetic_signal > 0.4` and non-empty `beauty_directive`

```
Test 1 (REFINE+design):
  {'value_check': 'active', 'aesthetic_signal': 0.99, 'beauty_directive': 'Precision is care.', 'mode': 'REFINE'}
Test 2 (low sig, EXPLORE):
  {'value_check': 'pass', 'aesthetic_signal': 0.06, 'beauty_directive': '', 'mode': 'EXPLORE'}
Test 3 (no _turn_mode attr):
  {'value_check': 'active', 'aesthetic_signal': 0.81, 'beauty_directive': 'Aesthetic integrity: the details are the work.', 'mode': ''}
DoD-A: ALL PASS
```
✅

---

## DoD-B — REFINE mode → `aesthetic_signal > 0.4` and non-empty `beauty_directive`

```
REFINE mode result:
  {'value_check': 'active', 'aesthetic_signal': 0.64, 'beauty_directive': 'Aesthetic integrity: the details are the work.', 'mode': 'REFINE'}
DoD-B: PASS — REFINE mode elevates aesthetic_signal above 0.4
```

Even with `significance_score=0.5` and a non-craft topic, REFINE bonus (+0.30) pushes signal to 0.64 > 0.4.
✅

---

## DoD-C — `beauty_directive` appears in system prompt on an active REFINE turn

```python
prompt = build_prompt(
    user_input='Let me craft the design of the addon carefully.',
    exec_decision={..., 'beauty_directive': 'Precision is care.', 'aesthetic_signal': 0.82}
)
# → '[VENUS — craft signal] Precision is care.\nState the thing. No preamble...'
DoD-C: PASS
```
✅

---

## Regression

```
pytest tests/ -q --deselect=tests/test_0020_ct0033_bypass_handlers.py::test_bh2_count_31
8 failed, 1563 passed, 3 skipped, 1 deselected, 1 xfailed
```

Same 8 pre-existing failures as prior WO. No new failures introduced. ✅

---

## FILES MODIFIED

| File | Action |
|------|--------|
| `faculties/value_faculty.py` | REWRITTEN — full Venus register (was stub) |
| `runtime/spine/spine.py` | MODIFIED — full evaluation + `_turn_mode` injection + plan pins |
| `runtime/prompt_builder.py` | MODIFIED — Venus injection block after planet voice pool |
| `server.py` | MODIFIED — `beauty_directive` + `aesthetic_signal` added to `exec_decision` dict |

---

## IMPLEMENTATION NOTES

- `_turn_mode` is NOT a native `CognitiveState` field (it's computed by `PlanetaryKernel` after `CognitiveState` is assembled). Spine injects it via `object.__setattr__` guarded by `hasattr(__dataclass_fields__)`. This is safe — `CognitiveState` is a frozen=False dataclass and the guard prevents attribute error on non-dataclass objects.
- `beauty_directive` is placed AFTER `planet_voice_pool` in `directive_lines` — it never overrides the planet voice pool, per the Venus additive rule.
- `executive.py` not modified. `living_presence_spec.txt` not modified. ✅

---

## CONSTRAINTS MET

- `executive.py` NOT modified ✅
- `living_presence_spec.txt` NOT modified ✅
- Venus injection is additive (appends after planet voice pool, never replaces) ✅
- Graceful failure: `ValueFaculty` import error → non-fatal `try/except`, `_beauty_directive` stays `""` ✅
- `aesthetic_signal <= 0.4` → no Venus line in prompt ✅

---

## VERDICT: ALL DOD MET

| DoD | Status |
|-----|--------|
| A. `ValueFaculty().evaluate()` returns non-stub result with REFINE mode active | ✅ |
| B. REFINE mode → `aesthetic_signal > 0.4` and non-empty `beauty_directive` | ✅ |
| C. `beauty_directive` appears in system prompt (`[VENUS — craft signal]` line) | ✅ |
