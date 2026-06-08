"""
avatar/unity_bridge.py — eLo Core → Unity signal bridge.

Communication method: local JSON file.
Python writes. Unity reads. No networking required.
Easy to debug. File can be inspected at any time.

Python side:
    export_signal(signal_dict)         → writes avatar_signal.json
    export_from_core(state, emotion, intent, energy, identity, mode, memory)  → builds + writes

Unity side:
    EloSignalReceiver.cs reads the file on a configurable interval.
    Maps signal fields to Animator parameters.

JSON file location:
    Default: ELO_SIGNAL_PATH env var, or avatar/avatar_signal.json relative to project root.
    Unity should point to the same path.

Signal schema:
    See avatar/signal_schema.json for the full documented schema.
"""

import json
import os

_DIR         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_OUT = os.environ.get(
    "ELO_SIGNAL_PATH",
    os.path.join(_DIR, "avatar", "avatar_signal.json"),
)


def export_signal(signal: dict, path: str = None) -> str:
    """
    Write an avatar signal dict to the JSON bridge file.

    Args:
        signal: Full avatar signal from avatar_bridge.get_avatar_signal()
                plus identity fields.
        path:   Override output path. Default: ELO_SIGNAL_PATH or avatar/avatar_signal.json.

    Returns:
        Path written to.
    """
    out = path or _DEFAULT_OUT
    os.makedirs(os.path.dirname(out), exist_ok=True)

    payload = _build_payload(signal)

    with open(out, "w") as f:
        json.dump(payload, f, indent=2)

    return out


def export_from_core(
    state:    str,
    emotion:  str,
    intent:   str,
    energy:   float,
    identity: dict = None,
    mode:     str  = "companion",
    memory:   dict = None,
    path:     str  = None,
) -> str:
    """
    Build a complete signal from core engine outputs and write to the bridge file.

    This is the convenience entry point called from core_engine.turn().
    """
    from core.avatar_bridge import get_avatar_signal, signal_to_animation_hints

    signal = get_avatar_signal(state, emotion, mode, memory)

    # enrich with identity signals
    if identity:
        signal["identity"] = {
            "perspective": identity.get("perspective", ""),
            "intent":      identity.get("intent",      ""),
            "values":      identity.get("values",      []),
            "bias":        identity.get("response_bias", ""),
        }

    # add animation hints
    hints = signal_to_animation_hints(signal)
    signal["animation_hints"] = hints

    return export_signal(signal, path)


def _build_payload(signal: dict) -> dict:
    """
    Normalise a signal dict into the canonical bridge format.
    Ensures Unity always receives a consistent schema.
    """
    return {
        "version":   "1.0",
        "source":    "eLo Core",

        # core identity signals
        "state":     signal.get("state",   "exploring"),
        "emotion":   signal.get("emotion", "calm"),
        "intent":    signal.get("intent",  "hold_space"),
        "energy":    signal.get("energy",  0.5),
        "mode":      signal.get("mode",    "companion"),

        # identity layer
        "identity":  signal.get("identity", {
            "perspective": "",
            "intent":      "",
            "values":      [],
            "bias":        "",
        }),

        # expression hints for animation
        "animation_hints": signal.get("animation_hints", {
            "head_tilt_deg":    0.0,
            "lean_amount":      0.0,
            "bounce_intensity": 0.0,
            "rotation_speed":   0.0,
            "scale_pulse":      0.0,
            "movement_speed":   signal.get("energy", 0.5),
        }),

        # orb glow
        "orb": {
            "intensity": signal.get("orb", 0.5),
            "mode":      _orb_mode(signal.get("state", "exploring")),
        },

        # context
        "project":   signal.get("project", "elo_core"),
        "posture":   signal.get("posture", "settle"),
        "pace":      signal.get("pace",    "measured"),
    }


def _orb_mode(state: str) -> str:
    """Map state to an orb animation mode string for Unity."""
    return {
        "exploring":  "slow_pulse",
        "building":   "steady",
        "focused":    "bright_point",
        "reflecting": "dim_breathe",
        "playful":    "colour_shift",
        "resting":    "minimal",
    }.get(state, "slow_pulse")


def read_signal(path: str = None) -> dict:
    """
    Read the current signal from the bridge file.
    Useful for debugging and for Unity editor tools that verify the Python side.
    """
    p = path or _DEFAULT_OUT
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return json.load(f)
