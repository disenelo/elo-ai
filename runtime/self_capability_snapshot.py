"""
runtime/self_capability_snapshot.py — WO-PRES-006

SelfCapabilitySnapshot: single assembled snapshot of what eLo's body can physically do.
Assembled once per turn (after capability_set is read) and passed to the planner.
Replaces scattered capability_set dict reads with one typed object.

Depends on: WO-NAV-004 (jump_px), WO-PRES-001 (run_capability), WO-PRES-003 (wrap_available).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SelfCapabilitySnapshot:
    jump_px:            float  # max horizontal jump reach in pixels (from capability_set)
    embodiment_scope:   list   # ["desktop", "mobile", ...] (from capability_set)
    run_capability:     bool   # True if eLo can run on current surface (WO-PRES-001)
    run_up_distance_px: float  # min pixel run distance before long jump (WO-PRES-001)
    size_px:            float  # eLo body footprint in pixels (from elo_spatial body bounds)
    movement_speed_px_s: float # approximate movement speed in px/s
    wrap_available:     bool   # True if desktop boundaries allow toroidal wrap (WO-PRES-003)
    body_win_id:        Optional[str] = None  # current surface win_id (from elo_spatial.json)


def build_snapshot(capability_set: dict, spatial: dict) -> SelfCapabilitySnapshot:
    """
    Assemble per-turn SelfCapabilitySnapshot from capability_set and elo_spatial data.

    capability_set: dict from elo_spatial.json["surface_graph"]["capability_set"]
    spatial: full elo_spatial.json dict (for body bounds and body_win_id)
    """
    jump_px = float(capability_set.get("jump_px", 0))
    embodiment_scope = list(capability_set.get("embodiment_scope", ["desktop"]))
    run_capability = bool(capability_set.get("run_capability", True))
    run_up_distance_px = float(capability_set.get("run_up_distance_px", 120.0))
    movement_speed_px_s = float(capability_set.get("movement_speed_px_s", 200.0))
    wrap_available = bool(capability_set.get("wrap_available", False))

    # body size_px from body bounds rect if available
    body_rect = spatial.get("body_rect_px", [])
    size_px = float(body_rect[2]) if len(body_rect) >= 3 else float(capability_set.get("size_px", 80.0))

    # body_win_id from elo_spatial
    body_win_id = spatial.get("body_win_id", None)
    if body_win_id is not None:
        body_win_id = str(body_win_id)

    return SelfCapabilitySnapshot(
        jump_px=jump_px,
        embodiment_scope=embodiment_scope,
        run_capability=run_capability,
        run_up_distance_px=run_up_distance_px,
        size_px=size_px,
        movement_speed_px_s=movement_speed_px_s,
        wrap_available=wrap_available,
        body_win_id=body_win_id,
    )
