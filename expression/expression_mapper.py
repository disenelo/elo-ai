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

from presence.presence_state import PresenceMode


# mode → shape key blend dict
# Keys are actual Blender shape key names on eLo-BodyxHead w/Mouth
# Values are target blend amounts within each key's safe range
_MODE_EXPRESSION: dict[str, dict] = {
    "idle": {
        "MouthOpen.Slightly": 0.0,
        "Smile.L":            0.0,
        "Smile.R":            0.0,
        "Satisfied/LittleJoy": 0.0,
    },
    "thinking": {
        "MouthOpen.Slightly": 0.1,
        "Huh":                0.2,
        "Confident":          0.1,
    },
    "observing": {
        "MouthOpen.Slightly": 0.15,
        "Smile.L":            0.1,
        "Smile.R":            0.1,
    },
    "building": {
        "MouthOpen.Slightly": 0.2,
        "Smile.L":            0.2,
        "Smile.R":            0.2,
        "Confident":          0.3,
    },
    "celebrating": {
        "MouthOpen.Wide":      0.6,
        "Smile.L":             0.7,
        "Smile.R":             0.7,
        "Smile-Cheeks":        0.5,
        "Satisfied/LittleJoy": 0.8,
    },
    "resting": {
        "MouthOpen.Slightly": 0.0,
        "Smile.L":            0.05,
        "Smile.R":            0.05,
    },
    "exploring": {
        "MouthOpen.Slightly": 0.25,
        "Huh":                0.15,
        "Smile.L":            0.1,
        "Smile.R":            0.1,
    },
}

# CAL action bonus — layered on top of mode expression
_ACTION_BONUS: dict[str, dict] = {
    "CELEBRATE": {"MouthOpen.Wide": 0.2,  "Smile-Cheeks": 0.2},
    "CHALLENGE": {"Confident":      0.3,  "MouthOpen.Slightly": 0.1},
    "REFLECT":   {"Huh":            0.15, "MouthOpen.Slightly": -0.05},
    "WITNESS":   {"Smile.L":        0.05, "Smile.R": 0.05},
    "GROUND":    {"MouthOpen.Slightly": -0.05},
}

# mode → head lean on c_head.x bone (Euler Y rotation, radians, small values)
_HEAD_LEAN: dict[str, float] = {
    "idle":        0.0,
    "thinking":    0.08,   # slight tilt right — processing
    "observing":   0.05,
    "building":    0.0,    # forward, straight
    "celebrating": -0.05,  # slight open tilt left
    "resting":     0.06,
    "exploring":  -0.06,
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

    # scale by intensity
    shape_keys = {k: round(v * intensity, 3) for k, v in base.items()}
    lean       = round(lean * intensity, 4)

    return {
        "shape_keys": shape_keys,
        "head_lean":  lean,
        "pacing":     pacing,
        "intensity":  round(intensity, 3),
    }
