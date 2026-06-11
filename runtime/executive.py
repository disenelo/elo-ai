"""
runtime/executive.py — eLo OS v2 Executive Function + Conversation Action Layer.

Step 4 of the cognitive cycle:
    Attention model → executive decision → prompt directive.

Maps intent + emotional_context + valence + momentum to:
    - conversation_action (what kind of response to produce)
    - voice tone selection (one of 5)
    - max sentence count
    - stability mode flag

CONVERSATION ACTION LAYER:
    Sits between attention and response generation.
    Determines WHAT TO DO, not just what to say.

    Actions (priority order):
    ANSWER    — factual question → direct answer
    BUILD     — idea presented or explicit "build on this" → contribute
    CONNECT   — multiple concepts → show relationships
    CELEBRATE — positive momentum / breakthrough → acknowledge progress
    REFLECT   — exploring meaning → gentle perspective
    GROUND    — overwhelm / distress → stabilise
    CHALLENGE — stuck assumption → gentle alternative view
    WITNESS   — personal/emotional share → presence only
    SILENCE   — nothing useful to add

POSITIVE EMOTION RULE:
    Positive valence must NEVER trigger grounding.
    Positive high energy + building momentum → CELEBRATE or BUILD.
    Never route joy into stabilisation responses.
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


_BUILD_PHRASES    = ["build on that", "can you build", "expand on", "go further",
                     "take that further", "add to that", "tell me more", "what else",
                     "i had an insight", "i think it's essentially", "elo is essentially",
                     "the whole product", "the whole thing is", "i think elo is",
                     "that's what makes it", "that is what makes it",
                     "that's the difference", "the pitch is", "the mirror has",
                     "a diary", "diary doesn't", "diary does not", "the whole pitch",
                     "not a chatbot", "thinks alongside", "pushes back"]

_SHORT_AFFIRM     = ["and stays", "that's it", "that is it", "yeah", "exactly",
                     "right", "and that's it", "both", "i like that", "and remembers",
                     "and stays", "yep", "good instinct"]
_CONNECT_PHRASES  = ["how do they connect", "how does that connect", "are they related",
                     "why am i building all", "why are all these", "same idea",
                     "all matter", "they all", "all of them", "all connected",
                     "the game and", "the book and", "the robot and", "the os and"]
_CELEBRATE_PHRASES= ["i finally", "think i have", "got it", "figured it out",
                     "things are clicking", "it clicked", "feel clear", "opening arc",
                     "whole pitch", "that's it", "i understand now"]
_WITNESS_PHRASES  = ["i miss", "i wish i", "part of me", "sometimes i wonder",
                     "i don't know why i feel", "i feel like i've lost"]


def _conversation_action(
    user_input: str,
    intent:     str,
    valence:    str,
    momentum:   str,
) -> dict:
    """
    Conversation Action Layer — decides what eLo should DO this turn.

    Returns dict with action, confidence, reason.

    Priority: ANSWER > BUILD > CONNECT > CELEBRATE > REFLECT > GROUND > CHALLENGE > WITNESS > SILENCE
    """
    t = user_input.lower()

    # Short affirmations checked first — they celebrate, not build
    if any(p in t for p in _SHORT_AFFIRM) and len(t.strip()) < 35:
        return {"action": "celebrate", "confidence": 0.8, "reason": "short affirmation"}

    # Explicit BUILD/CONNECT phrases override intent
    if any(p in t for p in _BUILD_PHRASES):
        return {"action": "build", "confidence": 0.9, "reason": "explicit build phrase"}
    if any(p in t for p in _CONNECT_PHRASES):
        return {"action": "connect", "confidence": 0.9, "reason": "explicit connect phrase"}

    # 1. ANSWER — factual questions (must be interrogative, not just contain "what")
    if intent in ("inquiry", "recall"):
        is_question = t.strip().endswith("?") or \
                      any(t.strip().startswith(w) for w in ("what ", "how ", "why ", "who ", "when ", "where "))
        if is_question:
            return {"action": "answer", "confidence": 0.95, "reason": "factual question"}

    # 2. BUILD — creative positive context
    if intent == "creation" and valence in ("positive_high", "positive_low"):
        return {"action": "build", "confidence": 0.8, "reason": "creative positive context"}

    # 4. CELEBRATE — positive breakthrough or momentum
    if valence == "positive_high" and momentum == "building":
        return {"action": "celebrate", "confidence": 0.85, "reason": "positive momentum detected"}
    if any(p in t for p in _CELEBRATE_PHRASES):
        return {"action": "celebrate", "confidence": 0.8, "reason": "breakthrough signal"}
    if valence in ("positive_high", "positive_low") and intent in ("conversation", "emotional"):
        return {"action": "celebrate", "confidence": 0.7, "reason": "positive state"}

    # 5. REFLECT — exploring meaning or genuinely uncertain
    if intent == "emotional" and valence == "neutral":
        return {"action": "reflect", "confidence": 0.7, "reason": "emotional + neutral valence"}

    # 6. GROUND — overwhelm, distress, negative low energy, stuck
    if intent in ("emotional", "stabilise") and valence in ("negative_low", "negative_high"):
        return {"action": "ground", "confidence": 0.9, "reason": "negative emotional state"}
    if momentum == "stuck" or intent == "stabilise":
        return {"action": "ground", "confidence": 0.85, "reason": "stuck or stabilise intent"}
    if valence in ("negative_low", "negative_high"):
        return {"action": "ground", "confidence": 0.8, "reason": "negative valence"}

    # 7. WITNESS — personal emotional share, nothing to fix
    if any(p in t for p in _WITNESS_PHRASES):
        return {"action": "witness", "confidence": 0.8, "reason": "personal emotional share"}

    # 8. Short affirmations — stay with the momentum
    if any(p in t for p in _SHORT_AFFIRM) and len(t.strip()) < 35:
        return {"action": "celebrate", "confidence": 0.75, "reason": "short affirmation in context"}

    # 9. Building momentum — default to build, not reflect
    if momentum == "building" and valence not in ("negative_low", "negative_high"):
        return {"action": "build", "confidence": 0.65, "reason": "building momentum, stay in build mode"}

    # default
    return {"action": "reflect", "confidence": 0.5, "reason": "default — no stronger signal"}


_RESPONSE_GOAL: dict[str, str] = {
    "inquiry":      "answer",
    "creation":     "create",
    "emotional":    "stabilise",
    "recall":       "reflect",
    "conversation": "answer",
    "stabilise":    "stabilise",
    "simplify":     "clarify",
}

_GOAL_EMO_OVERRIDE: dict[str, str] = {
    "overwhelmed": "stabilise",
    "stressed":    "stabilise",
}

_COGNITIVE_LOAD: dict[str, str] = {
    _TONE_SILENCE_AWARE:  "low",
    _TONE_DIRECT:         "low",
    _TONE_CHILDLIKE_WISE: "medium",
    _TONE_WITTY:          "medium",
    _TONE_JOYFUL:         "high",
}


def decide(attention_model: dict, loop_detected: bool = False, user_input: str = "") -> dict:
    """
    Compute the executive decision from the attention model.

    Args:
        attention_model: Output of core.attention.compute().
        loop_detected:   True if hard loop detection fired.

    Returns:
        ExecDecision dict:
            tone          — one of 5 voice tones
            max_sentences — 1–4
            stability     — True = apply stability override
            intent        — passed through for transparency
            response_goal — clarify | stabilise | explore | create | answer | reflect
            cognitive_load — low | medium | high
            priority_order — ["primary", "secondary", "ignore"] labels
    """
    intent   = attention_model.get("intent", "conversation")
    emo      = attention_model.get("emotional_context", {})
    state    = emo.get("inferred_state", "present")
    valence  = emo.get("valence",  "neutral")
    momentum = emo.get("momentum", "stable")

    # compute conversation action
    cal = _conversation_action(user_input, intent, valence, momentum)
    action = cal["action"]

    # loop protection always wins
    if loop_detected or intent == "stabilise":
        return {
            "tone":              _TONE_DIRECT,
            "max_sentences":     1,
            "stability":         True,
            "intent":            intent,
            "response_goal":     "stabilise",
            "cognitive_load":    "low",
            "priority_order":    ["stabilise", "simplify", "ignore"],
            "action":            "ground",
            "valence":           valence,
            "momentum":          momentum,
        }

    # response goal from action
    _ACTION_GOAL = {
        "answer":    "answer",
        "build":     "create",
        "connect":   "reflect",
        "celebrate": "answer",
        "reflect":   "reflect",
        "ground":    "stabilise",
        "witness":   "stabilise",
        "challenge": "reflect",
        "silence":   "stabilise",
    }
    goal = _ACTION_GOAL.get(action, "answer")

    # tone from action — positive actions MUST get positive tones
    _ACTION_TONE = {
        "celebrate": _TONE_JOYFUL,
        "build":     _TONE_JOYFUL,
        "connect":   _TONE_CHILDLIKE_WISE,
        "answer":    _TONE_DIRECT,
        "ground":    _TONE_SILENCE_AWARE,
        "witness":   _TONE_SILENCE_AWARE,
        "reflect":   _TONE_CHILDLIKE_WISE,
        "challenge": _TONE_WITTY,
        "silence":   _TONE_SILENCE_AWARE,
    }
    tone = _ACTION_TONE.get(action, _TONE_CHILDLIKE_WISE)

    tension   = emo.get("tension", 0.4)
    energy    = emo.get("energy", 0.5)
    is_stable = action in ("ground", "witness", "silence")
    cog_load  = _COGNITIVE_LOAD.get(tone, "medium")

    priority_order = ["stabilise", "simplify", "ignore"] if is_stable \
                     else ["primary", "secondary", "ignore"]

    return {
        "tone":           tone,
        "max_sentences":  _MAX_SENTENCES.get(tone, 3),
        "stability":      is_stable,
        "intent":         intent,
        "response_goal":  goal,
        "cognitive_load": cog_load,
        "priority_order": priority_order,
        "action":         action,
        "valence":        valence,
        "momentum":       momentum,
    }
