"""
expression/expression_mapper.py — PresenceState + CAL action → expression command.

eLo has no eyes. Expression comes entirely from:
    - body posture (via animation clip)
    - pacing (speed of movement)
    - mouth shape (open/closed/small/wide)
    - head tilt / lean direction

Output is a flat dict consumed by the Blender bridge.
"""
from __future__ import annotations

from presence.presence_state import PresenceMode


# mode + action → mouth shape (Blender shape key name)
_MOUTH_SHAPE: dict[str, str] = {
    "idle":        "closed",
    "thinking":    "small",
    "observing":   "small",
    "building":    "open",
    "celebrating": "wide",
    "resting":     "closed",
    "exploring":   "open",
}

# mode → head lean (-1 = left, 0 = straight, 1 = right, 0.5 = slight right)
_HEAD_LEAN: dict[str, float] = {
    "idle":        0.0,
    "thinking":    0.3,    # slight lean — processing
    "observing":   0.15,
    "building":    0.0,    # forward, straight
    "celebrating": -0.1,   # slight open tilt
    "resting":     0.2,
    "exploring":   -0.2,
}

# action → pacing label
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
            "mouth":     str,    — shape key name for Blender
            "head_lean": float,  — -1 to 1
            "pacing":    str,    — descriptive pacing label
            "intensity": float,  — expression strength
        }
    """
    mode_str = mode.value if hasattr(mode, "value") else str(mode)

    mouth    = _MOUTH_SHAPE.get(mode_str, "closed")
    lean     = _HEAD_LEAN.get(mode_str, 0.0)
    pacing   = _ACTION_PACING.get(action.upper(), "steady")

    # intensity scales lean slightly
    lean = round(lean * (0.5 + intensity * 0.5), 3)

    return {
        "mouth":     mouth,
        "head_lean": lean,
        "pacing":    pacing,
        "intensity": round(intensity, 3),
    }
