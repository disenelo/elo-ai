"""
continuity/continuity_summary.py — human-readable continuity text.

Produces startup messages and recall responses from IdentityState.
Not transcripts. Meaning only.
"""
from __future__ import annotations
from continuity.identity_state import IdentityState

# ── direction phrases ─────────────────────────────────────────────────────────

_DIRECTION_PHRASE = {
    "building":    "moving toward",
    "opening":     "opening up around",
    "contracting": "sitting with something around",
    "settling":    "settling into",
}

_PROJECT_PHRASE = {
    "os":          "the OS",
    "game":        "the game",
    "robot":       "the robot",
    "book":        "the book",
    "kickstarter": "the Kickstarter",
}

_THEME_PHRASE = {
    "clarity":    "clarity",
    "building":   "building something",
    "identity":   "what eLo is",
    "connection": "how everything connects",
    "momentum":   "momentum",
    "overwhelm":  "finding a way through",
    "presence":   "presence",
}


def startup_message(state: IdentityState, base: str = "Welcome back.") -> str:
    """
    Returns the startup greeting line.
    Format: "Welcome back. Last time we were moving toward clarity around the OS."
    Falls back to plain "Welcome back." if state is empty.
    """
    if state.is_empty():
        return base

    direction = _DIRECTION_PHRASE.get(state.emotional_direction, "working on")
    project   = _PROJECT_PHRASE.get(state.active_project, "")
    theme     = _THEME_PHRASE.get(state.session_theme, state.session_theme)

    if project and theme:
        return f"{base} Last time we were {direction} {theme} around {project}."
    if theme:
        return f"{base} Last time we were {direction} {theme}."
    if project:
        return f"{base} Last time we were working on {project}."
    return base


def recall_response(state: IdentityState) -> str:
    """
    Answers "What were we doing?" / "What have I been working on?"
    Returns meaning, not transcript.
    """
    if state.is_empty():
        return "I don't have enough across sessions yet to give you a clear picture."

    parts = []

    project = _PROJECT_PHRASE.get(state.active_project, "")
    theme   = _THEME_PHRASE.get(state.session_theme, state.session_theme)
    direction = _DIRECTION_PHRASE.get(state.emotional_direction, "working on")

    if project and theme:
        parts.append(f"We were {direction} {theme} around {project}.")
    elif project:
        parts.append(f"Most of the energy was on {project}.")
    elif theme:
        parts.append(f"The main thread was {theme}.")

    if state.what_changed:
        parts.append(f"Since last time: {', '.join(state.what_changed)} came up.")

    if state.what_stayed:
        topics = ", ".join(state.what_stayed[:2])
        parts.append(f"{topics} keeps returning.")

    if state.what_matters and not (project or theme):
        parts.append(state.what_matters)

    return " ".join(parts) if parts else "The direction has been building."


def shift_note(state: IdentityState) -> str | None:
    """
    Returns a short note about a relationship shift, or None.
    Used to supplement the startup message.
    """
    if state.relationship_shift == "closer":
        return "Something shifted — you feel more open than last time."
    if state.relationship_shift == "more distant":
        return None  # don't comment on withdrawal — just be present
    return None
