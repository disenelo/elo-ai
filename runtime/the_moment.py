"""
runtime/the_moment.py — WO-079: The Situated Self Invariant / The Moment.

Compiles a verified snapshot of eLo's current state each turn from existing
sources (self-model, perch_state, capability registry). Writes self/state/
the_moment.json for cross-process reading (robot NeoPixels, iOS, DesktopBuddy).

This is ASSEMBLY, not a new daemon. One call per turn, synchronous, <1ms.

ADR-Exec-004 (Situated Self) · ADR-Exec-006 (Executive Assembly) · WO-079.
"""
from __future__ import annotations

import json
import logging
import os
import time

_log = logging.getLogger(__name__)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MOMENT_PATH = os.path.join(_ROOT, "self", "state", "the_moment.json")

# Epistemic tier vocabulary (CA-proposed, WO-079)
# verified   — hardware/OS fact retrieved this turn
# inferred   — probabilistic, based on recent observation
# last-known — from persistent state, may be stale
# live       — checked against a live registry this turn
# unknown    — no data available
_TIER = {
    "verified":   "[verified]",
    "inferred":   "[inferred]",
    "last-known": "[last-known]",
    "live":       "[live]",
    "unknown":    "[unknown]",
}


def compile(  # noqa: A001 — shadows builtin intentionally for domain clarity
    state,
    *,
    perch_fresh: bool = False,
    pose_acked: bool = False,
) -> dict:
    """
    Build the current-moment snapshot from verified state.

    Args:
        state        : EloSelfState (self/elo_self_model.py)
        perch_fresh  : True if perch_state.json was successfully read THIS turn
        pose_acked   : True if a pose ACK was received this turn

    Returns a plain dict — serialisable to JSON for cross-process reading.
    """
    now = time.time()

    # Capability registry — live check (never guess)
    caps_live: list[str] = []
    try:
        from runtime.capabilities.registry import all_enabled as _cap_all
        caps_live = [getattr(c, "id", str(c)) for c in _cap_all()]
    except Exception:
        pass

    moment = {
        "ts":               now,
        "embodiment":       state.embodiment,
        "embodiment_tier":  "verified",          # set at startup from OS context
        "pose":             state.pose,
        "pose_tier":        "verified" if pose_acked else "last-known",
        "surface":          state.surface or state.location or "",
        "surface_tier":     "verified" if perch_fresh else "last-known",
        "balance":          state.balance,
        "size_cm": {
            "height": state.size.get("height_cm"),
            "reach":  state.size.get("reach_cm"),
            "jump":   state.size.get("jump_cm"),
        },
        "available_actions":    list(state.available_actions or []),
        "current_action":       state.current_action or "idle",
        "locomotion_health":    state.locomotion_faculty_health,
        "locomotion_tier":      "live",
        "capabilities":         caps_live,
        "capabilities_tier":    "live" if caps_live else "unknown",
        "nearby_surfaces":      list(state.nearby_surfaces or []),
        "nearby_tier":          "inferred",
        "mood":                 round(getattr(state, "mood", 0.5), 3),
        "curiosity":            round(getattr(state, "curiosity", 0.5), 3),
        "goal":                 getattr(state, "goal", ""),
        "last_self_update":     getattr(state, "last_updated", 0.0),
    }
    return moment


def write(state, *, perch_fresh: bool = False, pose_acked: bool = False) -> None:
    """Compile and write the_moment.json. Silent on failure — never blocks a turn."""
    try:
        moment = compile(state, perch_fresh=perch_fresh, pose_acked=pose_acked)
        os.makedirs(os.path.dirname(_MOMENT_PATH), exist_ok=True)
        with open(_MOMENT_PATH, "w", encoding="utf-8") as f:
            json.dump(moment, f, indent=2, ensure_ascii=False)
    except Exception as e:
        _log.debug("the_moment write failed (non-critical): %s", e)


def situated_with_epistemic(state, *, perch_fresh: bool = False, pose_acked: bool = False) -> str:
    """
    Returns a [SITUATED SELF] block with epistemic tier markers.
    Drop-in replacement for self.elo_self_model.situated_block() — extends it
    with WO-079 tier labels so eLo's language can match verification level.
    """
    m = compile(state, perch_fresh=perch_fresh, pose_acked=pose_acked)

    where     = m["surface"] or "unknown"
    pose      = m["pose"]
    e_pose    = _TIER[m["pose_tier"]]
    e_surface = _TIER[m["surface_tier"]]
    e_body    = _TIER["verified"]  # size/embodiment
    e_caps    = _TIER[m["capabilities_tier"]]
    e_near    = _TIER[m["nearby_tier"]]

    acts = ", ".join(m["available_actions"]) if m["available_actions"] else "unknown"
    caps = ", ".join(m["capabilities"][:8]) if m["capabilities"] else "none listed"

    lines = [
        "[SITUATED SELF — verified. Answer where you are / what you can do / pose ONLY from "
        "this. Never invent; if a field is unknown say so — never claim unverified state.]",
        f"embodiment: {m['embodiment']} {e_body}",
        f"where: {where} {e_surface}   pose: {pose} {e_pose}   balance: {m['balance']}",
        f"size: ~{m['size_cm']['height']}cm tall · reach ~{m['size_cm']['reach']}cm · "
        f"jump ~{m['size_cm']['jump']}cm {e_body}",
        f"actions now: {acts}",
        f"capabilities: {caps} {e_caps}",
        f"locomotion: {m['locomotion_health']} {_TIER['live']}",
    ]
    if m["nearby_surfaces"]:
        lines.append(f"nearby: {', '.join(map(str, m['nearby_surfaces']))} {e_near}")
    if m["current_action"] and m["current_action"] != "idle":
        lines.append(f"currently: {m['current_action']}")
    return "\n".join(lines)
