"""
blender_bridge/blender_receiver.py — Blender-side script that polls state.json.

DROP THIS FILE INTO BLENDER'S TEXT EDITOR and run it.
(Or register it as a modal timer via bpy.app.timers.register)

Polls blender/blender_state.json every 250ms.
When state changes, drives the eLo rig via animation_driver.

USAGE IN BLENDER:
    1. Open Blender, load the eLo rig scene
    2. Open Scripting workspace
    3. Open this file in the text editor
    4. Click Run Script
    5. eLo starts responding to eLo OS output

REQUIREMENTS:
    - eLo rig must be in the active scene (object named "eLo_Rig" or similar)
    - NLA clips must be named: idle, walk, jump, sit, float
    - state.json path may need adjustment for your machine

Polling continues until Blender is closed or the script is stopped.
"""

import bpy
import json
import os
import time

# ── CONFIGURE THIS PATH ───────────────────────────────────────────────────────
# Absolute path to blender_state.json on your machine
STATE_PATH = os.path.expanduser("~/eLo-Planet-AI/blender/blender_state.json")

# Name of the eLo armature object in your scene
RIG_NAME = "eLo_Rig"

# NLA track name that contains the animation clips
NLA_TRACK_NAME = "eLo_Animations"

# ── POLL INTERVAL ─────────────────────────────────────────────────────────────
POLL_INTERVAL = 0.25   # seconds

# ── state ─────────────────────────────────────────────────────────────────────
_last_ts        = 0.0
_last_animation = ""


def _read_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _apply_state(data: dict) -> None:
    global _last_animation

    motion    = data.get("motion", {})
    animation = motion.get("animation", "idle")
    speed     = float(motion.get("speed", 0.6))
    intensity = float(motion.get("intensity", 0.5))

    if animation == _last_animation:
        # same clip — just update speed/intensity if rig is accessible
        _set_speed(animation, speed)
        return

    _last_animation = animation
    _play_clip(animation, speed)


def _play_clip(clip_name: str, speed: float) -> None:
    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None:
        return

    # find clip in NLA tracks
    if rig.animation_data is None:
        return

    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            strip.mute = True  # mute all

    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            if strip.action and strip.action.name.lower() == clip_name.lower():
                strip.mute   = False
                strip.scale  = max(0.1, 1.0 / speed) if speed > 0 else 1.0
                strip.use_sync_length = False
                return  # only unmute first match


def _set_speed(clip_name: str, speed: float) -> None:
    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None or rig.animation_data is None:
        return
    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            if (strip.action and
                    strip.action.name.lower() == clip_name.lower() and
                    not strip.mute):
                strip.scale = max(0.1, 1.0 / speed) if speed > 0 else 1.0
                return


def _poll() -> float:
    global _last_ts

    data = _read_state()
    if not data:
        return POLL_INTERVAL

    ts = data.get("_ts", 0.0)
    if ts != _last_ts:
        _last_ts = ts
        _apply_state(data)

    return POLL_INTERVAL


# Register as a Blender timer — runs every POLL_INTERVAL seconds
if not bpy.app.timers.is_registered(_poll):
    bpy.app.timers.register(_poll, persistent=True)
    print(f"[eLo Bridge] polling {STATE_PATH} every {POLL_INTERVAL}s")
