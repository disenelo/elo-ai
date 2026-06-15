"""
desktop/desktop_presence.py — eLo observes the desktop, never controls it.

Shadow mode: reads window state and produces soft context for the conversation.
Runs as a background observer. Does not modify any window or application.

Output: a short context string injected into the prompt when relevant.
        Empty string if no useful context can be derived.

Usage:
    from desktop.desktop_presence import observe, shadow_context

    # call once per turn — non-blocking
    ctx = shadow_context()   # "" or "You're in Blender right now."
"""
from __future__ import annotations

from desktop.window_state import get as _get_window, WindowState


# activity → observation template
_ACTIVITY_OBS: dict[str, str] = {
    "coding":       "You're in the code right now.",
    "creating":     "You're in creative tools right now.",
    "designing":    "You're working in a design tool.",
    "writing":      "You're in writing mode.",
    "terminal":     "You're in the terminal.",
    "browsing":     "You're in a browser.",
    "communicating": "You're in a communication tool.",
    "listening":    "You've got music on.",
    "watching":     "You're watching something.",
}

# apps that warrant a named mention (more specific than activity)
_NAMED_APPS = {"Blender", "Unity", "Obsidian", "Xcode", "Figma"}


def observe() -> WindowState:
    """Read-only window state. Always safe to call."""
    return _get_window()


def shadow_context() -> str:
    """
    Return a short context string for the conversation prompt.
    Returns "" if desktop access not available or activity not meaningful.
    """
    ws = observe()

    if not ws.available or not ws.app:
        return ""

    # named app mention
    for name in _NAMED_APPS:
        if name.lower() in ws.app.lower():
            return f"You're in {name} right now."

    # activity-based
    obs = _ACTIVITY_OBS.get(ws.activity, "")
    return obs
