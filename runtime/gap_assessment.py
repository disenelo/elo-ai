"""
runtime/gap_assessment.py — WO-113: 7-state gap vocabulary.

Affordance = world geometry ∩ body capability ∩ confidence.
Not a surface lookup — a real assessment with numbers behind it.

The seven gap states (Row 17 GAP):
  CAN                  — within reliable_range, clear path
  CANNOT               — gap exceeds max possible, action blocked
  CAN-BUT-DEGRADED     — action available but locomotion health degraded
  CAN-BUT-LOW-CONFIDENCE — within max range but outside reliable_range
  CAN-IF-CONDITION     — possible with prerequisite (e.g. run-up needed)
  UNKNOWN              — insufficient spatial data
  BLOCKED              — action not in surface affordances at all

Declared constants (source: declared, not learned):
  maxJumpEloHeights = 1.5   — from DesktopBuddy.cs:EloDesktopNav
  comfortable_margin = 0.85  — gap must be ≤ 85% of reliable_range to be CAN
  run_up_threshold = 1.0     — gap > reliable_range but ≤ max → CAN-IF-CONDITION
  max_range_factor = 1.2     — beyond 1.2× reliable_range → CANNOT
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

# ── Declared constants ─────────────────────────────────────────────────────────
_MAX_JUMP_ELO_HEIGHTS = 1.5          # DesktopBuddy.cs:EloDesktopNav maxJumpEloHeights
_COMFORTABLE_MARGIN = 0.85           # gap ≤ 85% reliable_range → CAN
_RUNUP_FACTOR = 1.0                  # gap > reliable_range but ≤ 1.0× max → CAN-IF-CONDITION
_CANNOT_FACTOR = 1.2                 # gap > 1.2× reliable_range → CANNOT
_RANGE_SOURCE_DECLARED = "declared"
_RANGE_SOURCE_LEARNED  = "learned"

# The seven canonical gap states
GAP_STATES = frozenset({
    "CAN",
    "CANNOT",
    "CAN-BUT-DEGRADED",
    "CAN-BUT-LOW-CONFIDENCE",
    "CAN-IF-CONDITION",
    "UNKNOWN",
    "BLOCKED",
})

# Actions that involve crossing a spatial gap
_GAP_ACTIONS = frozenset({"jump", "wall-run", "wall_jump"})


@dataclass
class GapResult:
    """Gap assessment for a single action from the current position."""
    action:              str
    status:              str            # one of GAP_STATES
    confidence:          float          # 0.0–1.0
    gap_distance_px:     Optional[float]  # None if unknown
    reliable_range_px:   float          # 1.5 × elo_height_px (declared)
    max_range_px:        float          # reliable_range_px / comfortable_margin
    range_source:        str            # "declared" | "learned"
    reason:              str

    def to_dict(self) -> dict:
        return asdict(self)


def _elo_height_px(spatial: dict) -> float:
    """
    Derive eLo's on-screen height in pixels from spatial state.
    spatial["height"] is a fraction of screen_h (from elo_spatial.json).
    Falls back to 94.0px (≈ 0.065 × 1440) when data is absent.
    """
    h_frac = spatial.get("height", 0.0)
    screen_h = spatial.get("screen_h", 1440)
    if h_frac and h_frac > 0:
        return float(h_frac) * float(screen_h)
    return 94.0  # declared fallback: ~6.5% of 1440p


def _reliable_range(elo_height_px: float) -> float:
    """1.5 × eLo height (declared from DesktopBuddy.cs maxJumpEloHeights)."""
    return _MAX_JUMP_ELO_HEIGHTS * elo_height_px


def _assess_one(
    action: str,
    gap_distance_px: Optional[float],
    reliable_range_px: float,
    locomotion_health: str,
    in_affordances: bool,
) -> GapResult:
    """Compute the gap state for one action."""
    max_range = reliable_range_px / _COMFORTABLE_MARGIN

    if not in_affordances:
        return GapResult(
            action=action,
            status="BLOCKED",
            confidence=1.0,
            gap_distance_px=gap_distance_px,
            reliable_range_px=reliable_range_px,
            max_range_px=max_range,
            range_source=_RANGE_SOURCE_DECLARED,
            reason=f"{action} is not available from the current surface",
        )

    if gap_distance_px is None:
        return GapResult(
            action=action,
            status="UNKNOWN",
            confidence=0.0,
            gap_distance_px=None,
            reliable_range_px=reliable_range_px,
            max_range_px=max_range,
            range_source=_RANGE_SOURCE_DECLARED,
            reason="gap distance not available — no spatial target data",
        )

    if locomotion_health in ("DEGRADED", "OFFLINE"):
        return GapResult(
            action=action,
            status="CAN-BUT-DEGRADED",
            confidence=0.3,
            gap_distance_px=gap_distance_px,
            reliable_range_px=reliable_range_px,
            max_range_px=max_range,
            range_source=_RANGE_SOURCE_DECLARED,
            reason=f"locomotion is {locomotion_health} — reduced reliability",
        )

    if gap_distance_px > max_range * _CANNOT_FACTOR:
        return GapResult(
            action=action,
            status="CANNOT",
            confidence=0.95,
            gap_distance_px=gap_distance_px,
            reliable_range_px=reliable_range_px,
            max_range_px=max_range,
            range_source=_RANGE_SOURCE_DECLARED,
            reason=f"gap ({gap_distance_px:.0f}px) exceeds max range ({max_range * _CANNOT_FACTOR:.0f}px)",
        )

    if gap_distance_px <= reliable_range_px * _COMFORTABLE_MARGIN:
        confidence = round(1.0 - (gap_distance_px / reliable_range_px) * 0.3, 2)
        return GapResult(
            action=action,
            status="CAN",
            confidence=confidence,
            gap_distance_px=gap_distance_px,
            reliable_range_px=reliable_range_px,
            max_range_px=max_range,
            range_source=_RANGE_SOURCE_DECLARED,
            reason=f"gap ({gap_distance_px:.0f}px) within reliable range ({reliable_range_px:.0f}px)",
        )

    if gap_distance_px <= reliable_range_px:
        confidence = round(0.55 - (gap_distance_px - reliable_range_px * _COMFORTABLE_MARGIN) / reliable_range_px * 0.4, 2)
        return GapResult(
            action=action,
            status="CAN-BUT-LOW-CONFIDENCE",
            confidence=max(0.1, confidence),
            gap_distance_px=gap_distance_px,
            reliable_range_px=reliable_range_px,
            max_range_px=max_range,
            range_source=_RANGE_SOURCE_DECLARED,
            reason=(
                f"gap ({gap_distance_px:.0f}px) within max range but outside reliable range "
                f"({reliable_range_px:.0f}px) — might not clear it"
            ),
        )

    # gap > reliable_range, ≤ max_range × CANNOT_FACTOR → CAN-IF-CONDITION (needs run-up)
    return GapResult(
        action=action,
        status="CAN-IF-CONDITION",
        confidence=0.35,
        gap_distance_px=gap_distance_px,
        reliable_range_px=reliable_range_px,
        max_range_px=max_range,
        range_source=_RANGE_SOURCE_DECLARED,
        reason=(
            f"gap ({gap_distance_px:.0f}px) exceeds reliable range ({reliable_range_px:.0f}px) "
            f"— run-up required"
        ),
    )


def assess(
    surface_affordances: tuple | list,
    *,
    spatial: dict | None = None,
    locomotion_health: str = "OK",
    gap_distance_px: Optional[float] = None,
) -> list[GapResult]:
    """
    Assess gap states for all jump-class actions in surface_affordances.

    Args:
        surface_affordances: tuple/list of action verbs from affordances_for()
        spatial:             elo_spatial.json dict (for eLo height + screen dims)
        locomotion_health:   from EloSelfState ("OK" | "DEGRADED" | "OFFLINE")
        gap_distance_px:     known gap distance in pixels; None = UNKNOWN

    Returns list of GapResult, one per _GAP_ACTIONS entry assessed.
    Only _GAP_ACTIONS members are assessed; other affordances are ignored.
    """
    sp = spatial or {}
    elo_h = _elo_height_px(sp)
    rrange = _reliable_range(elo_h)
    affordance_set = frozenset(surface_affordances or [])

    # Always assess the canonical gap-crossing actions
    results = []
    for action in sorted(_GAP_ACTIONS):
        results.append(_assess_one(
            action=action,
            gap_distance_px=gap_distance_px,
            reliable_range_px=rrange,
            locomotion_health=locomotion_health,
            in_affordances=(action in affordance_set),
        ))
    return results


def prompt_block(results: list[GapResult]) -> str:
    """
    [GAP ASSESSMENT] block for the Executive prompt.
    Only shows actions that are CAN, CAN-BUT-*, or CAN-IF-CONDITION.
    BLOCKED and UNKNOWN are omitted — they add noise, not capability.
    """
    if not results:
        return ""
    lines = ["[GAP ASSESSMENT — declared reliable_range, numbers from state]"]
    for r in results:
        if r.status in ("BLOCKED", "UNKNOWN"):
            continue
        dist_str = f"gap={r.gap_distance_px:.0f}px" if r.gap_distance_px is not None else "gap=unknown"
        lines.append(
            f"  {r.action:<12} {r.status:<28} conf={r.confidence:.2f}  "
            f"{dist_str}  reliable={r.reliable_range_px:.0f}px"
        )
    return "\n".join(lines) if len(lines) > 1 else ""
