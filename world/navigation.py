"""
world/navigation.py — WO-NAV-010: SP-12 + SP-11

SP-12: Surface identity bridge — int win_id → surface dict, built from surface_graph.nodes
       at LiveWorldState assembly time.

SP-11: Candidate generation — produces a Candidate list from current body position,
       surface graph edges, and route history.

Phase 2 scope: ledge-to-ledge (horizontal) candidates only.
Nodes with kind="overhang" or kind="wall" are excluded per SP-11 contract.
"""
from __future__ import annotations

from dataclasses import dataclass


# ── SP-11: Candidate dataclass ────────────────────────────────────────────────

@dataclass
class Candidate:
    """One candidate surface reachable (or not) from current body position."""
    target_win_id:   int
    horizontal_gap:  float
    euclidean_gap_px: float
    requires_verb:   str
    reachable:       bool
    route_confidence: float


# ── SP-12: Surface identity bridge ───────────────────────────────────────────

def build_surface_index(surfaces: tuple) -> dict:
    """
    SP-12: Map int win_id → surface dict from LiveWorldState.surfaces.

    surfaces entries carry win_id as the original node id string e.g. 'win-1679'.
    Returns {} on empty or unparseable input.
    """
    index: dict = {}
    for s in surfaces:
        raw_id = s.get("win_id", "")
        try:
            if "win-" in raw_id:
                int_id = int(raw_id.split("win-")[1])
            else:
                int_id = int(raw_id)
            index[int_id] = s
        except (IndexError, ValueError, TypeError):
            pass
    return index


# ── SP-11: Candidate generation ───────────────────────────────────────────────

def generate_candidates(
    body_win_id: int,
    surface_edges: tuple,
    surface_index: dict,
    jump_px: int,
    route_history: list,
) -> list:
    """
    SP-11: Generate candidate surfaces reachable from body_win_id.

    Returns [] immediately when body_win_id == -1 (mid-hop / unknown per SP-9 / L3-NAV-3).

    route_history is a list of route_memory records (assembled at world-state time).
    route_confidence is populated per SP-14; defaults to 0.5 when no history exists.

    Phase 2 scope: ledge-to-ledge (horizontal) only.
    Excluded: kind='overhang', kind='wall'.
    """
    if body_win_id == -1:
        return []

    source_key = f"win-{body_win_id}"
    source = surface_index.get(body_win_id)
    if source is None:
        return []

    src_rect = source.get("rect_px", [0, 0, 0, 0])
    candidates: list = []

    for edge in surface_edges:
        if edge.get("from") != source_key:
            continue

        to_key = edge.get("to", "")
        try:
            to_win_id = (
                int(to_key.split("win-")[1]) if "win-" in to_key else int(to_key)
            )
        except (IndexError, ValueError, TypeError):
            continue

        target = surface_index.get(to_win_id)
        if target is None:
            continue

        # Phase 2: ledge-to-ledge only
        kind = target.get("kind", "window")
        if kind in ("overhang", "wall"):
            continue

        tgt_rect = target.get("rect_px", [0, 0, 0, 0])
        # SP-8/L3-NAV-1: horizontal gap from rect_px (right edge of source to left edge of target)
        horizontal_gap = float(tgt_rect[0] - (src_rect[0] + src_rect[2]))

        euclidean_gap = float(edge.get("gap_px", 0))
        requires_verb = str(edge.get("requires_verb", ""))

        # SP-8: reachability — horizontal gap within jump capability AND verb available
        reachable = (horizontal_gap <= jump_px) and bool(requires_verb)

        rc = _route_confidence_for_win_id(to_win_id, route_history)

        candidates.append(Candidate(
            target_win_id=to_win_id,
            horizontal_gap=horizontal_gap,
            euclidean_gap_px=euclidean_gap,
            requires_verb=requires_verb,
            reachable=reachable,
            route_confidence=rc,
        ))

    return candidates


def _route_confidence_for_win_id(target_win_id: int, route_history: list) -> float:
    """Delegate to route_memory SP-14 function; return 0.5 on any error."""
    try:
        from self.route_memory import route_confidence_by_win_id as _rc
        return _rc(target_win_id, route_history)
    except Exception:
        return 0.5
