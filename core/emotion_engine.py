"""
core/emotion_engine.py — eLo AI tone modifier.

Role: adjust HOW eLo speaks, not WHAT it decides.

Outputs three values only:
    tone     — the quality of voice (warm, precise, playful, minimal, open)
    pacing   — how fast or slow the response should feel (slow / moderate / quick)
    warmth   — how much presence eLo brings (0.0 = minimal, 1.0 = full)

This module does NOT:
    - select response mode
    - influence routing decisions
    - control response structure
    - determine what questions are asked

The kernel's router owns those decisions.
Emotion adjusts the delivery after the content is decided.

No AI model required. Deterministic mapping from input signals.
"""

import re


# ── emotion detection signals ──────────────────────────────────────────────────

_EMOTION_SIGNALS: dict = {
    "curious":    [r"\bwhat\s+if\b", r"\bwhy\b", r"\bhow\b", r"\bwonder\b", r"\?"],
    "excited":    [r"!{2,}", r"\bfinally\b", r"\byes\b", r"\bamazing\b", r"\blet'?s\s+go\b"],
    "reflective": [r"\bfeel\b", r"\bsense\b", r"\bwrong\b", r"\bnot\s+sure\b", r"\bthink\b"],
    "playful":    [r"\bhaha\b", r"\bweird\b", r"\bfun\b", r"\bsilly\b", r"\bwild\b"],
    "distorted":  [r"\bchaos\b", r"\boverwhelm\b", r"\bstuck\b", r"\bexhausted\b",
                   r"\beverything.*wrong\b", r"\bnothing\s+works\b"],
    "focused":    [r"\bstep\s+by\s+step\b", r"\bbuild\b", r"\bplan\b", r"\bsystem\b"],
}


def detect_emotion(text: str) -> str:
    """
    Detect the dominant emotion from input text.
    Returns one of: curious, excited, reflective, playful, distorted, focused, neutral.
    """
    text_lower = text.lower()
    scores = {e: 0 for e in _EMOTION_SIGNALS}

    for emotion, patterns in _EMOTION_SIGNALS.items():
        for p in patterns:
            if re.search(p, text_lower):
                scores[emotion] += 1

    best = max(scores, key=lambda e: scores[e])
    return best if scores[best] > 0 else "neutral"


# ── tone modifier tables ───────────────────────────────────────────────────────

_TONE_MAP: dict = {
    "curious":    "open",
    "excited":    "energised",
    "reflective": "soft",
    "playful":    "light",
    "distorted":  "minimal",
    "focused":    "precise",
    "neutral":    "warm",
}

_PACING_MAP: dict = {
    "curious":    "moderate",
    "excited":    "quick",
    "reflective": "slow",
    "playful":    "quick",
    "distorted":  "slow",
    "focused":    "moderate",
    "neutral":    "moderate",
}

_WARMTH_MAP: dict = {
    "curious":    0.75,
    "excited":    0.85,
    "reflective": 0.65,
    "playful":    0.80,
    "distorted":  0.40,
    "focused":    0.55,
    "neutral":    0.70,
}


# ── public API ─────────────────────────────────────────────────────────────────

def get_tone_modifier(user_input: str) -> dict:
    """
    Return a tone modifier dict based on the emotion detected in user_input.

    This is the only public function the rest of the system should call.
    The output adjusts delivery — it does not affect routing or structure.

    Returns:
        {
            "emotion": str    — detected emotion label
            "tone":    str    — voice quality hint (open / soft / light / precise / etc.)
            "pacing":  str    — timing hint (slow / moderate / quick)
            "warmth":  float  — presence level 0.0–1.0
        }
    """
    emotion = detect_emotion(user_input)
    return {
        "emotion": emotion,
        "tone":    _TONE_MAP.get(emotion,   _TONE_MAP["neutral"]),
        "pacing":  _PACING_MAP.get(emotion, _PACING_MAP["neutral"]),
        "warmth":  _WARMTH_MAP.get(emotion, _WARMTH_MAP["neutral"]),
    }


# ── avatar expression signals ──────────────────────────────────────────────────

_STATE_SIGNALS: dict = {
    #            emotion       intent               posture         pace       energy
    "idle":      ("calm",      "hold_space",        "settle",       "slow",    0.20),
    "conversing":("engaged",   "show_presence",     "upright",      "steady",  0.60),
    "thinking":  ("curious",   "show_curiosity",    "lean_forward", "slow",    0.50),
    "sitting":   ("relaxed",   "hold_space",        "settle",       "slow",    0.30),
    "excited":   ("excited",   "show_enthusiasm",   "upright",      "lively",  0.90),
    "calm":      ("calm",      "hold_space",        "settle",       "slow",    0.20),
}

_ENERGY_BOOST: dict = {
    "excited":    +0.10,
    "playful":    +0.08,
    "curious":    +0.05,
    "reflective": -0.05,
    "distorted":  -0.10,
}

_ORB_BOOST: dict = {
    "excited":  +0.10,
    "curious":  +0.07,
    "playful":  +0.05,
    "calm":     -0.08,
    "relaxed":  -0.05,
}


def from_state(state: str, input_emotion: str = "neutral", mode: str = "companion") -> dict:
    """
    Map eLo's current state + detected input emotion + mode into expression signals.

    Returns:
        {
            "emotion": str,   # eLo's expressed emotion
            "intent":  str,   # expression intent for the body
            "posture": str,   # body posture hint
            "pace":    str,   # response/movement pace
            "energy":  float, # 0.0 (low) to 1.0 (high), clamped
        }
    """
    base = _STATE_SIGNALS.get(state, _STATE_SIGNALS["idle"])
    emotion, intent, posture, pace, energy = base

    energy += _ENERGY_BOOST.get(input_emotion, 0.0)
    energy = round(max(0.0, min(1.0, energy)), 2)

    return {
        "emotion": emotion,
        "intent":  intent,
        "posture": posture,
        "pace":    pace,
        "energy":  energy,
    }


def orb_intensity(energy: float, emotion: str = "neutral") -> float:
    """
    Derive orb glow intensity from energy level and emotion.

    Returns a float clamped to [0.0, 1.0], rounded to 2 decimal places.
    """
    intensity = energy + _ORB_BOOST.get(emotion, 0.0)
    return round(max(0.0, min(1.0, intensity)), 2)
