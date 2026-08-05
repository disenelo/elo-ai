"""
runtime/affordances.py — WO-056: Affordances on the World Model

Affordance Before Action (ADR-Exec-003 LAW):
The Executive searches POSSIBILITIES, not animations.

Maps surface_type → frozenset of available actions.
Surface types come from the desktop/world model (window_top, window_body,
desktop_floor, unknown). Actions use the 049-A verb vocabulary.
"""
from __future__ import annotations

# ── Affordance table ──────────────────────────────────────────────────────────
# Each surface maps to a frozenset of action verbs.
# Verb vocabulary matches the ratified 049-A contract.

SURFACE_AFFORDANCES: dict[str, frozenset] = {
    "window_top":    frozenset({
        "stand", "run", "jump", "wall-run", "peek", "enter", "exit",
    }),
    "window_body":   frozenset({
        "wall-run", "climb", "hide", "peek",
    }),
    "window_bottom": frozenset({
        "stand", "peek", "exit",
    }),
    "desktop_floor": frozenset({
        "stand", "run", "jump",
    }),
    "taskbar":       frozenset({
        "stand", "run", "jump", "enter",
    }),
    "unknown":       frozenset({
        "stand", "run",
    }),
}

# Canonical ordered form for display / prompt injection
_ORDER = [
    "stand", "run", "jump", "wall-run", "climb",
    "hide", "peek", "enter", "exit",
]


def affordances_for(surface_type: str) -> tuple:
    """
    Return a sorted tuple of affordances for the given surface.

    Args:
        surface_type — one of the SURFACE_AFFORDANCES keys, or any unknown string.

    Returns:
        Sorted tuple of action verb strings.
        Falls back to ("stand", "run") for unrecognised surfaces.
    """
    verbs = SURFACE_AFFORDANCES.get(surface_type, SURFACE_AFFORDANCES["unknown"])
    return tuple(v for v in _ORDER if v in verbs)


def prompt_block(surface_type: str) -> str:
    """
    Formatted [AFFORDANCES] block for the Executive prompt.

    The Executive reads this before deciding — it consults possibility, not
    geometry. If a verb isn't in this list, eLo cannot do it right now.
    """
    verbs = affordances_for(surface_type)
    if not verbs:
        return ""
    verb_str = " · ".join(verbs)
    return f"[AFFORDANCES surface={surface_type}] {verb_str}"
