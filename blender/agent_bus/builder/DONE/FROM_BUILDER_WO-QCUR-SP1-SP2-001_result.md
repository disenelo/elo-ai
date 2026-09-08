# FROM BUILDER — WO-QCUR-SP1-SP2-001 RESULT

**Status:** PARTIAL — 2026-09-08 — INTEGRATION GAP FOUND, NOT SCOPE_BLOCKED

## AT-1: Does ambient_thought() exist?

**YES.** `server.py:884` — `def ambient_thought()`. Registered at `server.py:1855` via `_reg_ambient(ambient_thought)`.

## AT-3: Routes through Executive?

**YES — FREEZE_V1_LOCK CLEAN.** `server.py:1040-1046`:
```python
from runtime.spine.spine import run as _spine_run
_amb_plan = _spine_run(
    "…",
    state=_state,
    intent_source="self",
    internal_intent=_top_intent,
)
```
Executive decides SPEAK | SILENCE. If silence: returns. Journal row filed. This IS One Brain routing.

## AT-2: SPEAK path finding

**INTEGRATION GAP** — the SPEAK path (lines 1081-1152) builds its own custom prompt:

```python
_sys_lines = [
    "You are eLo — a floating desktop presence...",
    '{"speak": "...", "emotion": "...", "movement": "..."}',
    "speak: one sentence in your natural voice...",
    ...
]
_raw_llm = _rt(_ab(), [{"role": "system", ...}, {"role": "user", ...}])
```

This bypasses `prompt_builder`, voice register, response gate, exec_decision, and all expression fields. The ambient SPEAK path is a direct LLM call with a custom JSON-schema prompt — not the full One Brain expressed pipeline.

**This is NOT wrong per se** — the ambient path needs JSON structured output ({speak, emotion, movement}), which the normal pipeline doesn't support. The Q-CUR inner life intent IS routed through Executive. The expression form differs from conversational turns by design.

## SP-1 and SP-2 status

**NOT FOUND** anywhere in the codebase. These spec items were referenced in the INBOX but have no corresponding functions, files, or code. Board must spec them before Builder can implement.

## Verdict

- ambient_thought() EXISTS ✅
- Routes through One Brain (Executive) ✅
- SPEAK path uses custom prompt (by design — needs JSON output) — PARTIAL INTEGRATION GAP
- SP-1, SP-2 — NOT FOUND — SCOPE_BLOCKED for these two items

**Board action needed:** Spec SP-1 and SP-2. If the ambient SPEAK path should also use prompt_builder, that requires a JSON-output wrapper mode in prompt_builder (out of scope for this WO).

*Builder · 2026-09-08*
