"""
runtime/executive.py — eLo OS v2 Executive Function.

Step 4 of the cognitive cycle:
    Attention model → executive decision → prompt directive.

Maps intent + emotional_context to:
    - voice tone selection (one of 5)
    - max sentence count
    - stability mode flag
    - loop protection override

STABILITY FIRST RULE (hard priority order):
    1. Stabilise user
    2. Simplify response
    3. Reduce output length
    4. Avoid questions

LOOP PROTECTION:
    If triggered → DIRECT mode, no abstraction, no expansion.
"""

from __future__ import annotations

# Tone labels correspond to voice_range spec sections.
# Used as a directive injected into the system prompt.
_TONE_CHILDLIKE_WISE = "CHILDLIKE-WISE"
_TONE_SILENCE_AWARE  = "SILENCE-AWARE"
_TONE_DIRECT         = "DIRECT"
_TONE_JOYFUL         = "JOYFUL"
_TONE_WITTY          = "WITTY"

# Intent → default tone mapping
_INTENT_TONE: dict[str, str] = {
    "inquiry":      _TONE_CHILDLIKE_WISE,
    "creation":     _TONE_JOYFUL,
    "emotional":    _TONE_SILENCE_AWARE,
    "recall":       _TONE_CHILDLIKE_WISE,
    "conversation": _TONE_CHILDLIKE_WISE,
    "stabilise":    _TONE_DIRECT,
    "simplify":     _TONE_SILENCE_AWARE,
}

# Emotional state → tone refinement (overrides intent mapping when emotion is strong)
_EMO_TONE_OVERRIDE: dict[str, str] = {
    "overwhelmed": _TONE_SILENCE_AWARE,
    "stressed":    _TONE_SILENCE_AWARE,
    "low-energy":  _TONE_SILENCE_AWARE,
    "energised":   _TONE_JOYFUL,
}

# Max sentences by tone
_MAX_SENTENCES: dict[str, int] = {
    _TONE_SILENCE_AWARE:  2,
    _TONE_DIRECT:         1,
    _TONE_JOYFUL:         3,
    _TONE_WITTY:          2,
    _TONE_CHILDLIKE_WISE: 3,
}


def decide(attention_model: dict, loop_detected: bool = False) -> dict:
    """
    Compute the executive decision from the attention model.

    Args:
        attention_model: Output of core.attention.compute().
        loop_detected:   True if hard loop detection fired.

    Returns:
        ExecDecision dict:
            {
                "tone":          str,   one of 5 voice tones
                "max_sentences": int,   1–4
                "stability":     bool,  True = apply stability override
                "intent":        str,   passed through for transparency
            }
    """
    intent = attention_model.get("intent", "conversation")
    emo    = attention_model.get("emotional_context", {})
    state  = emo.get("inferred_state", "present")

    # loop protection always wins
    if loop_detected or intent == "stabilise":
        return {
            "tone":          _TONE_DIRECT,
            "max_sentences": 1,
            "stability":     True,
            "intent":        intent,
        }

    # emotional state overrides intent-based tone when strong
    tone = _EMO_TONE_OVERRIDE.get(state) or _INTENT_TONE.get(intent, _TONE_CHILDLIKE_WISE)

    # witty: light confusion or curiosity with low tension
    tension = emo.get("tension", 0.4)
    energy  = emo.get("energy", 0.5)
    if intent == "conversation" and tension < 0.3 and energy > 0.4:
        tone = _TONE_WITTY

    stability = state in ("overwhelmed", "stressed") or intent in ("stabilise", "simplify")

    return {
        "tone":          tone,
        "max_sentences": _MAX_SENTENCES.get(tone, 3),
        "stability":     stability,
        "intent":        intent,
    }
