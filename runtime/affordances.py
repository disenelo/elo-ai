"""
runtime/affordances.py — WO-056: Affordances on the World Model

Affordance Before Action (ADR-Exec-003 LAW):
The Executive searches POSSIBILITIES, not animations.

Maps surface_type → frozenset of available actions.
Surface types come from the desktop/world model (window_top, window_body,
desktop_floor, unknown). Actions use the 049-A verb vocabulary.

WO-113: GAP state — seven-state capability assessment with real numbers.
"""
from __future__ import annotations
from dataclasses import dataclass

# ── Affordance table ──────────────────────────────────────────────────────────
# Each surface maps to a frozenset of action verbs.
# Verb vocabulary matches the ratified 049-A contract.

SURFACE_AFFORDANCES: dict[str, frozenset] = {
    "window_top":    frozenset({
        "stand", "run", "jump", "wall-jump", "wall-run", "peek", "enter", "exit",
    }),
    "window_body":   frozenset({
        "wall-jump", "wall-run", "climb", "hide", "peek",
    }),
    "window_bottom": frozenset({
        "stand", "peek", "exit",
    }),
    "desktop_floor": frozenset({
        "stand", "run", "jump",
    }),
    "taskbar":       frozenset({
        "stand", "run", "jump", "enter",
    }),
    "unknown":       frozenset({
        "stand", "run",
    }),
}

# Canonical ordered form for display / prompt injection
_ORDER = [
    "stand", "run", "jump", "wall-jump", "wall-run", "climb",
    "hide", "peek", "enter", "exit",
]


def affordances_for(surface_type: str) -> tuple:
    """
    Return a sorted tuple of affordances for the given surface.

    Args:
        surface_type — one of the SURFACE_AFFORDANCES keys, or any unknown string.

    Returns:
        Sorted tuple of action verb strings.
        Falls back to ("stand", "run") for unrecognised surfaces.
    """
    verbs = SURFACE_AFFORDANCES.get(surface_type, SURFACE_AFFORDANCES["unknown"])
    return tuple(v for v in _ORDER if v in verbs)


def prompt_block(surface_type: str) -> str:
    """
    Formatted [AFFORDANCES] block for the Executive prompt.

    The Executive reads this before deciding — it consults possibility, not
    geometry. If a verb isn't in this list, eLo cannot do it right now.
    """
    verbs = affordances_for(surface_type)
    if not verbs:
        return ""
    verb_str = " · ".join(verbs)
    return f"[AFFORDANCES surface={surface_type}] {verb_str}"


# ── WO-113: GAP state — seven-state capability assessment ────────────────────

# Seven gap states (§6 — never yes/no).
GAP_CAN                  = "CAN"
GAP_CANNOT               = "CANNOT"
GAP_CAN_BUT_DEGRADED     = "CAN-BUT-DEGRADED"
GAP_CAN_BUT_LOW_CONF     = "CAN-BUT-LOW-CONFIDENCE"
GAP_CAN_IF_CONDITION     = "CAN-IF-CONDITION"
GAP_UNKNOWN              = "UNKNOWN"
GAP_BLOCKED              = "BLOCKED"

# Declared limits from EloDesktopNav.cs (maxJumpEloHeights=1.5f; DesktopBuddy.cs MaxHopDist()).
# Source: declared (not learned). Mark clearly — do not let a constant masquerade as experience.
# Until Ruling E lands (learned values), these are the reliable_range bounds.
_DECLARED_RELIABLE_PX: dict[str, float] = {
    "jump":      200.0,   # desktop floor hop; declared from MaxHopDist gate
    "wall-jump": 160.0,   # wall-to-surface; slightly tighter than floor jump
    "wall-run":  120.0,   # sustained wall contact; confidence degrades with distance
    "climb":      80.0,   # short ledge grab
    "run":       999.0,   # no gap limit on running
    "stand":     999.0,
}
_DECLARED_SOURCE = "declared"  # source tag — not yet learned from experience


