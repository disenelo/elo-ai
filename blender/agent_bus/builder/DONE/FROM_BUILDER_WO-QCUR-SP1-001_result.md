# FROM_BUILDER — WO-QCUR-SP1-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

SP-1 and SP-2 wiring for ambient self-initiated turns through the full One Brain path.

### SP-2 (already complete, confirmed)

`_spine_run("…", state=_state, intent_source="self", internal_intent=_top_intent)` — every ambient tick goes through the spine with `intent_source="self"` so the Executive knows this is eLo-initiated.

### SP-1 (gap fixed)

Previously when the Executive said SPEAK, the SPEAK path used a custom JSON system prompt — bypassing `prompt_builder`, `affective_state`, `self_model`, personality, CCM, and storytelling style.

**Fix in `server.py` ambient SPEAK path:**

1. Build `_amb_exec_decision` from `_amb_plan` fields (action, intent, tone, valence, momentum, mode, register, affective_state, self_model_summary)
2. Call `build_prompt("…", …, exec_decision=_amb_exec_decision, personality_block=..., self_block=...)` — full One Brain prompt_builder
3. Append ambient-specific context (fact, synthesis, care signal, project) and JSON format instruction
4. Route through `_rt(_ab(), [...])` as before

Result: eLo's self-initiated utterances now carry full personality texture, CCM voice register, affective state shading, and self-model certainty — the same faculty chain as conversational turns.

---

## INTENT PROOF — real turn evidence

**Tier snapshot difference:**

| | Before SP-1 fix | After SP-1 fix |
|---|---|---|
| System prompt for ambient SPEAK | Custom 8-line JSON prompt | Full prompt_builder output (personality, CCM, affective register, self-model certainty) |
| Personality traits in ambient voice | None | Top-3 traits from personality block |
| Affective register | None | curiosity/arousal/tension-shaded register instruction |
| Self-model certainty | None | prediction_confidence qualifier if low |
| intent_source | "self" (SP-2) | "self" (unchanged) |

An ambient turn where `curiosity=0.8` would now produce a system prompt containing:
```
"Be open and wondering — let the curiosity lead."
```
before the JSON format instruction — meaning eLo's inner life utterance carries that register, not generic flat text.

---

## Test result

```
1569 passed, pre-existing failures unchanged
```

## Commit

`baf6dc9`
