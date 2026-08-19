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

_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH  = os.path.join(_ROOT, "blender", "blender_state.json")
_EVENTS_PATH = os.path.join(_ROOT, "blender", "unity_events.json")

# These are head gestures — route through head_motion, not the trigger block.
_HEAD_GESTURES: frozenset[str] = frozenset({"nod", "shake", "tilt", "think", "lookup"})

# Names Designer wired to emit anim_complete/anim_failed via unity_events.json
# (per FROM_DESIGN_2026-08-13_capability_field_names.md, "What Designer shipped" in card 0011):
# wave + head gestures on real completion. Clip triggers (jump/gun/calm) deferred honestly —
# they must report `unconfirmed`, not success (card 0011 §Your half point 5).
_ANIM_ACK_COVERED: frozenset[str] = frozenset({
    "wave", "nod", "shake", "tilt", "think", "lookup",
})

# WO-111 (0011): default ACK wait bound. Timeout = reported failure, never silence.
ACK_TIMEOUT_S = 15.0

# WO-111: ACK status sentinel — anim triggers are one-shot file writes.
# Unity polls the file and plays the clip; Python has no socket to know it happened.
# Returning True claimed success with no evidence — replaced with this sentinel.
ANIM_UNCONFIRMED = "unconfirmed"


def fire(name: str, action_id: str | None = None, **extras) -> bool:
    """
    Write a one-shot animation trigger into blender_state.json.

    Unity's ApplyTrigger() edge-detects trigger._ts so each call fires exactly
    once regardless of how many times the receiver polls the file.

    Args:
        name       — trigger name (see Unity ApplyTrigger switch table)
        action_id  — optional pairing id; echoed back on the ACK row so the brain
                     can resolve which invocation completed. Include it when you
                     intend to wait on an ACK.
        extras     — optional extra fields on the trigger object (e.g. direction="left")

    Returns ANIM_UNCONFIRMED sentinel on write. **A write is not a completion.**
    Call fire_ack() to wait for a real ACK from unity_events.json.
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
            block = {"gesture": name, "ts": ts}
            if action_id:
                block["action_id"] = action_id
            state["head_motion"] = block
        else:
            block = {"name": name, "_ts": ts, **extras}
            if action_id:
                block["action_id"] = action_id
            state["trigger"] = block

        state["_ts"] = ts  # bump top-level _ts so content-change detection sees a diff

        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
        # WO-111: file written ≠ animation played. Unity polls independently.
        return ANIM_UNCONFIRMED  # type: ignore[return-value]

    except Exception:
        return False


# ── WO-111 (0011): consume anim_complete / anim_failed from unity_events.json ─
# The append-log schema is ratified in
# blender/agent_bus/builder/FROM_DESIGN_2026-08-15_unity_events_append_log_schema.md
# — newline-delimited JSON rows carrying {seq, type, subject, action_id, payload, _ts}.

def _iter_events_from(seq_after: int):
    """Yield rows in unity_events.json whose seq > seq_after."""
    try:
        with open(_EVENTS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if not isinstance(row, dict):
                    continue
                seq = row.get("seq")
                if not isinstance(seq, int):
                    continue
                if seq <= seq_after:
                    continue
                yield row
    except FileNotFoundError:
        return


def _max_seq() -> int:
    """Return the highest seq currently in unity_events.json, or -1 if empty."""
    max_seq = -1
    try:
        with open(_EVENTS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if isinstance(row, dict) and isinstance(row.get("seq"), int):
                    if row["seq"] > max_seq:
                        max_seq = row["seq"]
    except FileNotFoundError:
        pass
    return max_seq


def wait_for_ack(action_id: str, timeout_s: float = ACK_TIMEOUT_S,
                 poll_interval: float = 0.1, since_seq: int | None = None):
    """
    Poll unity_events.json for anim_complete / anim_failed matching action_id.

    Returns an ActionResult:
      - confirmed  on anim_complete
      - failed     on anim_failed (routes through honest_outcome → "didn't work")
      - failed(source="timeout")  when no matching ACK arrives before timeout_s
        — Rule: timeout ⇒ reported failure, never silence.
    """
    from runtime.ack_contract import ActionResult
    baseline = since_seq if since_seq is not None else _max_seq()
    deadline = time.time() + timeout_s
    while True:
        for row in _iter_events_from(baseline):
            if row.get("action_id") != action_id:
                continue
            rtype = row.get("type")
            if rtype == "anim_complete":
                return ActionResult(action_id=action_id, ok=True,
                                    detail=f"anim {row.get('subject','')} complete",
                                    source="unity_ack")
            if rtype == "anim_failed":
                reason = ""
                p = row.get("payload")
                if isinstance(p, dict):
                    reason = str(p.get("reason", ""))
                return ActionResult(action_id=action_id, ok=False,
                                    detail=(f"anim failed: {reason}"
                                            if reason else "anim failed"),
                                    source="unity_ack")
        if time.time() >= deadline:
            return ActionResult(action_id=action_id, ok=False,
                                detail=f"no ACK within {timeout_s:.1f}s",
                                source="timeout")
        time.sleep(poll_interval)


def fire_ack(name: str, action_id: str, timeout_s: float = ACK_TIMEOUT_S, **extras):
    """
    Fire a trigger and resolve it against a real ACK from unity_events.json.

    - Names Designer wired for anim_complete/anim_failed (wave + head gestures):
      write the trigger with action_id, wait for the matching ACK.
    - Clip triggers with no ACK path (jump/gun/calm/scale/idle/exit/spawn_wave):
      report `unconfirmed` synchronously — do NOT return True.
      (Card 0011: "Do not let them inherit the old True.")
    - Timeout on a covered name: reported failure.
    """
    from runtime.ack_contract import ActionResult
    # Snapshot baseline BEFORE writing so we only match ACKs for THIS invocation.
    baseline_seq = _max_seq()
    write_result = fire(name, action_id=action_id, **extras)
    if write_result is False:
        return ActionResult(action_id=action_id, ok=False,
                            detail="state write failed", source="internal")
    if name in _ANIM_ACK_COVERED:
        return wait_for_ack(action_id, timeout_s=timeout_s, since_seq=baseline_seq)
    return ActionResult(action_id=action_id, ok=None,
                        detail=f"'{name}' has no anim_complete ACK path yet",
                        source="internal")


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