@dataclass
class GapAssessment:
    """
    WO-113: Gap state for a single action.

    status        — one of the seven GAP_* constants
    verb          — the action being assessed
    confidence    — 0.0–1.0
    gap_distance  — current gap in pixels (None = unknown)
    reliable_range — declared/learned limit in pixels
    source        — "declared" | "learned"
    detail        — human-readable explanation with numbers
    """
    status:        str
    verb:          str
    confidence:    float
    gap_distance:  float | None
    reliable_range: float
    source:        str
    detail:        str


def gap_state(
    verb: str,
    gap_distance: float | None = None,
    body_size: float = 1.0,
    surface_type: str = "unknown",
) -> GapAssessment:
    """
    WO-113: Return a GapAssessment for `verb` given current geometry.

    Args:
        verb         — action to assess (e.g. "wall-jump", "jump")
        gap_distance — distance to target in pixels; None = unknown
        body_size    — eLo's size multiplier (from EloSelfState.size, default 1.0)
        surface_type — current surface (used to check BLOCKED)

    Returns GapAssessment with status, numbers, and detail string.
    The returned detail string carries the real numbers — never adjectives alone.
    """
    verbs_here = affordances_for(surface_type)

    # BLOCKED: surface doesn't support this verb
    if verb not in verbs_here:
        return GapAssessment(
            status=GAP_BLOCKED, verb=verb, confidence=0.0,
            gap_distance=gap_distance,
            reliable_range=_DECLARED_RELIABLE_PX.get(verb, 0.0) * body_size,
            source=_DECLARED_SOURCE,
            detail=f"{verb} not possible on {surface_type} surface",
        )

    reliable = _DECLARED_RELIABLE_PX.get(verb, 999.0) * body_size

    # UNKNOWN: no geometry information
    if gap_distance is None:
        return GapAssessment(
            status=GAP_UNKNOWN, verb=verb, confidence=0.5,
            gap_distance=None,
            reliable_range=reliable,
            source=_DECLARED_SOURCE,
            detail=f"{verb}: gap unknown — no geometry data this turn",
        )

    ratio = gap_distance / reliable if reliable > 0 else float("inf")

    if ratio <= 0.8:
        return GapAssessment(
            status=GAP_CAN, verb=verb, confidence=0.9,
            gap_distance=gap_distance, reliable_range=reliable,
            source=_DECLARED_SOURCE,
            detail=(
                f"{verb}: gap_distance={gap_distance:.0f}px, "
                f"reliable_range={reliable:.0f}px (source: {_DECLARED_SOURCE}) — within range"
            ),
        )
    if ratio <= 1.0:
        return GapAssessment(
            status=GAP_CAN_BUT_LOW_CONF, verb=verb, confidence=round(1.0 - (ratio - 0.8) * 2.5, 2),
            gap_distance=gap_distance, reliable_range=reliable,
            source=_DECLARED_SOURCE,
            detail=(
                f"{verb}: gap_distance={gap_distance:.0f}px, "
                f"reliable_range={reliable:.0f}px (source: {_DECLARED_SOURCE}) — near limit, low confidence"
            ),
        )
    if ratio <= 1.2:
        return GapAssessment(
            status=GAP_CAN_BUT_DEGRADED, verb=verb, confidence=round(1.0 - (ratio - 1.0) * 2.5, 2),
            gap_distance=gap_distance, reliable_range=reliable,
            source=_DECLARED_SOURCE,
            detail=(
                f"{verb}: gap_distance={gap_distance:.0f}px exceeds "
                f"reliable_range={reliable:.0f}px (source: {_DECLARED_SOURCE}) — possible but risky"
            ),
        )
    return GapAssessment(
        status=GAP_CANNOT, verb=verb, confidence=0.0,
        gap_distance=gap_distance, reliable_range=reliable,
        source=_DECLARED_SOURCE,
        detail=(
            f"{verb}: gap_distance={gap_distance:.0f}px far exceeds "
            f"reliable_range={reliable:.0f}px (source: {_DECLARED_SOURCE}) — cannot clear gap"
        ),
    )
