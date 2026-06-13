"""
avatar/presence_engine.py — cognition → embodiment.

Takes attention_model + exec_decision → AvatarState.
Maintains session-scoped current state so presence changes smoothly across turns.
"""

from avatar.avatar_state import default, blend

# session-scoped current presence — module singleton, reset each session
_current: dict = default()

# CAL action → avatar mode
_ACTION_MODE: dict[str, str] = {
    "celebrate": "celebrating",
    "build":     "building",
    "connect":   "exploring",
    "expand":    "exploring",
    "challenge": "observing",
    "reflect":   "thinking",
    "answer":    "thinking",
    "ground":    "resting",
    "witness":   "resting",
    "silence":   "idle",
}


def compute(attention_model: dict, exec_decision: dict) -> dict:
    """
    Derive target presence from the cognitive pipeline output.
    Blend toward it from the current state and return the smoothed result.
    """
    global _current

    emo     = attention_model.get("emotional_context", {})
    energy  = float(emo.get("energy",  0.5))
    tension = float(emo.get("tension", 0.4))
    action  = exec_decision.get("action", "reflect")

    mode = _ACTION_MODE.get(action, "thinking")

    target = {
        "mode":             mode,
        "energy":           round(energy, 3),
        "curiosity":        round(max(0.0, min(1.0, energy - tension * 0.5 + 0.3)), 3),
        "certainty":        round(max(0.0, min(1.0, 1.0 - tension)), 3),
        "engagement":       round(max(0.0, min(1.0, energy * (1.0 - tension * 0.3))), 3),
        "motion_permission": energy > 0.1,
    }

    _current = blend(_current, target)
    return _current


def reset() -> None:
    """Reset presence to default. Call at session start."""
    global _current
    _current = default()


def current() -> dict:
    """Return the current presence state without modifying it."""
    return dict(_current)
