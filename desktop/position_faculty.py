"""
desktop/position_faculty.py — WO-023: top-bias + keep-out position computer.

Computes where eLo should anchor on screen each turn and writes
blender/presence_position.json (atomic).  Unity reads this file to bias
eLo's idle/ambient anchor point.

Policy (David 2026-08-01):
  1. Default anchor = top strip of screen (PREFERRED_Y_NORM from top).
  2. Never sit over the active window's CONTROL REGION — the bottom
     CONTROL_BOTTOM_FRAC of the focused window where buttons/toolbars
     and text-entry fields tend to live.
  3. No jitter: this file is the DESIRED position, not a jump command.
     Unity smooths towards it.  Move only when eLo would otherwise
     land in a keep-out zone.

Output schema — blender/presence_position.json:
  {
    "target_x":          0.85,   # normalised 0-1 screen X
    "target_y":          0.07,   # normalised 0-1 screen Y (0 = top)
    "keep_out_applied":  false,  # true if target was nudged away from control region
    "keep_out": {
      "x_min": 0.0, "x_max": 1.0,
      "y_min": 0.85, "y_max": 1.0  # normalised; 0 = top
    },
    "active_window":     "Code",
    "active_window_px":  {"x": 0, "y": 0, "w": 2560, "h": 1440},
    "screen_w":          2560,
    "screen_h":          1440,
    "_ts":               1234567890.0
  }
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

from desktop.spatial_state import EloSpatial, WindowBounds, get_elo_spatial, get_windows

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUT     = os.path.join(_ROOT, "blender", "presence_position.json")

# ── Tuning constants ─────────────────────────────────────────────────────────
PREFERRED_Y_NORM      = 0.07   # default vertical anchor: top 7% of screen
PREFERRED_X_NORM      = 0.85   # default horizontal anchor: right-of-centre
CONTROL_BOTTOM_FRAC   = 0.12   # bottom 12% of focused window = control region
TOP_SAFE_Y_NORM       = 0.06   # fallback when keep-out would push eLo up

# ── Window-data cache (avoids osascript spam on rapid turns) ─────────────────
_WIN_CACHE_TTL = 5.0   # seconds
_win_cache: list[WindowBounds] = []
_win_cache_ts: float = 0.0


def _cached_windows() -> list[WindowBounds]:
    global _win_cache, _win_cache_ts
    now = time.time()
    if now - _win_cache_ts < _WIN_CACHE_TTL:
        return _win_cache
    try:
        _win_cache    = get_windows()
        _win_cache_ts = now
    except Exception:
        pass
    return _win_cache


# ── Core computation ─────────────────────────────────────────────────────────

def compute_position(
    elo:     Optional[EloSpatial]       = None,
    windows: Optional[list[WindowBounds]] = None,
) -> dict:
    """
    Compute the top-bias target position and keep-out zone.

    Parameters can be pre-fetched (e.g. reusing data already gathered for
    the spatial summary prompt) or left None to fetch fresh.

    Returns the presence_position dict (same schema as the JSON file).
    """
    if elo is None:
        try:
            elo = get_elo_spatial()
        except Exception:
            elo = EloSpatial()

    if windows is None:
        windows = _cached_windows()

    screen_w = elo.screen_w or 2560
    screen_h = elo.screen_h or 1440

    # Find the focused window by name (presence_state.json → elo.window)
    active_win: Optional[WindowBounds] = None
    active_name = elo.window or ""
    if active_name and windows:
        q = active_name.lower()
        for w in windows:
            if q in w.app.lower() or q in w.title.lower():
                active_win = w
                break

    # ── Compute keep-out rect ────────────────────────────────────────────────
    # Bottom CONTROL_BOTTOM_FRAC of the active window — normalised to screen.
    keep_out: dict = {"x_min": 0.0, "x_max": 1.0, "y_min": 1.0, "y_max": 1.0}
    active_win_px: dict = {}

    if active_win:
        active_win_px = {
            "x": active_win.x,
            "y": active_win.y,
            "w": active_win.w,
            "h": active_win.h,
        }
        control_start_px  = active_win.y + active_win.h * (1.0 - CONTROL_BOTTOM_FRAC)
        control_end_px    = active_win.y + active_win.h
        keep_out = {
            "x_min": active_win.x / screen_w,
            "x_max": (active_win.x + active_win.w) / screen_w,
            "y_min": control_start_px / screen_h,
            "y_max": min(1.0, control_end_px / screen_h),
        }

    # ── Compute target ───────────────────────────────────────────────────────
    target_x = PREFERRED_X_NORM
    target_y = PREFERRED_Y_NORM
    keep_out_applied = False

    # Check if the default target lands inside the control region.
    # (Unlikely with PREFERRED_Y_NORM=0.07, but possible if the active window
    # spans from y≈0 and its control region starts very high.)
    if _in_keep_out(target_x, target_y, keep_out):
        target_y = TOP_SAFE_Y_NORM
        keep_out_applied = True

    return {
        "target_x":         round(target_x, 4),
        "target_y":         round(target_y, 4),
        "keep_out_applied": keep_out_applied,
        "keep_out": {k: round(v, 4) for k, v in keep_out.items()},
        "active_window":    active_name,
        "active_window_px": active_win_px,
        "screen_w":         screen_w,
        "screen_h":         screen_h,
        "_ts":              round(time.time(), 3),
    }


def _in_keep_out(x: float, y: float, ko: dict) -> bool:
    """Return True if the normalised point (x, y) falls inside the keep-out rect."""
    return (
        ko["x_min"] <= x <= ko["x_max"]
        and ko["y_min"] <= y <= ko["y_max"]
    )


# ── I/O ──────────────────────────────────────────────────────────────────────

def emit(
    elo:     Optional[EloSpatial]         = None,
    windows: Optional[list[WindowBounds]] = None,
    path:    str                           = _OUT,
) -> dict:
    """
    Compute the position hint and write it atomically to presence_position.json.
    Returns the dict (same as compute_position).
    """
    pos = compute_position(elo=elo, windows=windows)
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(pos, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass
    return pos
