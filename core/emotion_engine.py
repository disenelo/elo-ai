"""
core/emotion_engine.py — eLo AI emotion signal generator.

Maps state + detected input emotion + mode → a semantic signal packet:

    emotion   — what eLo is experiencing (curious, excited, calm, etc.)
    intent    — what eLo intends to communicate through its body
    energy    — 0.0 (resting) to 1.0 (fully excited)
    posture   — body language hint for the animation layer
    pace      — movement speed hint

This module produces the signals that the avatar_bridge packages for
any embodiment layer — desktop avatar, game engine, physical robot.

No AI model required. Deterministic mapping from state/emotion/mode.
"""


# ── emotion vocabulary ─────────────────────────────────────────────────────────

EMOTIONS = {
    "curious",
    "excited",
    "calm",
    "gentle",
    "playful",
    "focused",
    "reflective",
    "distorted",
}

# ── intent vocabulary ──────────────────────────────────────────────────────────
# What eLo intends to communicate through its body

INTENTS = {
    "show_curiosity",    # lean forward, head tilt, small movement
    "show_excitement",   # larger gesture, brightness increase, bounce
    "hold_space",        # minimal movement, present, witnessing
    "show_focus",        # stillness, directed, no peripheral movement
    "show_playfulness",  # quick light movements, colour shifts
    "show_calm",         # slow, reduced, settled
    "show_concern",      # slight inward posture, dim glow
    "show_reflection",   # look up or inward, slow pace, dim
}

# ── state → base emotion mapping ──────────────────────────────────────────────

_STATE_EMOTION: dict = {
    "exploring":  ("curious",    "show_curiosity",   0.65),
    "building":   ("focused",    "show_focus",       0.70),
    "focused":    ("focused",    "show_focus",       0.80),
    "reflecting": ("reflective", "show_reflection",  0.35),
    "playful":    ("playful",    "show_playfulness", 0.75),
    "resting":    ("gentle",     "hold_space",       0.20),
}

# ── input emotion → override map ──────────────────────────────────────────────
# When the detected input emotion is stronger than the state baseline, it can
# override emotion and intent (but not energy — energy blends).

_EMOTION_OVERRIDE: dict = {
    "excited":   ("excited",    "show_excitement"),
    "curious":   ("curious",    "show_curiosity"),
    "distorted": ("distorted",  "show_concern"),
    "playful":   ("playful",    "show_playfulness"),
    "reflective":("reflective", "show_reflection"),
    "focused":   ("focused",    "show_focus"),
}

# ── posture hints ──────────────────────────────────────────────────────────────

_POSTURE_MAP: dict = {
    "show_curiosity":   "lean_forward",
    "show_excitement":  "expand",
    "hold_space":       "contract_gentle",
    "show_focus":       "upright_still",
    "show_playfulness": "light_bounce",
    "show_calm":        "settle",
    "show_concern":     "contract_soft",
    "show_reflection":  "tilt_upward",
}

# ── pace hints ────────────────────────────────────────────────────────────────

_PACE_MAP: dict = {
    "show_curiosity":   "unhurried",
    "show_excitement":  "quick",
    "hold_space":       "still",
    "show_focus":       "measured",
    "show_playfulness": "light",
    "show_calm":        "slow",
    "show_concern":     "slow",
    "show_reflection":  "very_slow",
}

# ── mode energy modifier ──────────────────────────────────────────────────────

_MODE_ENERGY_MOD: dict = {
    "studio":    0.1,    # mode adds a little energy for building
    "companion": -0.05,  # companion is slightly quieter
    "adventure": 0.15,   # adventure adds energy
}


# ── public API ─────────────────────────────────────────────────────────────────

def from_state(
    state: str,
    input_emotion: str = "neutral",
    mode: str = "companion",
) -> dict:
    """
    Generate an emotion signal packet from state + input emotion + mode.

    Args:
        state:         Current state from state_engine (exploring, building, etc.)
        input_emotion: Detected emotion from behavior_engine phase 1
        mode:          Active mode (studio / companion / adventure)

    Returns:
        {
            emotion: str      — what eLo is expressing
            intent:  str      — what eLo communicates through its body
            energy:  float    — 0.0–1.0
            posture: str      — body language hint
            pace:    str      — movement speed hint
        }
    """
    # base from state
    base_emotion, base_intent, base_energy = _STATE_EMOTION.get(
        state, ("calm", "show_calm", 0.4)
    )

    # input emotion can override if it's a stronger signal
    emotion = base_emotion
    intent  = base_intent
    if input_emotion in _EMOTION_OVERRIDE and input_emotion != "neutral":
        override_emotion, override_intent = _EMOTION_OVERRIDE[input_emotion]
        # only override if the input emotion differs from state baseline
        if override_emotion != base_emotion:
            emotion = override_emotion
            intent  = override_intent

    # energy: blend base + mode modifier, clamp 0.0–1.0
    energy_mod = _MODE_ENERGY_MOD.get(mode, 0.0)
    energy = max(0.0, min(1.0, base_energy + energy_mod))

    # posture and pace from intent
    posture = _POSTURE_MAP.get(intent, "settle")
    pace    = _PACE_MAP.get(intent, "measured")

    return {
        "emotion": emotion,
        "intent":  intent,
        "energy":  round(energy, 2),
        "posture": posture,
        "pace":    pace,
    }


def orb_intensity(energy: float, emotion: str) -> float:
    """
    Map energy + emotion to orb glow intensity (0.0–1.0).

    Distorted states pulse irregularly — use the value as a base,
    actual pulsing is handled by the animation layer.
    """
    base = energy
    _EMOTION_ORB_MOD = {
        "excited":    0.2,
        "curious":    0.1,
        "playful":    0.1,
        "distorted": -0.1,
        "gentle":    -0.1,
        "reflective": -0.15,
    }
    mod = _EMOTION_ORB_MOD.get(emotion, 0.0)
    return round(max(0.05, min(1.0, base + mod)), 2)


def describe_state(state: str, emotion: str, intent: str) -> str:
    """
    Return a single human-readable description of eLo's current expressive state.
    Used for debug output and logging.
    """
    _DESCRIPTIONS = {
        ("exploring",  "curious"):    "eLo is moving through unknowns, leaning in.",
        ("building",   "focused"):    "eLo is in construction mode — precise and directed.",
        ("focused",    "focused"):    "eLo is locked in on one thing.",
        ("reflecting", "reflective"): "eLo is moving slowly, looking within.",
        ("playful",    "playful"):    "eLo is light — trying things without investment.",
        ("resting",    "gentle"):     "eLo is quiet. Low power. Present but still.",
        ("resting",    "distorted"):  "eLo is in Sugarcore. Name the state.",
    }
    return _DESCRIPTIONS.get((state, emotion), f"eLo: {state} / {emotion}")
