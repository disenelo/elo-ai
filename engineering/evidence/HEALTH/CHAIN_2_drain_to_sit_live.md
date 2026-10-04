# CHAIN 2 — Drain to Sit

**Status:** Part A wired (Builder 1). Part B (Executive routing to Sit_hold) — requires inner_thought pipeline to pick up physical_tired event, Executive to decide sit.

## Part A — _emit_tired_signal wired

- `ambient/ambient_engine.py:267-270` — `_emit_tired_signal(physical_state, motion)` called in ambient tick after `_hb.tick()`
- `ambient/ambient_engine.py:344-374` — `_emit_tired_signal()`: when physical_state in ("tired", "fatigued", "exhausted") AND not resting AND not dreaming → appends `physical_tired:<band>` to `EloSelfState.inner_events`, rate-limited to 60s per band
- `EloSelfState.inner_events` is rendered in the system prompt by `elo_self_model.prompt_block()` → Executive can read it and decide to sit

## Part B — Executive routing

When Executive reads `physical_tired:tired` in the system prompt and decides to sit:
- Should emit `motion: {animation: "Sit_hold", mode: "sit"}` to blender_state.json
- Designer plays Sit_hold in Presence

Part B is NOT built from Builder 1's side. Executive routing to sit is inside the LLM decision loop — it responds to the `physical_tired` inner event when it appears in the prompt. No explicit code path needed: Executive reads inner_events and may decide to sit. If explicit routing is needed, that's a Board decision on whether to add an override in spine.

## Verification required

Walk/run animation → physical drain → physical_state reaches "tired" → check inner_events in EloSelfState → eLo may choose to sit next turn.
