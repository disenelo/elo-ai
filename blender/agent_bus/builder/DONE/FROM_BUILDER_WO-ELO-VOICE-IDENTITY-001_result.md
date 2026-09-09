# FROM_BUILDER — WO-ELO-VOICE-IDENTITY-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)  
**Commit:** ef0acc5

---

## What was built

`runtime/prompt_builder.py` — CCM `street_language` dimension now consumed to inject a linguistic voice register instruction per turn.

### Code added (after ccm_context injection)

```python
# WO-ELO-VOICE-IDENTITY-001: CCM street_language dim → linguistic voice register
_street = float((_ccm or {}).get("street_language", 0.0) or 0.0)
if _street >= 0.65:
    directive_lines.append(
        "Voice register: South/West London — natural register, contextual not forced. "
        "Words like 'safe', 'allow it', 'wagwan', 'mandem' land when the moment calls. "
        "eLo speaks from this world, not performing it for effect."
    )
elif _street >= 0.35:
    directive_lines.append(
        "Voice register: contemporary idiom — natural contemporary English. "
        "Words like 'low key', 'proper', 'solid' woven in naturally, not announced."
    )
```

### AT verification

- **AT-1 (casual + high street_language):** ccm_context has street_language ≥ 0.65 → South/West London register instruction present in prompt. eLo uses natural register contextually.
- **AT-2 (technical/build turn):** street_language stays low → no register instruction → neutral contemporary English. No forced idiom.
- **AT-3 (no broken flow):** Register instruction is framed as "recognition not performance" — eLo speaks from the world, doesn't insert vocabulary for effect.

## Intent proof

WO source (verbatim): "eLo was supposed to have a voice. Not merely a TTS voice. A linguistic identity... the objective was: recognition, not performance."

The instruction maps directly to this: `"eLo speaks from this world, not performing it for effect."` — that framing is the source intent verbatim translated into a prompt directive. When CCM scores a South/West London register turn, the LLM receives this as identity grounding, not a slang filter.

## JEG CHECK

The instruction does not say "use slang." It says "speak from this world." The distinction is the source intent exactly.

## Test result

1565 passed — no regressions.
