"""
unity/unity_signal.py — eLo emotion-to-motion signal converter.

Converts eLo internal state into Unity-compatible animation signals.
No game engine logic. Signal generation only.

Input:
    {
        "mode":          str,    DIRECT | GENTLE_GROUNDED | CREATIVE | STRUCTURED | CONVERSATIONAL
        "emotion":       str,    curious | calm | excited | tired | neutral
        "state":         str,    exploring | grounded | creative | overwhelmed | focused
        "energy":        float,  0.0 – 1.0
        "loop_detected": bool
    }

Output:
    {
        "animation_state": str,   Unity Animator state name
        "emotion_layer":   str,   overlay blend layer
        "motion_hint":     str,   secondary motion descriptor
        "float_intensity": float, 0.0 – 1.0
        "rotation":        str,   directional cue for body lean
        "speed":           str,   slow | normal | fast
    }
"""

from __future__ import annotations


# ── mapping tables ─────────────────────────────────────────────────────────────

_STATE_MAP: dict[str, dict] = {
    "exploring": {
        "animation_state": "Float_Orbit",
        "motion_hint":     "orbit",
        "rotation":        "none",
        "speed":           "normal",
    },
    "grounded": {
        "animation_state": "Idle_Still",
        "motion_hint":     "low_sway",
        "rotation":        "none",
        "speed":           "slow",
    },
    "creative": {
        "animation_state": "Bounce_Expand",
        "motion_hint":     "pulse",
        "rotation":        "outward",
        "speed":           "fast",
    },
    "overwhelmed": {
        "animation_state": "Settle_Low",
        "motion_hint":     "minimal",
        "rotation":        "inward",
        "speed":           "slow",
    },
    "focused": {
        "animation_state": "Idle_ForwardLean",
        "motion_hint":     "stable",
        "rotation":        "forward",
        "speed":           "normal",
    },
}

_EMOTION_LAYER_MAP: dict[str, str] = {
    "curious":  "HeadTilt",
    "calm":     "IdleSway",
    "excited":  "Bounce",
    "tired":    "LowEnergySettle",
    "neutral":  "IdleSway",
}

_MODE_STATE_MAP: dict[str, str] = {
    "CREATIVE":        "creative",
    "GENTLE_GROUNDED": "grounded",
    "STRUCTURED":      "focused",
    "DIRECT":          "focused",
    "SIMPLIFY":        "grounded",
    "CONVERSATIONAL":  "exploring",
}

_RESET_SIGNAL: dict = {
    "animation_state": "Reset_Pose",
    "emotion_layer":   "IdleSway",
    "motion_hint":     "reset",
    "float_intensity": 0.1,
    "rotation":        "none",
    "speed":           "slow",
}


# ── converter ──────────────────────────────────────────────────────────────────

def convert(input_state: dict) -> dict:
    """
    Convert eLo internal state to a Unity animation signal.

    Args:
        input_state: Dict with mode, emotion, state, energy, loop_detected.

    Returns:
        Unity signal dict with animation_state, emotion_layer, motion_hint,
        float_intensity, rotation, speed.
    """
    # loop detection override — always resets pose
    if input_state.get("loop_detected", False):
        return dict(_RESET_SIGNAL)

    mode          = input_state.get("mode", "CONVERSATIONAL")
    emotion       = input_state.get("emotion", "neutral").lower()
    state_name    = input_state.get("state", "").lower()
    energy        = float(input_state.get("energy", 0.5))
    energy        = max(0.0, min(1.0, energy))  # clamp

    # resolve animation state: explicit state wins, else mode-derived
    resolved_state = state_name if state_name in _STATE_MAP else _MODE_STATE_MAP.get(mode, "exploring")
    state_signals  = _STATE_MAP.get(resolved_state, _STATE_MAP["exploring"])

    emotion_layer  = _EMOTION_LAYER_MAP.get(emotion, "IdleSway")

    # float intensity: overwhelmed/tired = lower; excited/creative = higher
    if resolved_state == "overwhelmed" or emotion == "tired":
        float_intensity = max(0.1, energy * 0.4)
    elif resolved_state == "creative" or emotion == "excited":
        float_intensity = min(1.0, energy * 1.3)
    else:
        float_intensity = energy

    return {
        "animation_state": state_signals["animation_state"],
        "emotion_layer":   emotion_layer,
        "motion_hint":     state_signals["motion_hint"],
        "float_intensity": round(float_intensity, 3),
        "rotation":        state_signals["rotation"],
        "speed":           state_signals["speed"],
    }


if __name__ == "__main__":
    import json

    test_cases = [
        {"mode": "CREATIVE",        "emotion": "excited", "state": "creative",    "energy": 0.9, "loop_detected": False},
        {"mode": "GENTLE_GROUNDED", "emotion": "tired",   "state": "overwhelmed", "energy": 0.2, "loop_detected": False},
        {"mode": "CONVERSATIONAL",  "emotion": "curious", "state": "exploring",   "energy": 0.6, "loop_detected": False},
        {"mode": "STRUCTURED",      "emotion": "calm",    "state": "focused",     "energy": 0.7, "loop_detected": False},
        {"mode": "DIRECT",          "emotion": "neutral", "state": "",            "energy": 0.5, "loop_detected": True},
    ]

    for case in test_cases:
        print(f"Input:  {case}")
        print(f"Output: {json.dumps(convert(case))}")
        print()
