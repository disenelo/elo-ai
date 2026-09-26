"""
expression/expression_mapper.py — PresenceState + CAL action → expression command.

eLo has no eyes. Expression comes from:
    - shape key blends on eLo-BodyxHead w/Mouth
    - head bone rotation on c_head.x
    - pacing (speed label for animation brain)

Shape key ranges on eLo's mesh are NOT standard 0-1 — many run -5.0 to 5.0.
Values here stay within safe ranges (max ±1.0 on the wide-range keys).

Phoneme keys (Ah, Mbp, Oooh, etc.) are driven by voice/TTS — not set here.
This mapper handles emotional expression only.
"""
from __future__ import annotations

import random

from presence.presence_state import PresenceMode


# mode → shape key blend dict
# Keys are actual Blender shape key names on eLo-BodyxHead w/Mouth
# Values are target blend amounts within each key's safe range
_MODE_EXPRESSION: dict[str, dict] = {
    "idle": {
        "Smile.L":             0.15,
        "Smile.R":             0.15,
        "Satisfied/LittleJoy": 0.1,
    },
    "thinking": {
        "Huh":                0.45,
        "Confident":          0.3,
    },
    "observing": {
        "Smile.L":             0.25,
        "Smile.R":             0.25,
        "Satisfied/LittleJoy": 0.2,
    },
    "building": {
        "Smile.L":             0.45,
        "Smile.R":             0.45,
        "Confident":           0.5,
        "Satisfied/LittleJoy": 0.3,
    },
    "celebrating": {
        "MouthOpen.Wide":      0.85,
        "Smile.L":             0.9,
        "Smile.R":             0.9,
        "Smile-Cheeks":        0.75,
        "Satisfied/LittleJoy": 1.0,
    },
    "resting": {
        "Smile.L":             0.25,
        "Smile.R":             0.25,
        "Satisfied/LittleJoy": 0.2,
    },
    "exploring": {
        "Huh":                 0.35,
        "Smile.L":             0.25,
        "Smile.R":             0.25,
        "Satisfied/LittleJoy": 0.15,
    },
}

# CAL action bonus — layered on top of mode expression
_ACTION_BONUS: dict[str, dict] = {
    "CELEBRATE": {"MouthOpen.Wide": 0.3,  "Smile-Cheeks": 0.4,  "Satisfied/LittleJoy": 0.2},
    "BUILD":     {"Smile.L":        0.2,  "Smile.R": 0.2,        "Confident": 0.2},
    "CONNECT":   {"Smile.L":        0.15, "Smile.R": 0.15,       "Satisfied/LittleJoy": 0.15},
    "CHALLENGE": {"Confident":      0.4},
    "REFLECT":   {"Huh":            0.3},
    "WITNESS":   {"Smile.L":        0.2,  "Smile.R": 0.2},
    "GROUND":    {"Satisfied/LittleJoy": 0.1},
    "ANSWER":    {"Confident": 0.15},
}

# mode → head lean on c_head.x bone (Euler Y rotation, radians, small values)
_HEAD_LEAN: dict[str, float] = {
    "idle":        0.04,
    "thinking":    0.18,   # noticeable tilt — processing
    "observing":   0.12,
    "building":    0.0,    # forward, straight, focused
    "celebrating": -0.12,  # open tilt left — joy
    "resting":     0.14,
    "exploring":  -0.14,
}

# action → pacing label (consumed by animation brain for speed hints)
_ACTION_PACING: dict[str, str] = {
    "ANSWER":    "steady",
    "BUILD":     "forward",
    "CONNECT":   "gentle",
    "CELEBRATE": "bright",
    "REFLECT":   "slow",
    "GROUND":    "still",
    "CHALLENGE": "direct",
    "WITNESS":   "quiet",
    "SILENCE":   "still",
}


# Ambient flicker pool — mild, brief expression pulses for idle moments.
# Never dramatic; used by ambient_engine._pulse_emotion().
_AMBIENT_FLICKER_POOL: list[dict[str, float]] = [
    {"Smile.L": 0.3,  "Smile.R": 0.3},
    {"Satisfied/LittleJoy": 0.35, "Smile.L": 0.2, "Smile.R": 0.2},
    {"Huh": 0.3},
    {"Smile.L": 0.45, "Smile.R": 0.45, "Smile-Cheeks": 0.2},
    {"Confident": 0.25},
]


def get_ambient_flicker() -> dict[str, float]:
    """Return a random mild expression blend for an ambient emotion pulse.
    Returns an empty dict ~20% of the time so pulses feel spontaneous, not metronomic."""
    if random.random() < 0.2:
        return {}
    return dict(random.choice(_AMBIENT_FLICKER_POOL))


def map_emotion(valence: str, action: str) -> dict:
    """
    Map attention valence + CAL action → state.emotion + state.intensity.
    Unity uses this as the continuous mood baseline driving breathing rate
    and the held-floor blendshape (joy→Smile-Cheeks, worried→Worried, etc.).
    The floor never overrides a stronger value eLo OS sends in expression.shape_keys.
    """
    action_l = action.lower()
    if action_l == "celebrate":
        return {"emotion": "joy",       "intensity": 0.85}
    if action_l in ("build", "connect", "challenge"):
        return {"emotion": "confident", "intensity": 0.65}
    if action_l == "ground":
        return {"emotion": "worried",   "intensity": 0.55}
    if action_l == "witness":
        return {"emotion": "sad",       "intensity": 0.50}
    # valence-driven fallback
    if valence == "positive_high":
        return {"emotion": "joy",       "intensity": 0.75}
    if valence == "positive_low":
        return {"emotion": "confident", "intensity": 0.50}
    if valence == "negative_high":
        return {"emotion": "worried",   "intensity": 0.70}
    if valence == "negative_low":
        return {"emotion": "worried",   "intensity": 0.45}
    return {"emotion": "neutral",       "intensity": 0.20}


def build_expression(mode: PresenceMode, action: str, intensity: float) -> dict:
    """
    Build an expression command from presence mode + CAL action.

    Returns:
        {
            "shape_keys": dict[str, float],  — key name → blend value
            "head_lean":  float,             — c_head.x Y rotation (radians)
            "pacing":     str,               — speed label
            "intensity":  float,
        }
    """
    mode_str = mode.value if hasattr(mode, "value") else str(mode)

    base    = dict(_MODE_EXPRESSION.get(mode_str, {}))
    bonus   = _ACTION_BONUS.get(action.upper(), {})
    lean    = _HEAD_LEAN.get(mode_str, 0.0)
    pacing  = _ACTION_PACING.get(action.upper(), "steady")

    # merge bonus on top of base
    for k, v in bonus.items():
        base[k] = round(base.get(k, 0.0) + v, 3)

    # scale by intensity — floor at 0.6 so expressions are always visible
    eff = max(intensity, 0.6)
    shape_keys = {k: round(v * eff, 3) for k, v in base.items()}
    lean       = round(lean * eff, 4)

    return {
        "shape_keys": shape_keys,
        "head_lean":  lean,
        "pacing":     pacing,
        "intensity":  round(intensity, 3),
    }
