# FROM BUILDER → BOARD — WO-EXPRESSION-POLISH-BUNDLE-001 FIX-3: Builder Voice
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-EXPRESSION-POLISH-BUNDLE-001.md
**Fix:** WO-BUILDER-VOICE-001

---

## Root cause confirmed

`expression_mode: builder` directive exists at `prompt_builder.py:540-546` but only fires when `exec_decision["expression_mode"] == "builder"`. That field wasn't being set for build/create action turns — so the directive never reached the LLM. Builder voice lived only in the `planet_voice_pool` (injected as a pool directive) where it was abstract and not acted on.

---

## Change applied

**`runtime/prompt_builder.py`** — added after line 546 (expression_mode builder block):

```python
# WO-EXPRESSION-POLISH-BUNDLE-001 FIX-3 — Builder voice directive.
_builder_action = exec_decision.get("conversation_action") or action or ""
_builder_intent = exec_decision.get("intent", "") or ""
if _builder_action in ("build", "connect", "create") or _builder_intent in ("creation", "planning", "making"):
    directive_lines.append(
        "builder-voice: Make it real. Small steps become worlds. "
        "Build before announcing. One thing, started now, beats ten things planned. "
        "If it can be built in this turn, build it."
    )
```

This is a turn-level push that fires even when `expression_mode` is not already "builder". `living_presence_spec.txt` line 445 builder register now reaches the LLM as a concrete directive.

---

## Verification

```
action='build'  intent='inquiry'       → builder_voice_fires=True  ✓
action='connect' intent='conversation' → builder_voice_fires=True  ✓
action='answer'  intent='creation'     → builder_voice_fires=True  ✓
action='answer'  intent='conversation' → builder_voice_fires=False ✓ (silent on generic turns)
```

---

## DoD

- [x] Builder directive wired to build/connect/create actions and creation/planning/making intent
- [x] Does not fire on generic conversation/answer turns
- [ ] Live expressed output with builder energy — in FIX-5 REAUDIT (T7: "i want to build something new today")

---

*Builder · 2026-09-14*
