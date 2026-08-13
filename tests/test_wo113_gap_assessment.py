"""
tests/test_wo113_gap_assessment.py — WO-113: 7-state gap vocabulary.

AT-113-1: All 7 gap states are reachable (at least 4 on real scenarios)
AT-113-2: BLOCKED when action not in surface affordances
AT-113-3: UNKNOWN when gap_distance_px is None
AT-113-4: CAN when gap < 85% of reliable_range
AT-113-5: CAN-BUT-LOW-CONFIDENCE when gap is 86-100% of reliable_range
AT-113-6: CAN-IF-CONDITION when gap > reliable_range but ≤ max
AT-113-7: CANNOT when gap > 1.2× max range
AT-113-8: CAN-BUT-DEGRADED when locomotion health is DEGRADED
AT-113-9: Changing body size changes reliable_range (capability join is real)
AT-113-10: gap_assessment key present in compile() output (Executive-visible)
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from runtime.gap_assessment import (
    assess, GapResult, GAP_STATES,
    _reliable_range, _elo_height_px, _COMFORTABLE_MARGIN, _CANNOT_FACTOR,
)


def _reliable(spatial: dict) -> float:
    return _reliable_range(_elo_height_px(spatial))


_SPATIAL_STD = {"height": 0.065, "screen_h": 1440, "screen_w": 2560}  # ≈94px height
_JUMP_AFFORDANCE = ("jump", "wall-run", "wall_jump", "stand", "run")
_NO_JUMP_AFFORDANCE = ("stand", "run")  # no gap-crossing actions


# ── AT-113-1: all 7 states reachable ─────────────────────────────────────────

def test_all_seven_states_reachable():
    rr = _reliable(_SPATIAL_STD)
    scenarios = [
        # CAN
        assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=rr * 0.5),
        # CANNOT
        assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=rr * 2.5),
        # CAN-BUT-DEGRADED
        assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=rr * 0.5,
               locomotion_health="DEGRADED"),
        # CAN-BUT-LOW-CONFIDENCE
        assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=rr * 0.92),
        # CAN-IF-CONDITION
        assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=rr * 1.05),
        # UNKNOWN
        assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=None),
        # BLOCKED
        assess(_NO_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=rr * 0.5),
    ]
    found_statuses = set()
    for results in scenarios:
        for r in results:
            found_statuses.add(r.status)
    assert found_statuses == GAP_STATES, (
        f"Not all 7 states covered. Found: {found_statuses} Missing: {GAP_STATES - found_statuses}"
    )


# ── AT-113-2: BLOCKED when action not in affordances ─────────────────────────

def test_blocked_when_not_in_affordances():
    rr = _reliable(_SPATIAL_STD)
    results = assess(_NO_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=rr * 0.3)
    blocked = [r for r in results if r.status == "BLOCKED"]
    assert blocked, "Expected BLOCKED for jump-class actions not in affordances"
    assert all(r.action in ("jump", "wall-run", "wall_jump") for r in blocked)


# ── AT-113-3: UNKNOWN when gap_distance_px is None ───────────────────────────

def test_unknown_when_no_gap_data():
    results = assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=None)
    unknown = [r for r in results if r.status == "UNKNOWN"]
    assert unknown, "Expected UNKNOWN status when gap_distance_px is None"
    for r in unknown:
        assert r.gap_distance_px is None
        assert r.confidence == 0.0


# ── AT-113-4: CAN when gap < 85% of reliable_range ──────────────────────────

def test_can_when_gap_within_comfortable_margin():
    rr = _reliable(_SPATIAL_STD)
    safe_gap = rr * (_COMFORTABLE_MARGIN - 0.05)  # clearly within margin
    results = assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=safe_gap)
    can = [r for r in results if r.status == "CAN"]
    assert can, f"Expected at least one CAN result, gap={safe_gap:.1f}px, reliable={rr:.1f}px"
    for r in can:
        assert r.confidence > 0.5, f"CAN result has low confidence: {r.confidence}"


# ── AT-113-5: CAN-BUT-LOW-CONFIDENCE when 86-100% of reliable_range ─────────

def test_can_but_low_confidence_at_margin():
    rr = _reliable(_SPATIAL_STD)
    borderline_gap = rr * 0.92  # inside max but outside comfortable margin
    results = assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=borderline_gap)
    low_conf = [r for r in results if r.status == "CAN-BUT-LOW-CONFIDENCE"]
    assert low_conf, (
        f"Expected CAN-BUT-LOW-CONFIDENCE at gap={borderline_gap:.1f}px, reliable={rr:.1f}px"
    )


# ── AT-113-6: CAN-IF-CONDITION when gap > reliable but ≤ max ─────────────────

def test_can_if_condition_beyond_reliable_range():
    rr = _reliable(_SPATIAL_STD)
    stretch_gap = rr * 1.05  # beyond reliable, within max
    results = assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=stretch_gap)
    cond = [r for r in results if r.status == "CAN-IF-CONDITION"]
    assert cond, (
        f"Expected CAN-IF-CONDITION at gap={stretch_gap:.1f}px, reliable={rr:.1f}px"
    )
    for r in cond:
        assert "run-up" in r.reason.lower() or "condition" in r.reason.lower()


# ── AT-113-7: CANNOT when gap > 1.2× max range ───────────────────────────────

def test_cannot_when_clearly_out_of_range():
    rr = _reliable(_SPATIAL_STD)
    max_range = rr / _COMFORTABLE_MARGIN
    impossible_gap = max_range * (_CANNOT_FACTOR + 0.1)
    results = assess(_JUMP_AFFORDANCE, spatial=_SPATIAL_STD, gap_distance_px=impossible_gap)
    cannot = [r for r in results if r.status == "CANNOT"]
    assert cannot, (
        f"Expected CANNOT at gap={impossible_gap:.1f}px, max={max_range:.1f}px"
    )


# ── AT-113-8: CAN-BUT-DEGRADED when locomotion health is DEGRADED ─────────────

def test_can_but_degraded_when_health_degraded():
    rr = _reliable(_SPATIAL_STD)
    results = assess(
        _JUMP_AFFORDANCE, spatial=_SPATIAL_STD,
        gap_distance_px=rr * 0.5,
        locomotion_health="DEGRADED",
    )
    degraded = [r for r in results if r.status == "CAN-BUT-DEGRADED"]
    assert degraded, "Expected CAN-BUT-DEGRADED when locomotion_health=DEGRADED"
    for r in degraded:
        assert r.confidence < 0.5, f"Degraded result should have low confidence: {r.confidence}"


# ── AT-113-9: body size change → reliable_range changes ─────────────────────

def test_body_size_changes_reliable_range():
    small_spatial = {"height": 0.04, "screen_h": 1440}   # small eLo
    large_spatial = {"height": 0.12, "screen_h": 1440}   # large eLo

    rr_small = _reliable(small_spatial)
    rr_large = _reliable(large_spatial)

    assert rr_large > rr_small, (
        f"Larger body must have greater reliable_range: {rr_large:.1f} > {rr_small:.1f}"
    )

    # Assign a gap that is CAN for large but CANNOT for small
    mid_gap = (rr_small * (_COMFORTABLE_MARGIN - 0.05)) * 1.0 + (rr_large * 0.1)
    r_small = assess(_JUMP_AFFORDANCE, spatial=small_spatial, gap_distance_px=mid_gap)
    r_large = assess(_JUMP_AFFORDANCE, spatial=large_spatial, gap_distance_px=mid_gap)

    statuses_small = {r.status for r in r_small}
    statuses_large = {r.status for r in r_large}
    assert statuses_small != statuses_large, (
        "Body size change must change gap assessment — prove capability join is real. "
        f"Small: {statuses_small}  Large: {statuses_large}"
    )


# ── AT-113-10: compile() exposes gap_assessment to Executive ──────────────────

def test_moment_compile_includes_gap_assessment():
    from runtime.the_moment import compile as tm_compile
    from unittest.mock import MagicMock
    state = MagicMock()
    state.embodiment = "desktop"
    state.pose = "perched"
    state.surface = "Terminal"
    state.location = ""
    state.balance = "stable"
    state.size = {"height_cm": 18, "reach_cm": 30, "jump_cm": 30}
    state.available_actions = ["jump", "run", "stand"]
    state.current_action = "idle"
    state.locomotion_faculty_health = "OK"
    state.nearby_surfaces = []
    state.mood = 0.5
    state.curiosity = 0.5
    state.goal = ""
    state.last_updated = 0.0
    state.recent_behavior = {}

    moment = tm_compile(state)
    assert "gap_assessment" in moment, (
        "compile() must include 'gap_assessment' key — Executive can't see it otherwise"
    )
    assert isinstance(moment["gap_assessment"], list), (
        f"gap_assessment should be a list, got: {type(moment['gap_assessment'])}"
    )
