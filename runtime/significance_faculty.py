"""
runtime/significance_faculty.py — SP-29 schema layer (WO-NAV-006).

Significance faculty: computes a 14-dimensional significance score from world delta.

[ESTIMATE] weights: all currently uniform / placeholder values.
David L3 will specify final weights when behavioural decisions are made (D-gate SP-29).
Do NOT change weights without David L3 authorisation.

14 dimensions:
  presence, learning, logic, humour, relationship, creation,
  system_change, novelty, continuity, overall, embodiment,
  efficiency, safety, reward
"""
from __future__ import annotations

import logging

_log = logging.getLogger(__name__)

# [ESTIMATE] Uniform placeholder weights — one per dimension.
# Final values are a David L3 D-gate decision (SP-29).
_WEIGHTS = {
    "presence":      0.1,   # [ESTIMATE]
    "learning":      0.1,   # [ESTIMATE]
    "logic":         0.1,   # [ESTIMATE]
    "humour":        0.1,   # [ESTIMATE]
    "relationship":  0.1,   # [ESTIMATE]
    "creation":      0.1,   # [ESTIMATE]
    "system_change": 0.1,   # [ESTIMATE]
    "novelty":       0.1,   # [ESTIMATE]
    "continuity":    0.1,   # [ESTIMATE]
    "embodiment":    0.1,   # [ESTIMATE]
    "efficiency":    0.1,   # [ESTIMATE]
    "safety":        0.1,   # [ESTIMATE]
    "reward":        0.1,   # [ESTIMATE]
}

_DIMENSIONS = list(_WEIGHTS.keys())


def compute_significance(world_delta: dict, elo_self_state: dict | None = None) -> dict:
    """
    SP-29 schema layer: compute 14-dimensional significance score.

    Args:
        world_delta:    Output of world_delta.compute_delta() — fields: position_changed,
                        gaze_changed, new_platforms_visible, lost_platforms_visible,
                        elapsed_turns, any_change.
        elo_self_state: Optional EloSelfState dict for mood/curiosity weighting.

    Returns dict with 14 dimension scores (float 0.0–1.0) + "overall".
    All weights are [ESTIMATE] placeholders — D-gated to David L3.
    """
    if elo_self_state is None:
        elo_self_state = {}

    any_change   = bool(world_delta.get("any_change", False))
    gaze_changed = bool(world_delta.get("gaze_changed", False))
    pos_changed  = bool(world_delta.get("position_changed", False))
    new_plat     = bool(world_delta.get("new_platforms_visible"))
    lost_plat    = bool(world_delta.get("lost_platforms_visible"))

    # [ESTIMATE] Heuristic scoring — placeholder until David L3 specifies final logic.
    novelty_raw       = 1.0 if any_change else 0.0           # [ESTIMATE]
    embodiment_raw    = 1.0 if pos_changed else 0.0           # [ESTIMATE]
    system_change_raw = 1.0 if (new_plat or lost_plat) else 0.0  # [ESTIMATE]
    continuity_raw    = 0.0 if any_change else 1.0            # [ESTIMATE] inverse of novelty
    presence_raw      = 1.0 if gaze_changed else 0.0          # [ESTIMATE]

    scores = {
        "presence":      round(presence_raw * _WEIGHTS["presence"], 4),        # [ESTIMATE]
        "learning":      round(0.5 * _WEIGHTS["learning"], 4),                 # [ESTIMATE]
        "logic":         round(0.5 * _WEIGHTS["logic"], 4),                    # [ESTIMATE]
        "humour":        round(0.0 * _WEIGHTS["humour"], 4),                   # [ESTIMATE]
        "relationship":  round(0.5 * _WEIGHTS["relationship"], 4),             # [ESTIMATE]
        "creation":      round(0.0 * _WEIGHTS["creation"], 4),                 # [ESTIMATE]
        "system_change": round(system_change_raw * _WEIGHTS["system_change"], 4), # [ESTIMATE]
        "novelty":       round(novelty_raw * _WEIGHTS["novelty"], 4),           # [ESTIMATE]
        "continuity":    round(continuity_raw * _WEIGHTS["continuity"], 4),     # [ESTIMATE]
        "embodiment":    round(embodiment_raw * _WEIGHTS["embodiment"], 4),     # [ESTIMATE]
        "efficiency":    round(0.5 * _WEIGHTS["efficiency"], 4),               # [ESTIMATE]
        "safety":        round(1.0 * _WEIGHTS["safety"], 4),                   # [ESTIMATE] safety always baseline
        "reward":        round(0.0 * _WEIGHTS["reward"], 4),                   # [ESTIMATE]
    }

    # [ESTIMATE] overall = mean of all dimension scores
    scores["overall"] = round(sum(scores.values()) / len(scores), 4)           # [ESTIMATE]

    return scores
