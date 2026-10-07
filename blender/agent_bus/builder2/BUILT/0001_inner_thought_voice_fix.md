**WO:** INNER-THOUGHT-VOICE · **Seat:** builder2 · **Priority:** P0
**Reserved?** no

## Goal
eLo's inner thoughts sound like eLo, not a monitoring system. David called this out from his chatlog.

## Scope
1. `faculties/inner_thought/inner_thought_first.py` (or wherever the generation template lives):
   Replace prompt pattern that produces "I notice [David...]". New instruction:
   "Generate eLo's inner thought as what HE is thinking — not a description of what David said.
   WRONG: 'I notice David said when is sunset today'
   RIGHT: 'The light does shift around this time.' or 'Curious what the sky looks like right now.'
   The thought must be from eLo's perspective."

2. `faculties/inner_thought/inner_thought_quality.py` (quality checker) — add rejection rules:
   ```python
   import re
   BANNED = [r"^I notice David ", r"^I notice David's ", r"^I observe ",
             r"^I notice (?:that )?(?:David's|the|a) (?:sentence|question|word|phrase|use of)"]
   def check(thought):
       return not any(re.search(p, thought, re.IGNORECASE) for p in BANNED)
   ```
   Rejected thoughts are regenerated (not passed through).

## Files
`faculties/inner_thought/inner_thought_first.py` · `faculties/inner_thought/inner_thought_quality.py`

## Test
Write 3 example inner thoughts that pass the quality checker and do NOT contain "I notice David". File them in the result card as evidence. Existing tests must still pass.

## Done when
implemented + test green + committed + 3 example thoughts in result card.

## Result
- commit:
- test:
- notes:
