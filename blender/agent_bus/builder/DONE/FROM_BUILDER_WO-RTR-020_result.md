# FROM BUILDER — WO-RTR-020 RESULT

**Status:** DONE — 2026-09-08  
**Commit:** 25a07cb

## What was built

**`runtime/spine/plan.py`:** `expression_mode: str = "default"` field added to `CognitivePlan`.

**`runtime/spine/spine.py`:** Expression mode inference block added before storytelling_style inference:
```python
_BUILDER_INTENTS = {"code", "debug", "draft", "creation", "vault_write", "planning", "build"}
_BUILDER_MODE_KEYS = ("studio", "builder", "creat", "code", "debug")
if intent in BUILDER_INTENTS or mode has BUILDER_MODE_KEYS or action == "build":
    plan.expression_mode = "builder"
else:
    plan.expression_mode = "default"
```

**`server.py`:** `expression_mode` added to `exec_decision` dict.

**`runtime/prompt_builder.py`:** When `expression_mode == "builder"`, inject:
> "Expression mode: BUILDER — direct, compressed, precise. The rhythm stays eLo; the pace is focused execution. No preamble. No 'here's what we'll do'. Say the thing."

## Before / After

**Before:** All turns used the same register regardless of whether eLo was helping build something vs. being present companionship.
**After:** Code/debug/creation/planning intents → BUILDER mode → compressed, direct, focused register. Conversational turns → DEFAULT mode → full warmth register.

## Tests

1549 pass / 0 new failures.
