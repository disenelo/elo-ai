**WO:** ROOT-2 · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
eLo retrieves what he stored from prior sessions and uses it in his response. David says "where is my studio?" → eLo says "Hackney" without being re-told.

## Scope — exactly this, nothing more
- In `runtime/prompt_builder.py`: read `executive_ctx.autobiographical_summary`. If non-empty, inject as a section in the system prompt:
  ```
  ## What I know from our history (retrieved, treat as verified fact)
  <autobiographical_summary>
  [These are specific things I recorded from our sessions. Do not contradict or ignore them in favour of a general answer.]
  ```
- In `runtime/spine/spine.py` line 805: the truncation `[:240]` loses most of the WKG context. Raise to `[:800]` minimum.
- In `assets/living_presence_spec.txt` (or wherever the persona prompt lives): add one line — "The section 'What I know from our history' contains verified facts from prior sessions. Treat them as ground truth."

## Files to touch
`runtime/prompt_builder.py` · `runtime/spine/spine.py` (line 805) · `assets/living_presence_spec.txt`

## Test
`python3 tests/test_prompt_builder.py` — confirm `autobiographical_summary` content appears in assembled prompt when non-empty.
If no such test exists: write one. It must pass without David.

## Done when
Implemented + test green + committed. Acceptance test: set `autobiographical_summary = "David's studio is in Hackney"` in a test ExecutiveContext → assembled prompt contains "Hackney" in the ground-truth section.

**Spec detail:** `blender/agent_bus/builder/FROM_ARCHITECT_2026-10-06_ROOT2-MISSING-FACT-FIX.md`

## Result (fill in when done)
- commit:
- test:
- notes:
