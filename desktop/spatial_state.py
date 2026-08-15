"""
desktop/spatial_state.py — eLo's spatial awareness layer.

Python's half of the spatial contract:
  - Gets all visible window bounds via osascript (macOS)
  - Reads eLo's current window attachment from presence_state.json
  - Reads eLo's precise position from elo_spatial.json (written by Unity)
  - Calculates distances, finds nearest windows (does NOT plan routes — see faculties/spatial/)

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
import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional

_log = logging.getLogger(__name__)

_ROOT              = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PRESENCE_PATH     = os.path.join(_ROOT, "blender", "presence_state.json")
_SPATIAL_PATH      = os.path.join(_ROOT, "blender", "elo_spatial.json")

# WO-118: dedup — track last_move _ts values already fed to route_memory
_seen_move_ts: set[float] = set()
# WO-118 Rule 1 alarm: consecutive reads where body has goal but no last_move
_absent_last_move_count: int = 0


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
class GazeSpatial:
    """eLo's current gaze direction — written to elo_spatial.json by Unity (WO-099 UP channel)."""
    x:         float = 0.5    # normalised screen X gaze aims at
    y:         float = 0.5    # normalised screen Y
    win_id:    int   = 0      # window ID under gaze (0 = none)
    window:    str   = ""     # window name under gaze
    on_window: bool  = False  # True when gaze lands on a known window
    issued_by: str   = ""     # "brain" | "reflex" | ""


@dataclass
class EloSpatial:
    pos_x:     float = 0.5     # normalised screen X (Unity key: "x")
    pos_y:     float = 0.1     # normalised screen Y (Unity key: "y")
    height_px: int   = 120     # pixel height (Unity key: "height")
    window:    str   = ""      # window eLo is on
    edge:      str   = ""      # "bottom" | "top" | "left" | "right" | ""
    screen_w:  int   = 2560
    screen_h:  int   = 1440
    gaze:      "GazeSpatial | None" = None   # WO-099: gaze awareness UP

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
    Unity keys: x/y/height (not pos_x/pos_y/height_px).
    """
    spatial = EloSpatial()

    # Try full spatial file first (Unity writes this)
    try:
        with open(_SPATIAL_PATH, encoding="utf-8") as f:
            d = json.load(f)
        # WO-100: strict key reads — KeyError if Unity key absent, caught and logged below
        spatial.pos_x     = float(d["x"])
        spatial.pos_y     = float(d["y"])
        spatial.height_px = int(d["height"])
        spatial.window    = d.get("window", "")
        spatial.edge      = d.get("edge", "")
        spatial.screen_w  = int(d.get("screen_w", 2560))
        spatial.screen_h  = int(d.get("screen_h", 1440))
        # WO-118: feed completed moves into route_memory on first read per move
        global _absent_last_move_count
        _lm = d.get("last_move")
        if isinstance(_lm, dict):
            _absent_last_move_count = 0  # body is reporting — reset Rule 1 alarm
            _move_ts = float(_lm.get("_ts", 0.0))
            if _move_ts and _move_ts not in _seen_move_ts:
                _seen_move_ts.add(_move_ts)
                try:
                    from self.route_memory import remember_route as _rr
                    _retries    = int(_lm.get("retries", 0))
                    _smoothness = max(0.0, 1.0 - _retries * 0.2)
                    _rr(
                        goal_surface=str(_lm.get("goal", "")),
                        legs=list(_lm.get("legs", [])),
                        arrived=bool(_lm.get("arrived", False)),
                        fell=bool(_lm.get("fell", False)),
                        duration_s=float(_lm.get("cost_secs", 0.0)),
                        smoothness=_smoothness,
                        ack_id=str(_move_ts),
                        ack_received=True,
                    )
                except Exception as _re:
                    _log.warning("get_elo_spatial: route_memory write failed — %s", _re)
        else:
            # WO-118 Rule 1: body has active goal/route but last_move absent → may have gone silent
            if d.get("goal") or d.get("route"):
                _absent_last_move_count += 1
                if _absent_last_move_count >= 3:
                    _log.warning(
                        "WO-118 Rule 1: body navigating (goal=%r) but last_move absent "
                        "for %d consecutive reads — body may have gone silent.",
                        d.get("goal"), _absent_last_move_count,
                    )
            else:
                _absent_last_move_count = 0
        # WO-099: read gaze UP — "eLo KNOWS what he's looking at"
        _g = d.get("gaze")
        if isinstance(_g, dict):
            spatial.gaze = GazeSpatial(
                x=float(_g.get("x", 0.5)),
                y=float(_g.get("y", 0.5)),
                win_id=int(_g.get("win_id", 0)),
                window=str(_g.get("window", "")),
                on_window=bool(_g.get("on_window", False)),
                issued_by=str(_g.get("issued_by", "")),
            )
        return spatial
    except Exception as _e:
        _log.warning("get_elo_spatial: elo_spatial.json key read failed — %s", _e)

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
        parts.append(f"eLo is on '{elo.window}'" + (f" ({elo.edge} edge)" if elo.edge else ""))
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

    # WO-099: gaze awareness UP — only say he's looking if the state says so (ADR-Exec-001)
    if elo.gaze and elo.gaze.on_window and elo.gaze.window:
        src = f" (by {elo.gaze.issued_by})" if elo.gaze.issued_by else ""
        parts.append(f"gaze on '{elo.gaze.window}'{src}")
    elif elo.gaze and not elo.gaze.on_window:
        parts.append("gaze on open desktop (no window)")

    return "[SPATIAL] " + ". ".join(parts) + "."
