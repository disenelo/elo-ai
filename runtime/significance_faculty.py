"""
runtime/significance_faculty.py — SP-29 schema layer (WO-NAV-006).

Significance faculty: computes a 14-dimensional significance score from world delta
and (WO-SP29-CONV-SIGNIFICANCE-001) conversational text signals.

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
import re as _re

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


# ── WO-SP29-CONV-SIGNIFICANCE-001: conversational signal patterns ─────────────
# [ESTIMATE] — pattern → (dimension, boost). Boosts are additive to world_delta scores.
# David L3 must set final values at SP-29 D-gate. Do not change without authorisation.

_CONV_SIGNALS: list[tuple[str, str, float]] = [
    # Emotion / distress
    (r"\b(?:overwhelm|anxious|scared|spiralling|spinning|panic)\b",    "relationship",  0.6),  # [ESTIMATE]
    (r"\b(?:excited|breakthrough|figured\s+out|it\s+all\s+connects)\b", "creation",     0.7),  # [ESTIMATE]
    (r"\b(?:amazing|incredible|finally|everything\s+makes\s+sense)\b",  "novelty",      0.6),  # [ESTIMATE]
    # Creative / insight
    (r"\b(?:i\s+figured\s+out|i\s+realised|i\s+understand\s+now)\b",   "learning",     0.65), # [ESTIMATE]
    (r"\b(?:idea|concept|story|vision|arc|design|world)\b",             "creation",     0.35), # [ESTIMATE]
    (r"\b(?:this\s+is\s+it|that(?:'s|\s+is)\s+it|got\s+it)\b",        "novelty",      0.5),  # [ESTIMATE]
    # Conflict / disagreement
    (r"\b(?:wrong|broken|doesn(?:'t|\s+not)\s+work|that\s+fails)\b",   "logic",        0.5),  # [ESTIMATE]
    (r"\b(?:disagree|that(?:'s|\s+is)\s+not\s+right|actually)\b",      "logic",        0.4),  # [ESTIMATE]
    # Relationship / connection
    (r"\b(?:thank\s+you|means\s+a\s+lot|appreciate|grateful)\b",       "relationship", 0.55), # [ESTIMATE]
    (r"\b(?:miss|lonely|tired|exhausted|burnt\s+out)\b",               "relationship", 0.5),  # [ESTIMATE]
    # Deep question
    (r"\b(?:why|what\s+does|what\s+is\s+the\s+point|meaning)\b",      "learning",     0.3),  # [ESTIMATE]
    (r"\b(?:how\s+does|can\s+you\s+explain|walk\s+me\s+through)\b",   "learning",     0.25), # [ESTIMATE]
]


def _score_text_signals(text: str) -> dict[str, float]:
    """
    [ESTIMATE] Scan text for conversational significance signals.
    Returns {dimension: boost} — boosts are NOT yet weighted; caller applies weights.
    WO-SP29-CONV-SIGNIFICANCE-001: additive to world_delta scores.
    """
    if not text:
        return {}
    tl = text.lower()
    boosts: dict[str, float] = {}
    for pattern, dimension, boost in _CONV_SIGNALS:
        if _re.search(pattern, tl):
            boosts[dimension] = max(boosts.get(dimension, 0.0), boost)  # [ESTIMATE] max, not sum
    return boosts


def compute_significance(
    world_delta: dict,
    elo_self_state: dict | None = None,
    text_input: str = "",                    # WO-SP29-CONV-SIGNIFICANCE-001
) -> dict:
    """
    SP-29 schema layer: compute 14-dimensional significance score.

    Args:
        world_delta:    Output of world_delta.compute_delta() — fields: position_changed,
                        gaze_changed, new_platforms_visible, lost_platforms_visible,
                        elapsed_turns, any_change.
        elo_self_state: Optional EloSelfState dict for mood/curiosity weighting.
        text_input:     [WO-SP29-CONV-SIGNIFICANCE-001] Raw conversational text to score
                        for emotional/creative/conflict signals. [ESTIMATE] boosts.

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

    # WO-SP29-CONV-SIGNIFICANCE-001: apply conversational signal boosts
    # [ESTIMATE] boost * weight added to base score; capped at 1.0 per dimension.
    _conv_boosts = _score_text_signals(text_input)
    for dim, boost in _conv_boosts.items():
        if dim in scores:
            weighted_boost = round(boost * _WEIGHTS.get(dim, 0.1), 4)  # [ESTIMATE]
            scores[dim] = round(min(1.0, scores[dim] + weighted_boost), 4)  # [ESTIMATE]

    # [ESTIMATE] overall = mean of all dimension scores
    scores["overall"] = round(sum(scores.values()) / len(scores), 4)           # [ESTIMATE]

    # WO-SPG-HOOKS-001: tap significance spikes for SPG signal logger
    try:
        if scores["overall"] > 0.6:
            from memory.spg_capture import get_capture as _spg_get
            _top_dim = max(
                ((k, v) for k, v in scores.items() if k != "overall"),
                key=lambda kv: kv[1],
            )
            _spg_get().log(
                "significance_spike",
                significance=scores,
                edge_hint=_top_dim[0],
            )
    except Exception:
        pass

    return scores


