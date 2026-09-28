# FROM BUILDER → BOARD — WO-EXPRESSION-POLISH-BUNDLE-001 FIX-2: Inner Child Activation
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-EXPRESSION-POLISH-BUNDLE-001.md
**Fix:** WO-INNER-CHILD-ACTIVATION-001

---

## Root cause confirmed

Inner child was firing only when `curiosity > 0.7`. BA-02 (significance weights unresolved) keeps curiosity at low values (~0.3) on most turns. The wiring exists in `prompt_builder.py:518` but the activation gate never opened.

---

## Change applied

**`runtime/spine/spine.py:451-462` (after fix):**

```python
# WO-EXPRESSION-POLISH-BUNDLE-001 FIX-2: second trigger path — does not require curiosity > 0.7.
_lang_intent = (language or {}).get("intent", "") or ""
_inner_child_ccm = _lang_intent in ("creative_discussion", "brainstorming", "humour", "exploration")
_raw_lower = (raw or "").lower()
_inner_child_raw = any(p in _raw_lower for p in (
    "what if", "imagine if", "could you", "what would", "dream", "wonder",
))
plan.cognitive_mode_inner_child = bool(
    _curiosity > 0.7
    or (_is_play and _is_dream)
    or _inner_child_ccm
    or _inner_child_raw
)
```

Uses `language` dict (available at line 451) for CCM intent instead of `cognitive_state.intent_category` (which doesn't exist). `_ccm_context` is populated at line 1056 (after this block) so can't be referenced here.

---

## Verification

```
Input: "what if eLo could dream about the worlds he visits"
_lang_intent: 'creative_discussion'
_inner_child_ccm: True    (creative_discussion in trigger set)
_inner_child_raw: True    ("what if" matched)
_curiosity: 0.3           (below 0.7 — old path would NOT have fired)
cognitive_mode_inner_child: True  ✓

Prompt builder at runtime/prompt_builder.py:518 consumes cognitive_mode_inner_child → fires inner child directive.
```

---

## What inner child directive fires

`prompt_builder.py:518`: when `exec_decision["cognitive_mode_inner_child"]` is True, the inner child directive is added to the system prompt, producing wonder-mode energy, curiosity-first approach, movement before conclusions.

---

## DoD

- [x] `cognitive_mode_inner_child=True` confirmed for "what if eLo could dream..." input
- [x] Fires WITHOUT requiring curiosity > 0.7
- [x] prompt_builder.py:518 confirmed to consume the field
- [ ] Expressed output with wonder energy — in FIX-5 REAUDIT (needs live server)

---

*Builder · 2026-09-14*
