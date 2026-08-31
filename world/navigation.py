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
    requires_run_up: bool  = False   # WO-PRES-001: True when a run-up is needed to reach this surface
    route_nodes:     list  = None    # WO-PRES-001: [{action, surface/from/to, run_up}] for run-up candidates


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
    run_capability: bool  = True,
    run_up_distance_px: float = 120.0,
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

        # WO-PRES-001: run-up candidate when gap > jump_px but within jump + run_up_bonus
        run_up_bonus = jump_px * 0.25
        requires_run_up = False
        run_up_nodes = None
        if (
            not reachable
            and run_capability
            and jump_px > 0
            and jump_px < horizontal_gap <= jump_px + run_up_bonus
            and bool(requires_verb)
        ):
            requires_run_up = True
            reachable = True
            run_up_nodes = [
                {"action": "run_on_current", "surface": source_key},
                {"action": "jump", "from": source_key, "to": to_key, "run_up": True},
            ]

        rc = _route_confidence_for_win_id(to_win_id, route_history)

        candidates.append(Candidate(
            target_win_id=to_win_id,
            horizontal_gap=horizontal_gap,
            euclidean_gap_px=euclidean_gap,
            requires_verb=requires_verb,
            reachable=reachable,
            route_confidence=rc,
            requires_run_up=requires_run_up,
            route_nodes=run_up_nodes,
        ))

    return candidates


def _route_confidence_for_win_id(target_win_id: int, route_history: list) -> float:
    """Delegate to route_memory SP-14 function; return 0.5 on any error."""
    try:
        from self.route_memory import route_confidence_by_win_id as _rc
        return _rc(target_win_id, route_history)
    except Exception:
        return 0.5


# ── WO-PRES-005: Alternative route evaluation ─────────────────────────────────

_NAVIGATION_FAILED = {"outcome": "navigation_failed"}
_MAX_INTERMEDIATES = 3   # performance guard — never evaluate more than this


def evaluate_alternatives(
    body_win_id: int,
    destination_win_id: int,
    surface_edges: tuple,
    surface_index: dict,
    jump_px: int,
    route_history: list,
    run_capability: bool  = True,
    run_up_distance_px: float = 120.0,
    wrap_available: bool  = False,
) -> dict:
    """
    WO-PRES-005: bounded alternative-route evaluation.

    Evaluation ladder (fixed depth):
      1. DIRECT       — jump straight to destination
      2. INTERMEDIATE — jump to a closer surface, then to destination (≤3 candidates)
      3. RUN-UP       — run-up then jump if run_capability=True
      4. WRAP         — wrap_bottom_to_top route leg if wrap_available=True
      5. GIVE-UP      — return navigation_failed

    Returns a dict:
      {"outcome": "direct",        "route_nodes": [...]} — direct jump
      {"outcome": "intermediate",  "route_nodes": [...]} — two-leg
      {"outcome": "run_up",        "route_nodes": [...]} — run-up jump
      {"outcome": "wrap",          "route_nodes": [...]} — wrap leg
      {"outcome": "navigation_failed"}
    """
    run_up_bonus = jump_px * 0.25

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _key(win_id: int) -> str:
        return f"win-{win_id}"

    def _horizontal_gap(from_win_id: int, to_win_id: int) -> float:
        src = surface_index.get(from_win_id, {}).get("rect_px", [0, 0, 0, 0])
        tgt = surface_index.get(to_win_id,   {}).get("rect_px", [0, 0, 0, 0])
        return float(tgt[0] - (src[0] + src[2]))

    def _edge_for(from_win_id: int, to_win_id: int) -> dict | None:
        fk, tk = _key(from_win_id), _key(to_win_id)
        for e in surface_edges:
            if e.get("from") == fk and e.get("to") == tk:
                return e
        return None

    def _direct_reachable(from_id: int, to_id: int) -> bool:
        gap = _horizontal_gap(from_id, to_id)
        e   = _edge_for(from_id, to_id)
        return (e is not None) and bool(e.get("requires_verb")) and (gap <= jump_px)

    def _run_up_reachable(from_id: int, to_id: int) -> bool:
        if not run_capability or jump_px <= 0:
            return False
        gap = _horizontal_gap(from_id, to_id)
        e   = _edge_for(from_id, to_id)
        return (e is not None) and bool(e.get("requires_verb")) and (jump_px < gap <= jump_px + run_up_bonus)

    # ── 1. DIRECT ───────────────────────────────────────────────────────────────
    if _direct_reachable(body_win_id, destination_win_id):
        return {
            "outcome": "direct",
            "route_nodes": [
                {"action": "jump", "from": _key(body_win_id), "to": _key(destination_win_id)},
            ],
        }

    # ── 2. INTERMEDIATE ─────────────────────────────────────────────────────────
    _checked = 0
    for mid_id in surface_index:
        if mid_id in (body_win_id, destination_win_id):
            continue
        if _checked >= _MAX_INTERMEDIATES:
            break
        _checked += 1
        if _direct_reachable(body_win_id, mid_id) and _direct_reachable(mid_id, destination_win_id):
            return {
                "outcome": "intermediate",
                "route_nodes": [
                    {"action": "jump", "from": _key(body_win_id),   "to": _key(mid_id)},
                    {"action": "jump", "from": _key(mid_id),        "to": _key(destination_win_id)},
                ],
            }

    # ── 3. RUN-UP ───────────────────────────────────────────────────────────────
    if _run_up_reachable(body_win_id, destination_win_id):
        return {
            "outcome": "run_up",
            "route_nodes": [
                {"action": "run_on_current", "surface": _key(body_win_id)},
                {"action": "jump", "from": _key(body_win_id), "to": _key(destination_win_id), "run_up": True},
            ],
        }

    # ── 4. WRAP ─────────────────────────────────────────────────────────────────
    if wrap_available:
        return {
            "outcome": "wrap",
            "route_nodes": [
                {"action": "wrap_bottom_to_top"},
                {"action": "jump", "from": _key(body_win_id), "to": _key(destination_win_id)},
            ],
        }

    # ── 5. GIVE-UP ──────────────────────────────────────────────────────────────
    return _NAVIGATION_FAILED
