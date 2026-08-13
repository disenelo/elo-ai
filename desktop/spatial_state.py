"""
desktop/spatial_state.py — eLo's spatial awareness layer.

Python's half of the spatial contract:
  - Gets all visible window bounds via osascript (macOS)
  - Reads eLo's current window attachment from presence_state.json
  - Reads eLo's precise position from elo_spatial.json (written by Unity)
  - Calculates distances, finds nearest windows, plans routes

Unity's half (writes elo_spatial.json):
  {
    "pos_x": 0.5,        # normalised 0-1 screen X
    "pos_y": 0.2,        # normalised 0-1 screen Y (0 = top)
    "height_px": 120,    # eLo's pixel height at current scale
    "window": "Chrome",  # window eLo is currently on
    "screen_w": 2560,
    "screen_h": 1440,
    "_ts": 1234567890
  }

Python writes movement intents to blender_state.json as before.
New intent: {"name": "jump_to_app", "app": "Google Chrome"}
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional

_ROOT              = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PRESENCE_PATH     = os.path.join(_ROOT, "blender", "presence_state.json")
_SPATIAL_PATH      = os.path.join(_ROOT, "blender", "elo_spatial.json")


@dataclass
class WindowBounds:
    app:    str
    title:  str
    x:      int
    y:      int
    w:      int
    h:      int

    @property
    def centre_x(self) -> int:
        return self.x + self.w // 2

    @property
    def centre_y(self) -> int:
        return self.y + self.h // 2

    @property
    def top_edge(self) -> int:
        return self.y

    @property
    def right_edge(self) -> int:
        return self.x + self.w


@dataclass
class EloSpatial:
    pos_x:     float = 0.5     # normalised screen X
    pos_y:     float = 0.1     # normalised screen Y
    height_px: int   = 120     # pixel height
    window:    str   = ""      # window eLo is on
    screen_w:  int   = 2560
    screen_h:  int   = 1440

    @property
    def pixel_x(self) -> int:
        return int(self.pos_x * self.screen_w)

    @property
    def pixel_y(self) -> int:
        return int(self.pos_y * self.screen_h)

    def distance_to(self, win: WindowBounds) -> float:
        """Euclidean distance from eLo to the nearest edge of a window."""
        dx = max(0, win.x - self.pixel_x, self.pixel_x - win.right_edge)
        dy = max(0, win.top_edge - self.pixel_y, self.pixel_y - (win.y + win.h))
        return (dx ** 2 + dy ** 2) ** 0.5


def get_elo_spatial() -> EloSpatial:
    """
    Read eLo's current position from elo_spatial.json (Unity writes this).
    Falls back to presence_state.json for window attachment if spatial file absent.
    """
    spatial = EloSpatial()

    # Try full spatial file first (Unity writes this when implemented)
    try:
        with open(_SPATIAL_PATH, encoding="utf-8") as f:
            d = json.load(f)
        spatial.pos_x     = float(d.get("pos_x", 0.5))
        spatial.pos_y     = float(d.get("pos_y", 0.1))
        spatial.height_px = int(d.get("height_px", 120))
        spatial.window    = d.get("window", "")
        spatial.screen_w  = int(d.get("screen_w", 2560))
        spatial.screen_h  = int(d.get("screen_h", 1440))
        return spatial
    except Exception:
        pass

    # Fallback: read window from presence_state.json
    try:
        with open(_PRESENCE_PATH, encoding="utf-8") as f:
            p = json.load(f)
        spatial.window = p.get("frontWindowName", "")
    except Exception:
        pass

    return spatial


def get_windows() -> list[WindowBounds]:
    """
    Return bounds of all visible, non-minimised windows via osascript.
    Filters out eLo's own Presence window.
    """
    script = """
tell application "System Events"
    set result to {}
    set procs to every process where background only is false and visible is true
    repeat with proc in procs
        set pname to name of proc
        try
            repeat with win in windows of proc
                set pos to position of win
                set sz to size of win
                set wtitle to name of win
                set end of result to pname & "|||" & wtitle & "|||" & (item 1 of pos as string) & "|||" & (item 2 of pos as string) & "|||" & (item 1 of sz as string) & "|||" & (item 2 of sz as string)
            end repeat
        end try
    end repeat
    return result
end tell
"""
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return []

        windows: list[WindowBounds] = []
        for line in r.stdout.strip().split(", "):
            parts = line.strip().split("|||")
            if len(parts) != 6:
                continue
            app, title, x, y, w, h = parts
            app = app.strip()
            if "DISENELO" in app or "Presence" in app:
                continue
            try:
                windows.append(WindowBounds(
                    app=app, title=title.strip(),
                    x=int(float(x)), y=int(float(y)),
                    w=int(float(w)), h=int(float(h)),
                ))
            except ValueError:
                pass
        return windows
    except Exception:
        return []


def nearest_windows(elo: EloSpatial, windows: list[WindowBounds], limit: int = 5) -> list[tuple[WindowBounds, float]]:
    """Return windows sorted by distance to eLo, with distances."""
    scored = [(w, elo.distance_to(w)) for w in windows]
    return sorted(scored, key=lambda x: x[1])[:limit]


def find_window(app_name: str, windows: list[WindowBounds]) -> Optional[WindowBounds]:
    """Find a window by app name (case-insensitive partial match)."""
    q = app_name.lower()
    for w in windows:
        if q in w.app.lower() or q in w.title.lower():
            return w
    return None


def spatial_summary(elo: EloSpatial, windows: list[WindowBounds]) -> str:
    """One-paragraph text description of eLo's spatial context — injected into prompts."""
    parts: list[str] = []

    if elo.window:
        parts.append(f"eLo is on '{elo.window}'")
    else:
        parts.append("eLo's window attachment unknown")

    if windows:
        nearest = nearest_windows(elo, windows, limit=3)
        labels  = [f"{w.app} ({int(d)}px away)" for w, d in nearest]
        parts.append(f"nearest windows: {', '.join(labels)}")

    chrome = find_window("chrome", windows) or find_window("safari", windows)
    if chrome:
        dist = elo.distance_to(chrome)
        parts.append(f"browser is {int(dist)}px away")

    return "[SPATIAL] " + ". ".join(parts) + "."
