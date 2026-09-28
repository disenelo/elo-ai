# BUILDER RESULT — GAP-05: ambient_thought() SPEAK path through One Brain
Date: 2026-09-07
Status: DONE — path confirmed wired + expression fields added

---

## Dispatch claim

> "`ambient_thought()` SPEAK path uses a custom LLM prompt that bypasses `prompt_builder`, the voice register, and the response gate."

---

## Finding: dispatch claim is PARTIALLY CORRECT

The path was already wired through `build_prompt()` and `elo_response_gate()`.
The gap was real but narrower: the ambient exec_decision was missing the expression fields
added in WO-EXEC-DECISION-FIELDS-001, so ambient turns ran through the right pipeline
but with a thinner exec_decision than conversational turns.

---

## Code trace — server.py SPEAK path

```
ambient_thought()
  → vessel_phase == "SPEAK"
  → _amb_plan = await plan_speech(...)               # line ~1155
  → _amb_exec_decision = { ... }                     # line ~1165
  → _speak_result = await build_prompt(              # line 1186
        _amb_exec_decision, world_dict, ...
    )
  → _amb_system = _speak_result["system_prompt"]     # line 1197
  [fallback at line 1199 only fires if build_prompt raises]
  → response = await llm_call(_amb_system, ...)      # line ~1220
  → _speak_text = elo_response_gate(                 # line 1245
        _speak_text, current_turn_input="ambient"
    )
```

Both `build_prompt()` (prompt_builder, voice register, full faculty chain) and
`elo_response_gate()` are on the SPEAK path. The fallback custom prompt at line 1199
(`"You are eLo..."`) only fires when `build_prompt` raises an exception — not normally.

---

## Gap found during investigation: missing expression fields in ambient exec_decision

The ambient `_amb_exec_decision` had action/intent/tone/affective_state/self_model_summary
but was missing the expression fields consumed by `prompt_builder` in WO-EXEC-DECISION-FIELDS-001:

- `storytelling_style`
- `personality_traits` / `personality_baseline`
- `ccm_context`
- `significance_score`
- `relationship_mode`
- `turn_mode`
- `agency_level`
- `vessel_phase`

Without these, `build_prompt()` ran with a degraded exec_decision on all ambient SPEAK turns.

---

## Fix applied — server.py (ambient exec_decision block)

Added all missing expression fields to the `_amb_exec_decision` dict, each using
`getattr(_amb_plan, field, default)` so they're populated when the plan has them
or fall back to sensible defaults:

```python
# GAP-05 / WO-EXEC-DECISION-FIELDS-001: expression fields — same as conversational turns
"storytelling_style":    getattr(_amb_plan, "storytelling_style", "direct"),
"personality_traits":    getattr(_amb_plan, "personality_traits", {}),
"personality_baseline":  getattr(_amb_plan, "personality_baseline", {}),
"ccm_context":           getattr(_amb_plan, "ccm_context", {}),
"significance_score":    getattr(_amb_plan, "significance_score", 0.0),
"relationship_mode":     getattr(_amb_plan, "relationship_mode", ""),
"turn_mode":             getattr(_amb_plan, "turn_mode", "EXPLORE"),
"agency_level":          getattr(_amb_plan, "agency_level", 0.6),
"vessel_phase":          getattr(_amb_plan, "vessel_phase", "EXPRESS"),
```

---

## ATs

| AT | Description | Result |
|---|---|---|
| AT-1 | SPEAK path calls build_prompt() | ✅ server.py:1186 confirmed |
| AT-2 | SPEAK path calls elo_response_gate() | ✅ server.py:1245 confirmed |
| AT-3 | Fallback prompt is exception-only | ✅ line 1199, only on build_prompt raise |
| AT-4 | Expression fields added to ambient exec_decision | ✅ server.py edit applied |
| AT-5 | executive.py NOT touched | ✅ FREEZE_V1_LOCK clean |
| AT-6 | living_presence_spec.txt NOT touched | ✅ FREEZE clean |

---

## What was NOT present (and therefore not a gap)

- A second LLM call path bypassing build_prompt — does not exist
- A legacy custom system prompt on the normal SPEAK path — does not exist; the `"You are eLo..."` string at line 1199 is only the exception fallback

---

— Builder · 2026-09-07
