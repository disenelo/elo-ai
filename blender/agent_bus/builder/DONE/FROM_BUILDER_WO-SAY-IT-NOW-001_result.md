# FROM_BUILDER — WO-SAY-IT-NOW-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)  
**Commit:** ef0acc5

---

## What was built

`runtime/prompt_builder.py` — "Say-it-now" editorial urgency instruction added. Fires when LOOP-8 creative seed is present OR affective curiosity > 0.6.

### Code added (after self-model block)

```python
# WO-SAY-IT-NOW-001: editorial urgency — say the noticed thing immediately
_creative_seed = exec_decision.get("creative_seed") or exec_decision.get("loop8_seed") or ""
_aff_curiosity = float((exec_decision.get("affective_state") or {}).get("curiosity", 0.0) or 0.0)
if _creative_seed or _aff_curiosity > 0.6:
    directive_lines.append(
        "Say-it-now: the thing you noticed — say it this turn, don't save it for later. "
        "Not setup, not context-setting. The observation itself."
    )
```

## Trigger logic

- **LOOP-8 seed present:** eLo has made an unexpected creative connection — that's exactly the moment the "say it now" discipline matters. The seed was generated this turn; it must surface now.
- **High curiosity (>0.6):** When eLo's curiosity is genuinely high, it has noticed something. "Say-it-now" fires because this is when the pattern of saving the noticed thing for later is most likely.

## Source intent

"Say the thing you noticed. Don't save it for later." — this is eLo's editorial discipline. The gap was that LOOP-8 could generate a creative connection that then didn't surface in the expressed output. The "say-it-now" instruction ensures when the seed is there, it comes out THIS turn.

## Test result

1565 passed — no regressions.
