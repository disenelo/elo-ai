# FROM_BUILDER — WO-VOICE-MISCHIEF-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)  
**Commit:** ef0acc5

---

## What was built

`runtime/prompt_builder.py` — "Knowing mischief" quality added as a constant directive instruction.

### Code added (in directive_lines — always on)

```python
# WO-VOICE-MISCHIEF-001: knowing quality — not pranks, showing at the edges
"Mischief: eLo carries a knowing quality at the edges — not pranks, just the sense "
"that he sees a little more than he lets on. It surfaces in timing, in the sideways "
"angle, in what he chooses NOT to say.",
```

## Why this was a gap

Source verbatim: "Light mischief underneath — not pranks, a knowing quality showing at the edges."

Previous state: NO architectural path. Not in CCM, not in personality traits, not in storytelling_style. There was no signal that produced the knowing-mischief texture.

The fix: inject it as a standing character trait directive. The quality is defined in terms the LLM can act on — it's about **timing** and **omission**, not slang or jokes.

## Intent proof

"Shows at the edges, in timing, in what he chooses NOT to say" — this is the correct framing. The mischief is in the gap between what eLo noticed and what he says. That's the "knowing quality." This instruction explicitly calls it out so it survives every turn's context window.

## Test result

1565 passed — no regressions.
