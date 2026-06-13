"""
desktop/context_detector.py — surfaces eLo-relevant observations from desktop state.

Observation only. No control.

Examples:
    "Looks like Blender has been open a while."
    "You opened Obsidian."
    "Terminal has been open for a while."
"""

from __future__ import annotations
import time
from desktop.window_watcher import get as _win_get

# Map app name fragments → eLo-friendly name
_APP_LABELS: dict[str, str] = {
    "Blender":   "Blender",
    "Obsidian":  "Obsidian",
    "Unity":     "Unity",
    "Xcode":     "Xcode",
    "VS Code":   "VS Code",
    "Visual Studio Code": "VS Code",
    "Terminal":  "Terminal",
    "iTerm":     "Terminal",
    "Finder":    "Finder",
    "Safari":    "Safari",
    "Chrome":    "Chrome",
    "Firefox":   "Firefox",
    "Figma":     "Figma",
    "Sketch":    "Sketch",
    "Notion":    "Notion",
}

# Minimum seconds an app must be frontmost before "open a while" observation
_DWELL_THRESHOLD = 300   # 5 minutes

_app_start_times: dict[str, float] = {}
_last_observation_app: str = ""


def _label(app_name: str) -> str:
    """Normalise app name to a friendly label, or return raw name."""
    for key, label in _APP_LABELS.items():
        if key.lower() in app_name.lower():
            return label
    return app_name


def observe() -> str | None:
    """
    Check current desktop state and return an observation string, or None.
    Fires at most once per app-change event.
    """
    global _last_observation_app

    state = _win_get()
    app   = state.get("frontmost_app", "")
    if not app:
        return None

    now   = time.monotonic()
    label = _label(app)

    # track dwell time
    if app not in _app_start_times:
        _app_start_times[app] = now

    dwell = now - _app_start_times.get(app, now)

    # new app came to front
    if state.get("changed") and app != _last_observation_app:
        _last_observation_app = app
        # reset dwell for the newly focused app
        _app_start_times[app] = now
        return f"You opened {label}."

    # app has been open a while (only fire once per threshold crossing)
    if dwell >= _DWELL_THRESHOLD and _last_observation_app != f"{app}_dwell":
        _last_observation_app = f"{app}_dwell"
        return f"Looks like {label} has been open a while."

    return None


def current_app() -> str:
    """Return the current frontmost app label."""
    state = _win_get()
    return _label(state.get("frontmost_app", ""))
