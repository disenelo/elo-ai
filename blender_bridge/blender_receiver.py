"""
blender_bridge/blender_receiver.py — Blender-side script. Polls state.json, drives rig.

DROP INTO BLENDER'S TEXT EDITOR and click Run Script.

What it drives:
    - NLA strips on the 'rig' armature  (body animation clips)
    - Shape keys on 'eLo-BodyxHead w/Mouth'  (expression blends)
    - c_head.x bone rotation  (head lean)

Polls blender/blender_state.json every 250ms.
Only acts when _ts changes — no wasted updates.

SETUP:
    1. Open Blender with the eLo scene
    2. Scripting workspace → open this file
    3. Edit STATE_PATH below to match your machine
    4. Run Script
    5. Start eLo OS in a terminal: python main.py
"""

import bpy
import json
import math
import os

# ── CONFIGURE ─────────────────────────────────────────────────────────────────
STATE_PATH   = os.path.expanduser("~/elo-ai/blender/blender_state.json")
RIG_NAME     = "rig"                        # armature object name
MESH_NAME    = "eLo-BodyxHead w/Mouth"      # mesh with shape keys
HEAD_BONE    = "c_head.x"                   # head lean bone
POLL_INTERVAL = 0.25                        # seconds

# ── state ─────────────────────────────────────────────────────────────────────
_last_ts        = 0.0
_last_animation = ""


# ── read ──────────────────────────────────────────────────────────────────────

def _read_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── NLA clip driver ───────────────────────────────────────────────────────────

def _play_clip(clip_name: str, speed: float) -> None:
    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None or rig.animation_data is None:
        return

    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            strip.mute = True

    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            if strip.action and strip.action.name.lower() == clip_name.lower():
                strip.mute  = False
                strip.scale = max(0.1, 1.0 / speed) if speed > 0 else 1.0
                return


# ── shape key driver ──────────────────────────────────────────────────────────

def _apply_shape_keys(shape_keys: dict) -> None:
    """
    Set shape key values on eLo-BodyxHead w/Mouth.
    shape_keys: dict of {key_name: value}
    Values are clamped to each key's slider range.
    """
    mesh_obj = bpy.data.objects.get(MESH_NAME)
    if mesh_obj is None or mesh_obj.data.shape_keys is None:
        return

    key_blocks = mesh_obj.data.shape_keys.key_blocks

    for key_name, target_value in shape_keys.items():
        kb = key_blocks.get(key_name)
        if kb is None:
            continue
        # clamp to the key's actual slider range
        clamped = max(kb.slider_min, min(kb.slider_max, float(target_value)))
        kb.value = clamped

    # reset any keys NOT in the incoming dict back toward 0
    incoming = set(shape_keys.keys())
    for kb in key_blocks:
        if kb.name == "Basis":
            continue
        if kb.name not in incoming and abs(kb.value) > 0.001:
            kb.value = kb.value * 0.6   # ease back, not hard reset


# ── head lean driver ──────────────────────────────────────────────────────────

def _apply_head_lean(lean: float) -> None:
    """
    Apply head lean by rotating c_head.x bone on Y axis.
    lean: radians (small values — ±0.1 is a noticeable tilt)
    """
    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None or rig.type != "ARMATURE":
        return

    # pose mode required to set pose bone rotation
    bone = rig.pose.bones.get(HEAD_BONE)
    if bone is None:
        return

    bone.rotation_mode = "XYZ"
    current = list(bone.rotation_euler)
    current[2] = lean   # Z axis = left/right lean on this rig
    bone.rotation_euler = current


# ── main apply ────────────────────────────────────────────────────────────────

def _apply_state(data: dict) -> None:
    global _last_animation

    motion     = data.get("motion",     {})
    expression = data.get("expression", {})

    animation = motion.get("animation", "idle")
    speed     = float(motion.get("speed", 0.6))

    # NLA clip
    if animation != _last_animation:
        _last_animation = animation
        _play_clip(animation, speed)
    else:
        # same clip — just nudge speed
        rig = bpy.data.objects.get(RIG_NAME)
        if rig and rig.animation_data:
            for track in rig.animation_data.nla_tracks:
                for strip in track.strips:
                    if not strip.mute and strip.action:
                        strip.scale = max(0.1, 1.0 / speed) if speed > 0 else 1.0

    # shape keys
    shape_keys = expression.get("shape_keys", {})
    if shape_keys:
        _apply_shape_keys(shape_keys)

    # head lean
    head_lean = expression.get("head_lean", 0.0)
    _apply_head_lean(head_lean)


# ── poll timer ────────────────────────────────────────────────────────────────

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


# Register
if not bpy.app.timers.is_registered(_poll):
    bpy.app.timers.register(_poll, persistent=True)
    print(f"[eLo Bridge] watching {STATE_PATH} every {POLL_INTERVAL}s")
    print(f"[eLo Bridge] rig={RIG_NAME}  mesh={MESH_NAME}  head={HEAD_BONE}")
