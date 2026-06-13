"""
desktop_avatar/movement_controller.py — maps presence state + context to avatar movement.

Phase F — DESKTOP → AVATAR.

Translates avatar presence state and desktop context into motion commands
for the renderer.

Rules (from spec):
    - No interruptions
    - Presence > notifications
    - Idle: moves slowly
    - Thinking: sits
    - Excited: walks
"""

from __future__ import annotations
import time
from desktop_avatar.avatar_renderer import get as _get_renderer
from desktop.context_detector import observe as _desktop_observe, current_app as _current_app

# ── presence mode → motion mapping ───────────────────────────────────────────

_MODE_MOTION: dict[str, str] = {
    "idle":        "idle",
    "observing":   "look",
    "thinking":    "sit",
    "building":    "walk",
    "celebrating": "jump",
    "exploring":   "walk",
    "resting":     "sit",
}

# ── timing ────────────────────────────────────────────────────────────────────

_MIN_MOTION_CHANGE = 6.0   # seconds between motion changes
_last_motion_time: float = 0.0


def update(presence_state: dict) -> None:
    """
    Map the current presence state to a renderer motion.
    Also checks desktop context for observation opportunities.
    """
    renderer = _get_renderer()
    if not renderer._running:
        return

    mode   = presence_state.get("mode", "idle")
    motion = _MODE_MOTION.get(mode, "idle")

    now = time.monotonic()
    if (now - _last_motion_time) >= _MIN_MOTION_CHANGE:
        renderer.set_motion(motion)
        _update_last_motion_time()

    # surface desktop observation as speech (non-interrupting)
    _obs = _desktop_observe()
    if _obs and not renderer._speech:
        renderer.say(_obs, duration=3.0)


def _update_last_motion_time() -> None:
    global _last_motion_time
    _last_motion_time = time.monotonic()
