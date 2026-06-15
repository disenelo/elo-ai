"""
desktop/window_state.py — read-only snapshot of what's on the desktop.

Shadow mode: eLo observes, never controls. No window manipulation.
Collects context only — app name, window title, general activity class.

Requires macOS. Uses osascript + optional accessibility APIs.
Falls back gracefully if permissions are not granted.
"""
from __future__ import annotations
import subprocess
import re
from dataclasses import dataclass


# activity classes — coarse grouping, not app-specific
_APP_ACTIVITY: dict[str, str] = {
    "Xcode":          "coding",
    "Visual Studio Code": "coding",
    "code":           "coding",
    "Terminal":       "terminal",
    "iTerm":          "terminal",
    "Blender":        "creating",
    "Unity":          "creating",
    "Figma":          "designing",
    "Sketch":         "designing",
    "Notion":         "writing",
    "Obsidian":       "writing",
    "Notes":          "writing",
    "Safari":         "browsing",
    "Chrome":         "browsing",
    "Firefox":        "browsing",
    "Slack":          "communicating",
    "Discord":        "communicating",
    "Mail":           "communicating",
    "Music":          "listening",
    "Spotify":        "listening",
    "YouTube":        "watching",
}


@dataclass
class WindowState:
    app:      str = ""        # active application name
    title:    str = ""        # window title (may be empty if not accessible)
    activity: str = "unknown" # coarse activity class
    available: bool = True    # False if accessibility not permitted

    def is_creative(self) -> bool:
        return self.activity in ("coding", "creating", "designing", "writing")

    def is_idle(self) -> bool:
        return not self.app


def get() -> WindowState:
    """
    Return a snapshot of the current foreground window.
    Read-only. Never raises — returns WindowState(available=False) on any failure.
    """
    try:
        script = (
            'tell application "System Events" to get {name of first process '
            'whose frontmost is true, name of front window of first process '
            'whose frontmost is true}'
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode != 0:
            # no accessibility permission — return gracefully
            return WindowState(available=False)

        parts = [p.strip() for p in result.stdout.strip().split(",", 1)]
        app   = parts[0] if parts else ""
        title = parts[1] if len(parts) > 1 else ""

        # strip path from title if it sneaked in
        if "/" in title:
            title = title.split("/")[-1]

        activity = _classify(app)
        return WindowState(app=app, title=title, activity=activity)

    except Exception:
        return WindowState(available=False)


def _classify(app: str) -> str:
    for key, cls in _APP_ACTIVITY.items():
        if key.lower() in app.lower():
            return cls
    return "unknown"