def derive_affective_state(scores: dict, text_input: str = "") -> "AffectiveState":
    """
    WO-AFFECTIVE-STATE-001: Derive 13-dimensional AffectiveState from SP-29 scores.

    Maps significance dimensions to affective geometry.
    [ESTIMATE] — mappings are heuristic until David L3 calibration.
    """
    from runtime.contracts import AffectiveState

    overall = scores.get("overall", 0.0)
    novelty_s = scores.get("novelty", 0.0)
    learning_s = scores.get("learning", 0.0)
    relationship_s = scores.get("relationship", 0.0)
    creation_s = scores.get("creation", 0.0)
    safety_s = scores.get("safety", 0.0)
    reward_s = scores.get("reward", 0.0)
    logic_s = scores.get("logic", 0.0)

    # [ESTIMATE] derive affective dims from significance dims
    _tl = text_input.lower() if text_input else ""
    _distress = bool(_re.search(r"\b(?:overwhelm|anxious|scared|panic|spiralling)\b", _tl))
    _positive = bool(_re.search(r"\b(?:excited|amazing|breakthrough|incredible|finally)\b", _tl))
    _creative = bool(_re.search(r"\b(?:idea|design|vision|story|concept|build)\b", _tl))

    valence = min(1.0, max(-1.0,
        (relationship_s * 2.0 + reward_s * 2.0 + creation_s - logic_s * 0.5)
        + (0.4 if _positive else 0.0) - (0.5 if _distress else 0.0)
    ))
    arousal = min(1.0, overall * 1.5 + (0.3 if _positive else 0.0))
    safety = min(1.0, safety_s * 5.0 + 0.5 - (0.4 if _distress else 0.0))
    novelty = min(1.0, novelty_s * 8.0)
    curiosity = min(1.0, (learning_s * 5.0 + novelty_s * 3.0)
                    + (0.2 if _creative else 0.0))
    confidence = min(1.0, 0.6 - logic_s * 2.0 + safety_s * 3.0)
    uncertainty = min(1.0, 1.0 - confidence)
    attachment = min(1.0, relationship_s * 6.0)
    tension = min(1.0, (0.4 if _distress else 0.0) + logic_s * 2.0)
    comfort = min(1.0, safety_s * 4.0 + (0.3 if not _distress else 0.0))
    agency = min(1.0, 0.5 + creation_s * 3.0 - (0.2 if _distress else 0.0))
    significance = min(1.0, overall)
    reward_v = min(1.0, reward_s * 8.0)

    return AffectiveState(
        valence=round(valence, 3),
        arousal=round(arousal, 3),
        safety=round(max(0.0, safety), 3),
        novelty=round(novelty, 3),
        curiosity=round(curiosity, 3),
        confidence=round(max(0.0, confidence), 3),
        uncertainty=round(uncertainty, 3),
        attachment=round(attachment, 3),
        tension=round(tension, 3),
        comfort=round(max(0.0, comfort), 3),
        agency=round(max(0.0, agency), 3),
        significance=round(significance, 3),
        reward=round(reward_v, 3),
    )
