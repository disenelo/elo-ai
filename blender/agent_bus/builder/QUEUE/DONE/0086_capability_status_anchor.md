**WO:** ROOT-7-B1-WIRE · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
eLo stops denying Spotify while it's playing. Capability state in the anchor.

## Scope
In `runtime/prompt_builder.py`:
```python
from tools.capability_status import capabilities_block
_cap_block = capabilities_block()
_cap_section = "\n\n## What I can do right now\n" + _cap_block + "\n"
```
Inject `_cap_section` in system prompt (before response instruction, after identity).
`capability_status.py` is at `tools/capability_status.py`, commit 995d48b. Do not edit it.

## Files
`runtime/prompt_builder.py`

## Test
`python3 tests/test_b3_capability_status.py` — 5/5. Then verify assembled prompt contains "What I can do right now" section.

## Done when
implemented + test green + committed.

## Result
- commit:
- test:
- notes:
