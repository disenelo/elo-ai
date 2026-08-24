"""
SP-17 (WO-NAV-003) — Referent Resolver.

Maps speech deixis ("that platform", "over there", "the ledge I'm looking at")
to a win_id from world_dict, using gaze_win_id as the primary proximal signal.

Contract:
  - Reads world_dict and elo_spatial.json only.
  - Never calls the Executive or the LLM.
  - Unresolvable input → returns None. Caller handles the None case.
  - Pure lookup — no side effects, no writes.
"""

from __future__ import annotations
import re

_PROXIMAL = re.compile(
    r"\b(?:this|here|that|there|over\s+there|the\s+(?:platform|ledge|surface|thing)\s+"
    r"i(?:'m|\s+am)\s+looking\s+at)\b",
    re.IGNORECASE,
)


def resolve(text: str, world_dict: dict, spatial: dict | None = None) -> int | None:
    """
    Resolve a natural-language surface referent to a win_id.

    Args:
        text:       The user utterance or referent phrase.
        world_dict: The assembled world state dict (must contain 'gaze_win_id').
        spatial:    Optional pre-loaded elo_spatial.json dict (avoids re-read if caller
                    already has it). If None, surface-graph label search is skipped.

    Returns:
        int win_id if resolved, None if unresolvable.
    """
    # 1. Proximal deixis → gaze_win_id
    if _PROXIMAL.search(text):
        gaze_id = world_dict.get("gaze_win_id", 0)
        if gaze_id:
            return int(gaze_id)

    # 2. Named surface → search surface_graph by label
    if spatial:
        surface_graph = spatial.get("surface_graph", {})
        text_lower = text.lower()
        for node_id, node in surface_graph.items():
            label = str(node.get("label", "")).lower()
            if label and label in text_lower:
                win = node.get("win_id") or node.get("id")
                if win is not None:
                    return int(win)

    return None
