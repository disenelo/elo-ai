# FROM_BUILDER — WO-COMPRESSION-AS-DEFAULT-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)  
**Commit:** ef0acc5

---

## What was built

`runtime/prompt_builder.py` — Compression added as a **constant** directive instruction that fires every turn, regardless of mode.

### Code added (in directive_lines construction — always on)

```python
# WO-COMPRESSION-AS-DEFAULT-001: compression is eLo's baseline, not a mode
"Compression: fewer words reveal more character. Say the thing and stop. "
"Don't explain what you're about to say. Don't recap what you just said.",
```

This replaces the prior state: compression only in `builder` mode expression (`"No preamble. No 'here's what we'll do'. Say the thing."`) — now that's a MODIFIER, and compression is the baseline.

## Why this was the primary gap

Source verbatim: **"excessive explanation replacing compression" is the primary drift failure.** The system had compression gated on `expression_mode == "builder"`. That meant every EXPLORE or PLAY turn could still over-explain. Compression must be eLo's character, not his build mode.

## Intent proof

**Before:** Compression instruction only fires in builder mode. eLo in EXPLORE/PLAY could produce 6-sentence explanations of what he was about to say.

**After:** Every turn carries `"fewer words reveal more character"` as a standing directive. The builder mode still adds its own modifier (no preamble, precise), but compression is no longer its exclusive territory.

## Test result

1565 passed — no regressions.
