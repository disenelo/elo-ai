"""
faculties/spatial/spatial_faculty.py — WO-120

Spatial Faculty — Vol XIII canonical owner of geometry and reachability.

Python role: reason about space (this file).
Unity role: execute movement (EloDesktopNav.cs). [Ruling E]

Each turn:
  1. Read current position and last_move from elo_spatial.json (ground truth).
  2. Map surface → affordances (what eLo can do here).
  3. Score recent route success from route_memory.
  4. Return context_block() for the Executive prompt.

Split rule: this file holds the boundary. No movement commands issued here.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

_ROOT         = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SPATIAL_PATH = os.path.join(_ROOT, "blender", "elo_spatial.json")

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpatialContext:
    """Ground-truth spatial snapshot for one turn."""
    surface:           str          # "window_top" | "window_body" | "desktop_floor" | ""
    affordances:       tuple        # what eLo can do on this surface
    last_move_goal:    str          # "" if no completed move yet
    last_move_arrived: bool | None  # None = no move yet
    last_move_fell:    bool
    recent_reached:    int          # out of last 5 route attempts
    recent_total:      int


def assemble() -> SpatialContext:
    """
    Read ground truth from elo_spatial.json and route_memory.
    Returns a SpatialContext. Never raises — falls back to empty on any error.
    """
    from runtime.affordances import affordances_for
    from self.route_memory import recent_routes as _recent_routes

    surface = "desktop_floor"
    last_move_goal    = ""
    last_move_arrived = None
    last_move_fell    = False

    try:
        with open(_SPATIAL_PATH, encoding="utf-8") as f:
            d = json.load(f)

        edge = d.get("edge", "")
        win  = d.get("window", "")
        if edge == "top":
            surface = "window_top"
        elif edge == "bottom":
            surface = "window_bottom"
        elif win:
            surface = "window_body"
        else:
            surface = "desktop_floor"

        lm = d.get("last_move")
        if isinstance(lm, dict):
            last_move_goal    = str(lm.get("goal", ""))
            last_move_arrived = bool(lm.get("arrived", False))
            last_move_fell    = bool(lm.get("fell", False))
    except Exception as e:
        _log.debug("SpatialFaculty.assemble: %s", e)

    recent = _recent_routes(5)
    recent_reached = sum(1 for r in recent if r.get("arrived"))

    return SpatialContext(
        surface=surface,
        affordances=affordances_for(surface),
        last_move_goal=last_move_goal,
        last_move_arrived=last_move_arrived,
        last_move_fell=last_move_fell,
        recent_reached=recent_reached,
        recent_total=len(recent),
    )


def context_block() -> str:
    """
    Return a prompt-ready spatial context block for the Executive.
    Empty string on any failure — never blocks the turn.
    """
    try:
        ctx = assemble()
        parts: list[str] = []

        if ctx.surface:
            affs = ", ".join(ctx.affordances) if ctx.affordances else "—"
            parts.append(f"surface={ctx.surface} can=[{affs}]")

        if ctx.last_move_arrived is not None:
            if ctx.last_move_arrived:
                outcome = "arrived"
            elif ctx.last_move_fell:
                outcome = "fell"
            else:
                outcome = "missed"
            parts.append(f"last_move→{ctx.last_move_goal or '?'}:{outcome}")

        if ctx.recent_total > 0:
            parts.append(f"reach={ctx.recent_reached}/{ctx.recent_total}")

        return "[SPATIAL] " + " | ".join(parts) if parts else ""
    except Exception as e:
        _log.debug("SpatialFaculty.context_block: %s", e)
        return ""
