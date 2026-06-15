"""
avatar_runtime/transition_engine.py — produces cross-fade parameters.

When the animation brain signals blending=True, this engine computes
blend weights so the Blender/Unity bridge can cross-fade between clips.

Outputs a simple {from_clip, to_clip, progress} dict that bridges consume.
Progress advances linearly over the blend_duration window.
"""
from __future__ import annotations
import time

_BLEND_DURATION = 0.5   # seconds for full cross-fade


class TransitionEngine:
    def __init__(self):
        self._blend_start: float = 0.0
        self._from_clip:   str   = ""
        self._to_clip:     str   = ""
        self._active:      bool  = False

    def start(self, from_clip: str, to_clip: str) -> None:
        self._from_clip  = from_clip
        self._to_clip    = to_clip
        self._blend_start = time.monotonic()
        self._active     = True

    def tick(self) -> dict:
        """
        Returns current blend state.
        {active, from_clip, to_clip, progress (0–1), complete}
        """
        if not self._active:
            return {"active": False, "from_clip": "", "to_clip": self._to_clip,
                    "progress": 1.0, "complete": True}

        elapsed  = time.monotonic() - self._blend_start
        progress = min(1.0, elapsed / _BLEND_DURATION)
        complete = progress >= 1.0

        if complete:
            self._active = False

        return {
            "active":     self._active or not complete,
            "from_clip":  self._from_clip,
            "to_clip":    self._to_clip,
            "progress":   round(progress, 3),
            "complete":   complete,
        }

    def is_blending(self) -> bool:
        return self._active
