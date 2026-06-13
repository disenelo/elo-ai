"""
desktop/window_watcher.py — macOS frontmost app + open window detection.

Observation only. No control.

Returns:
    {
        "frontmost_app": str,   # e.g. "Blender", "Obsidian", "Terminal"
        "open_apps":     list,  # all visible app names
        "changed":       bool,  # True if frontmost changed since last call
    }
"""

from __future__ import annotations
import subprocess
import json

_last_frontmost: str = ""


def get() -> dict:
    """Poll the current frontmost app and open windows via osascript."""
    global _last_frontmost

    frontmost = _frontmost_app()
    open_apps = _open_apps()
    changed   = (frontmost != _last_frontmost) and bool(frontmost)
    _last_frontmost = frontmost

    return {
        "frontmost_app": frontmost,
        "open_apps":     open_apps,
        "changed":       changed,
    }


def _frontmost_app() -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true'],
            capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _open_apps() -> list:
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to get name of every application process whose visible is true'],
            capture_output=True, text=True, timeout=2
        )
        raw = result.stdout.strip()
        # osascript returns comma-separated list
        return [a.strip() for a in raw.split(",") if a.strip()]
    except Exception:
        return []
