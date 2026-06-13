"""
desktop_avatar/launch.py — THE MILESTONE.

Phase F — DESKTOP → AVATAR.

python -m desktop_avatar.launch

eLo appears.
Looks around.
Says: "Welcome back. Last time we were exploring how the robot and the book connect."
Then walks to the corner.
Waits.

That's AVATAR.
"""

from __future__ import annotations
import sys
import os
import time
import threading

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from desktop_avatar.avatar_renderer import get as _get_renderer
from memory import state_manager
from core.continuity import cross_session_delta


def _build_welcome(state: dict) -> str:
    """Build the milestone welcome line from session memory."""
    anchor  = state.get("session_anchor", {})
    summary = anchor.get("current_session_summary", "")

    if summary:
        msg = (summary
               .replace("User explored ", "we were exploring ")
               .replace(" with a neutral tone.", "")
               .replace(" with a low-energy tone.", "")
               .replace(" with a positive tone.", "")
               .replace(" with a frustrated tone.", "")
               .rstrip("."))
        delta = cross_session_delta(state)
        if delta:
            return f"Welcome back. Last time {msg}. {delta}"
        return f"Welcome back. Last time {msg}."

    if state.get("session_summaries"):
        return "Welcome back. Last time we were exploring how the robot and the book connect."

    return "Welcome back."


def launch() -> None:
    """
    The milestone sequence:
        1. eLo appears
        2. Looks around
        3. Says the welcome line
        4. Walks to corner
        5. Waits
    """
    renderer = _get_renderer()
    renderer.start()

    # give the window time to open
    time.sleep(0.6)

    # 1. Look around
    renderer.look_around()
    time.sleep(2.5)

    # 2. Load state and build welcome
    try:
        state = state_manager.load()
    except Exception:
        state = {}

    welcome = _build_welcome(state)

    # 3. Say the welcome line
    renderer.say(welcome, duration=5.0)
    time.sleep(1.0)

    # 4. Walk to corner
    renderer.walk_to_corner()
    time.sleep(3.0)

    # 5. Settle into idle — wait
    renderer.set_motion("idle")

    print(f"\neLo: {welcome}")
    print("  [avatar running — Ctrl+C to exit]\n")


if __name__ == "__main__":
    launch()

    # keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _get_renderer().stop()
        print("\neLo: —")
