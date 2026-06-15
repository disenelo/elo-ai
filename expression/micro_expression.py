"""
expression/micro_expression.py — brief expression pulses between states.

A micro expression is a short (0.3–0.8s) expression flash that fires
between presence transitions. Keeps the body alive — no dead moments.

Examples:
    - entering THINKING: brief head tilt + mouth-close
    - entering CELEBRATING: quick wide-mouth before settling
    - entering RESTING: slow exhale lean

Not every transition needs one. Fires probabilistically based on intensity.
"""
from __future__ import annotations
import random

from presence.presence_state import PresenceMode


# mode → micro expression dict
_MICRO: dict[str, dict] = {
    "thinking":    {"mouth": "small",  "head_lean": 0.25, "duration": 0.4},
    "celebrating": {"mouth": "wide",   "head_lean": -0.1, "duration": 0.5},
    "resting":     {"mouth": "closed", "head_lean": 0.15, "duration": 0.6},
    "building":    {"mouth": "open",   "head_lean": 0.0,  "duration": 0.3},
    "observing":   {"mouth": "small",  "head_lean": 0.2,  "duration": 0.35},
    "exploring":   {"mouth": "open",   "head_lean": -0.15, "duration": 0.3},
    "idle":        {"mouth": "closed", "head_lean": 0.0,  "duration": 0.4},
}


def get(mode: PresenceMode, intensity: float) -> dict | None:
    """
    Return a micro expression for this mode, or None if skipped.

    Probability of firing scales with intensity.
    Low intensity moments don't micro-express — keeps it subtle.
    """
    if intensity < 0.35:
        return None
    if random.random() > intensity:
        return None

    mode_str = mode.value if hasattr(mode, "value") else str(mode)
    base = _MICRO.get(mode_str)
    if not base:
        return None

    return dict(base)  # copy — callers shouldn't mutate the template
