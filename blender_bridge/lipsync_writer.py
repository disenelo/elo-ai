"""
blender_bridge/lipsync_writer.py — patches blender_state.json with lipsync shapes.

Writes mouth blendshape values directly into expression.shape_keys of the main
state file at ~50ms intervals during speech. The receiver (EloOSAvatarReceiver)
reads that same file, so lipsync shapes arrive without any field-path change.

Between cognitive turns (which rewrite the whole file) this holds the lipsync
shapes. A cognitive turn overwrites for ~1 frame — visually imperceptible.
"""
from __future__ import annotations
import json
import os
import time

_ROOT               = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH         = os.path.join(_ROOT, "blender", "blender_state.json")
_LIPSYNC_STATE_PATH = os.path.join(_ROOT, "blender", "lipsync_state.json")

_ALL_MOUTH = [
    "Ah", "Eh", "Ee", "Ai", "Oooh", "Shock-Oooo",
    "Mbp", "Mmmm", "Fv", "FvS", "S", "Huh",
    "MouthOpen.Slightly", "MouthOpen.Wide",
    "MouthWidth.L", "MouthWidth.R",
    "Puff-EyebrowsRaise",
    # JawOpening intentionally omitted — Unity auto-derives it from the strongest open viseme.
    # Sending it here would conflict with EloOSAvatarReceiver's jaw calculation.
]


def write_active_flag(active: bool, text: str = "") -> None:
    """Write lipsync_state.json — Unity reads this for IsSpeaking gate and message serialization."""
    try:
        payload: dict = {"active": active, "_ts": round(time.time(), 3)}
        if text:
            payload["text"] = text
        tmp = _LIPSYNC_STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, _LIPSYNC_STATE_PATH)
    except Exception:
        pass


def write_lipsync(shape_keys: dict[str, float], *, active: bool = True,
                  head_lean: float | None = None, text: str = "") -> bool:
    """Patch expression.shape_keys in blender_state.json with mouth shapes,
    and write active flag to lipsync_state.json so Unity's IsSpeaking gate works."""
    try:
        try:
            with open(_STATE_PATH, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            payload = {}

        if "expression" not in payload:
            payload["expression"] = {"shape_keys": {}, "head_lean": 0.0,
                                     "pacing": "steady", "intensity": 0.5}
        payload["expression"]["shape_keys"].update(shape_keys)
        if head_lean is not None:
            payload["expression"]["head_lean"] = round(head_lean, 4)
        payload["_ts"] = round(time.time(), 3)

        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, _STATE_PATH)

        write_active_flag(active, text)
        return True
    except Exception:
        return False


def write_shapes_only(shape_keys: dict[str, float],
                      head_lean: float | None = None) -> bool:
    """Patch blender_state.json shape_keys without touching lipsync_state.json.
    Use for micro-expression and ambient flicker pulses that aren't speech lipsync."""
    try:
        try:
            with open(_STATE_PATH, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            payload = {}

        if "expression" not in payload:
            payload["expression"] = {"shape_keys": {}, "head_lean": 0.0,
                                     "pacing": "steady", "intensity": 0.5}
        payload["expression"]["shape_keys"].update(shape_keys)
        if head_lean is not None:
            payload["expression"]["head_lean"] = round(head_lean, 4)
        payload["_ts"] = round(time.time(), 3)

        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, _STATE_PATH)
        return True
    except Exception:
        return False


def clear_lipsync() -> bool:
    """Set all mouth shapes to 0 and mark inactive — mouth returns to rest."""
    rest = {k: 0.0 for k in _ALL_MOUTH}
    return write_lipsync(rest, active=False)
