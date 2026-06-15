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
    4. Run Script — you should see "[eLo Bridge] watching..." in the console
    5. Start eLo OS: python main.py
    6. Talk to eLo — rig should respond each turn

TROUBLESHOOTING:
    - Nothing moving: open Blender's System Console (Window > Toggle System Console)
      and look for [eLo Bridge] lines. If the timer stopped, re-run the script.
    - "Object not found": check RIG_NAME and MESH_NAME match your scene exactly.
    - Shape keys not moving: confirm the mesh is NOT in Edit mode.
    - Blender sluggish: lower POLL_INTERVAL to 0.5 or higher.
"""

import bpy
import json
import os

# ── CONFIGURE ─────────────────────────────────────────────────────────────────
STATE_PATH    = os.path.expanduser("~/elo-ai/blender/blender_state.json")
RIG_NAME      = "rig"
MESH_NAME     = "eLo-BodyxHead w/Mouth"
HEAD_BONE     = "c_head.x"
POLL_INTERVAL = 0.25   # seconds — raise to 0.5 if Blender feels sluggish

# ── internal state ─────────────────────────────────────────────────────────────
_last_ts        = 0.0
_last_animation = ""
_warn_once      = set()   # keys already warned about — suppress repeat noise


# ── helpers ───────────────────────────────────────────────────────────────────

def _warn(key: str, msg: str) -> None:
    if key not in _warn_once:
        _warn_once.add(key)
        print(f"[eLo Bridge] WARNING: {msg}")


def _read_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        _warn("no_state", f"state file not found: {STATE_PATH} — is eLo OS running?")
        return {}
    except json.JSONDecodeError:
        return {}   # mid-write race — skip this tick
    except Exception as e:
        _warn("read_err", f"read error: {e}")
        return {}


# ── NLA clip driver ───────────────────────────────────────────────────────────

def _play_clip(clip_name: str, speed: float) -> None:
    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None:
        _warn("no_rig", f"armature '{RIG_NAME}' not found in scene")
        return
    if rig.animation_data is None:
        _warn("no_anim", f"'{RIG_NAME}' has no animation data")
        return
    if not rig.animation_data.nla_tracks:
        _warn("no_nla", f"'{RIG_NAME}' has no NLA tracks — add clips to the NLA editor")
        return

    found = False
    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            is_match = strip.action and strip.action.name.lower() == clip_name.lower()
            strip.mute = not is_match
            if is_match:
                strip.scale = max(0.1, 1.0 / speed) if speed > 0 else 1.0
                found = True

    if not found:
        _warn(f"clip_{clip_name}", f"NLA clip '{clip_name}' not found — available: " +
              ", ".join(s.action.name for t in rig.animation_data.nla_tracks
                        for s in t.strips if s.action))


def _update_clip_speed(clip_name: str, speed: float) -> None:
    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None or rig.animation_data is None:
        return
    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            if not strip.mute and strip.action and strip.action.name.lower() == clip_name.lower():
                strip.scale = max(0.1, 1.0 / speed) if speed > 0 else 1.0
                return


# ── shape key driver ──────────────────────────────────────────────────────────

def _apply_shape_keys(shape_keys: dict) -> None:
    mesh_obj = bpy.data.objects.get(MESH_NAME)
    if mesh_obj is None:
        _warn("no_mesh", f"mesh '{MESH_NAME}' not found in scene")
        return

    # shape keys can't be set while the mesh itself is in Edit mode
    # (being in Object mode is fine even if armature is in Edit mode)
    if mesh_obj.mode == "EDIT":
        return   # only skip when THIS mesh is in edit, not the rig

    if mesh_obj.data.shape_keys is None:
        _warn("no_keys", f"'{MESH_NAME}' has no shape keys")
        return

    key_blocks = mesh_obj.data.shape_keys.key_blocks
    incoming   = set(shape_keys.keys())

    for key_name, target_value in shape_keys.items():
        kb = key_blocks.get(key_name)
        if kb is None:
            _warn(f"key_{key_name}", f"shape key '{key_name}' not found on '{MESH_NAME}'")
            continue
        clamped  = max(kb.slider_min, min(kb.slider_max, float(target_value)))
        kb.value = clamped

    # ease unused keys back toward 0 — not hard reset
    for kb in key_blocks:
        if kb.name == "Basis" or kb.name in incoming:
            continue
        if abs(kb.value) > 0.001:
            kb.value = round(kb.value * 0.55, 4)

    mesh_obj.update_tag()   # tell Blender the mesh needs redraw


# ── head lean driver ──────────────────────────────────────────────────────────

def _apply_head_lean(lean: float) -> None:
    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None or rig.type != "ARMATURE":
        return

    # pose bone access only works when NOT in Edit mode
    if rig.mode == "EDIT":
        return

    bone = rig.pose.bones.get(HEAD_BONE)
    if bone is None:
        _warn("no_head_bone", f"pose bone '{HEAD_BONE}' not found on '{RIG_NAME}'")
        return

    bone.rotation_mode = "XYZ"
    rot = list(bone.rotation_euler)
    rot[2] = float(lean)
    bone.rotation_euler = rot

    rig.update_tag()   # flag for redraw — no full depsgraph eval needed


# ── main apply ────────────────────────────────────────────────────────────────

def _apply_state(data: dict) -> None:
    global _last_animation

    motion     = data.get("motion",     {})
    expression = data.get("expression", {})

    animation = motion.get("animation", "idle")
    speed     = float(motion.get("speed", 0.6))

    if animation != _last_animation:
        _last_animation = animation
        _play_clip(animation, speed)
    else:
        _update_clip_speed(animation, speed)

    shape_keys = expression.get("shape_keys", {})
    if shape_keys:
        _apply_shape_keys(shape_keys)

    head_lean = float(expression.get("head_lean", 0.0))
    _apply_head_lean(head_lean)


# ── poll timer ────────────────────────────────────────────────────────────────

def _poll() -> float:
    global _last_ts

    # always return the interval — never raise, never return None
    try:
        data = _read_state()
        if not data:
            return POLL_INTERVAL

        ts = data.get("_ts", 0.0)
        if ts != _last_ts:
            _last_ts = ts
            _apply_state(data)

    except Exception as e:
        # catch everything so the timer never silently stops
        print(f"[eLo Bridge] ERROR in poll: {e}")

    return POLL_INTERVAL


# ── register ──────────────────────────────────────────────────────────────────

if bpy.app.timers.is_registered(_poll):
    bpy.app.timers.unregister(_poll)

bpy.app.timers.register(_poll, persistent=True)
print(f"[eLo Bridge] watching  {STATE_PATH}")
print(f"[eLo Bridge] rig={RIG_NAME}  mesh={MESH_NAME}  head={HEAD_BONE}")
print(f"[eLo Bridge] poll every {POLL_INTERVAL}s  |  check Window > Toggle System Console for errors")
