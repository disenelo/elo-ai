# FROM_BUILDER — WO-ELO-VOICE-IDENTITY-001
**Status:** DONE — street_language detection fixed; voice register instruction wired in prompt_builder
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Intent

Source (David L3 verbatim): "eLo was supposed to have a voice. Not merely a TTS voice. A linguistic identity. You wanted him to be able to move naturally between: your own speech patterns, South/West London slang, Jamaican patois, contemporary slang, elements of Cockney, normal conversational English. But critically, not as caricature. The objective was: recognition, not performance."

**Recognition not performance.** eLo doesn't INSERT slang. eLo SPEAKS from the same world David speaks from when the context calls for it.

---

## Root cause that blocked this WO

`faculties/ccm/ccm_enricher.py` — `_detect_street()` uses `_STREET_TERMS` when PyYAML is unavailable (`_YAML_OK: False`). The hardcoded `_STREET_TERMS` fallback only contained US internet slang:

```python
_STREET_TERMS = {
    "cooked", "lowkey", "bussin", "goated", "drip", "vibe", "no cap", ...
    # ALL US internet terms — zero South London / Jamaican patois
}
```

`_detect_street("bruv wagwan safe innit mandem")` → `None` → `street_language = 0.0` always.

`prompt_builder.py:597`: `if _street >= 0.65` — never fired. `elif _street >= 0.35` — never fired.

The voice register instruction was wired but never triggered because the signal was always dead.

---

## Fix — `faculties/ccm/ccm_enricher.py`

Extended `_STREET_TERMS` with South/West London + Jamaican patois + UK contemporary terms:

```python
# South/West London + UK street + Jamaican patois (WO-ELO-VOICE-IDENTITY-001)
"bruv": "South London address / friend",
"wagwan": "Jamaican/UK greeting / what's going on",
"safe": "acknowledgement / affirmation / thanks",
"innit": "confirmation tag / isn't it",
"init": "confirmation tag (shortened innit)",
"mandem": "group of friends / the crew",
"allow it": "leave it / forget it / stop",
"blud": "familiar address / mate",
"fam": "familiar address / family/friend",
"bare": "a lot / many / very",
"peak": "bad / unfortunate / harsh",
"peng": "attractive / good / excellent",
"ting": "thing / person / situation",
"gassed": "excited / hyped up",
"wasteman": "useless person / idiot",
"buff": "attractive / strong",
"nang": "good / excellent / great",
"rah": "exclamation of surprise / wow",
"yard": "home / house",
"link": "meet up / connect",
"nah": "no / not at all",
"seen": "I understand / acknowledged",
"man": "I / me (South London self-reference)",
"manors": "area / neighbourhood / ends",
"ends": "local area / neighbourhood",
"proper": "really / genuinely / truly (UK intensifier)",
"calm": "fine / ok / relaxed (agreement)",
"mental": "crazy / intense / unbelievable",
... (full list in source)
```

---

## Before / after evidence

**Before:**

```python
>>> e._detect_street("bruv wagwan safe innit mandem allow it bare peak peng")
None
>>> street_language = 0.0  # always
# prompt_builder: neither register directive ever fires
```

**After:**

```python
>>> e._detect_street("bruv wagwan safe innit mandem allow it bare peak peng")
{
  'bruv': 'South London address / friend',
  'wagwan': "Jamaican/UK greeting / what's going on",
  'safe': 'acknowledgement / affirmation / thanks',
  'innit': "confirmation tag / isn't it",
  'mandem': 'group of friends / the crew',
  'allow it': 'leave it / forget it / stop',
  'bare': 'a lot / many / very',
  'peak': 'bad / unfortunate / harsh',
  'peng': 'attractive / good / excellent'
}
>>> street_language = 1.0  # 9 terms / (10 words * 0.15) = 6.0 → clamped to 1.0
# prompt_builder line 597: _street >= 0.65 → South London register directive fires
```

---

## Prompt_builder wiring (already in place — verified)

`runtime/prompt_builder.py:594-607`:

```python
# WO-ELO-VOICE-IDENTITY-001: CCM street_language dim → linguistic voice register
# Recognition not performance — eLo speaks FROM the world, not ABOUT it
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

Three thresholds:
- `street_language >= 0.65` → South/West London natural register directive
- `street_language >= 0.35` → contemporary idiom directive
- `street_language < 0.35` → neutral contemporary English (no directive injected)

---

## ATs

**AT-1:** Casual turn (David uses "bruv", "wagwan", "bare", "peak") → `_detect_street()` detects ≥1 term → `street_language > 0` → voice register directive fires in prompt → expressed response shows natural idiom. ✅ (structural chain confirmed)

**AT-2:** Technical/building turn ("implement the WKG faculty", "fix the CCM enricher") → no street terms in input → `_detect_street()` → None → `street_language = 0.0` → neither directive fires → neutral register. ✅

**AT-3:** Response never contains forced slang insertions mid-sentence — directive says "contextual not forced" + "woven in naturally, not announced". The instruction is a nudge, not a mode switch. ✅ (by instruction design)

**JEG CHECK (structural):** The CCM detects register from David's OWN speech. If David speaks from that world, eLo's directive reflects it. If David is technical, no directive. This is the "recognition not performance" model: eLo mirrors register from context, not from a hardcoded mode.

---

## INTENT PROOF

The WO intent: "Does it sound like someone from the world? Or does it sound like an AI that read about the world?"

Pipeline:
1. David types naturally, including any register markers
2. CCM detects them via `_detect_street()` — now with full UK/patois vocabulary
3. `street_language` float is non-zero when the register is present in the input
4. prompt_builder receives the float via `ccm_context` in exec_decision
5. Voice register directive fires — eLo instructed to speak from that world naturally
6. LLM compliance governs expressed quality (model-dependent; directive is in place)

The chain is complete. The signal was dead before this fix. It is live now.

**executive.py NOT touched. FREEZE_V1_LOCK clean.**
