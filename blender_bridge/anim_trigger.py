"""
blender_bridge/anim_trigger.py — one-shot animation trigger writer.

Patches blender_state.json with a `trigger` block so Unity fires a specific
animation exactly once, edge-detected on _ts. Bypasses the locomoting /
meditation / gun gates that normal motion writes respect, so Python can
interrupt with any named clip immediately.

Head gestures (nod/shake/tilt/think/lookup) route through `head_motion`
— the existing mechanism — because they only move c_head.x and never stomp
the body clip.

Usage:
    from blender_bridge.anim_trigger import fire, wave, celebrate, gun_check
    fire("wave")
    fire("celebrate")
    fire("gun_check")
    fire("exit", direction="left")
    nod()
    think()
"""
from __future__ import annotations
import json
import os
import time

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")

# These are head gestures — route through head_motion, not the trigger block.
_HEAD_GESTURES: frozenset[str] = frozenset({"nod", "shake", "tilt", "think", "lookup"})


def fire(name: str, **extras) -> bool:
    """
    Write a one-shot animation trigger into blender_state.json.

    Unity's ApplyTrigger() edge-detects trigger._ts so each call fires exactly
    once regardless of how many times the receiver polls the file.

    Args:
        name    — trigger name (see Unity ApplyTrigger switch table)
        extras  — optional extra fields on the trigger object (e.g. direction="left")

    Returns True on success.
    """
    try:
        # Load current state so we don't wipe motion/expression/etc.
        try:
            with open(_STATE_PATH, encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

        ts = round(time.time(), 6)

        if name in _HEAD_GESTURES:
            # Head gesture — reuse existing head_motion block so existing GestureCo fires.
            state["head_motion"] = {"gesture": name, "ts": ts}
        else:
            state["trigger"] = {"name": name, "_ts": ts, **extras}

        state["_ts"] = ts  # bump top-level _ts so content-change detection sees a diff

        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
        return True

    except Exception:
        return False


# ── Named helpers ─────────────────────────────────────────────────────────────

def wave()       -> bool: return fire("wave")
def jump()       -> bool: return fire("jump")
def celebrate()  -> bool: return fire("celebrate")
def gun_check()  -> bool: return fire("gun_check")
def gun_run()    -> bool: return fire("gun_run")
def gun_fire()   -> bool: return fire("gun_fire")
def calm_enter() -> bool: return fire("calm_enter")
def calm_exit()  -> bool: return fire("calm_exit")

# Return to clean idle — clears locomoting + meditating gates.
def idle()       -> bool: return fire("idle")

# Head gestures (route through head_motion)
def nod()        -> bool: return fire("nod")
def shake()      -> bool: return fire("shake")
def tilt()       -> bool: return fire("tilt")
def think()      -> bool: return fire("think")
def lookup()     -> bool: return fire("lookup")

# Exit sequence — walk off screen left or right
def exit_left()  -> bool: return fire("exit", direction="left")
def exit_right() -> bool: return fire("exit", direction="right")


# ── Scale commands ────────────────────────────────────────────────────────────
# Unity reads scale_cmd._ts (edge-detect) and applies delta to the same step
# the +/- UI buttons use. +1 = one step bigger, -1 = one step smaller.

def _scale(delta: int) -> bool:
    try:
        try:
            with open(_STATE_PATH, encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
        state["scale_cmd"] = {"delta": delta, "_ts": round(time.time(), 6)}
        state["_ts"] = state["scale_cmd"]["_ts"]
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
        return True
    except Exception:
        return False

def scale_up()   -> bool: return _scale(1)
def scale_down() -> bool: return _scale(-1)
