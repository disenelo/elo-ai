"""
blender/blender_bridge.py — eLo presence preview.

Standalone test runner and importable bridge.

Run:
    python blender_bridge.py
    python blender_bridge.py "I think I found the opening scene."
    python blender_bridge.py "The project suddenly feels alive."
    python blender_bridge.py "I feel disconnected."

The module also reads blender/blender_state.json written by animation_router
when running inside the main loop.
"""

from __future__ import annotations
import sys
import os
import json

# allow running from blender/ or project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from blender.avatar_driver    import drive
from blender.state_visualiser import show

_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")


def from_text(text: str) -> dict:
    """Run the full cognition pipeline on text. Returns {motion, state}."""
    from core.attention         import compute as attn_compute
    from runtime.executive      import decide  as exec_decide
    from avatar.presence_engine import compute as presence_compute
    from avatar.motion_mapper   import map     as motion_map

    att      = attn_compute(text, {}, {})
    ex       = exec_decide(att, user_input=text)
    presence = presence_compute(att, ex)
    motion   = motion_map(presence)
    return {"motion": motion, "state": presence}


def from_file() -> dict:
    """Read blender_state.json written by animation_router._to_blender()."""
    if not os.path.exists(_STATE_PATH):
        return {}
    with open(_STATE_PATH) as f:
        data = json.load(f)
    # animation_router writes {motion: ..., state: ...}
    if "motion" in data:
        return data
    # backwards-compat: flat motion dict
    return {"motion": data, "state": {}}


def run(text: str = "") -> None:
    if text:
        result = from_text(text)
    else:
        result = from_file()
        if not result:
            print("[eLo] No state. Pass text input or write blender/blender_state.json.")
            return

    show(result["state"], result["motion"])
    drive(result["motion"])


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    run(text)
