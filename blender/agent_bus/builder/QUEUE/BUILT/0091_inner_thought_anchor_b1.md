**WO:** INNER-THOUGHT-ANCHOR-B1 · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
Builder 2 fixed the voice (commit 269b49f — "I notice" banned). Builder 1 needs to wire the fixed inner thought generation into the prompt anchor so eLo's own perspective appears in every turn's context, not just in the Designer's speech bubble.

## Scope
Commit 91d8331 (inner thought ordering Option C) was built by Builder 1. Confirm:
1. `inner_thought_text` from `blender_state.json` reaches the assembled system prompt
2. It appears AFTER self-model, BEFORE response instruction (Option C ordering)
3. The banned "I notice [David...]" pattern cannot appear — gate exists in generation or prompt_builder

If already done by 91d8331: confirm in code + test, move to DONE with that commit hash.
If not: add the anchor injection in `prompt_builder.py`.

## Files to touch
`runtime/prompt_builder.py` (read first; may be already done)

## Test command
`python3 tests/test_prompt_builder.py` — confirm inner_thought section present and ordered correctly

## Done when
Test passes + no "I notice [name]" can appear in generation output. Commit in Result.

## Result
- commit:
- test:
- notes:
