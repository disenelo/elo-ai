"""
faculties/music_memory/analyser.py — Music significance scoring.

Significance = play_frequency + personal_notes + creative_connection
             + emotional_intensity + time_association

This mirrors significance_engine.py's multi-dimensional approach but
applied to music memory specifically. Music does not become memory
automatically — it becomes a candidate. Score drives eligibility.
"""
from __future__ import annotations

from faculties.music_memory.models import MusicMemory


# ── Dimension weights ─────────────────────────────────────────────────────────
# Sum = 1.0. Play frequency is the loudest signal from platform data.
# Personal notes and creative connection are the loudest signals from David.

_WEIGHTS = {
    "play_frequency":      0.25,
    "personal_notes":      0.25,
    "creative_connection": 0.20,
    "emotional_intensity": 0.15,
    "time_association":    0.15,
}

# Play counts at which significance saturates (0.0 → 1.0 per dimension)
_PLAY_SATURATION = 50   # 50+ plays = full play_frequency score


def score(memory: MusicMemory) -> float:
    """
    Compute a significance score for a music memory.

    Returns a float 0.0 – 1.0.
    0.0  = no signal yet (candidate only)
    0.5+ = eligible for vault write
    0.8+ = high importance memory
    """
    f = memory.fact
    i = memory.interpretation

    # play_frequency — how often the user returns to this
    play_freq = min(f.play_count / _PLAY_SATURATION, 1.0)

    # personal_notes — has David said anything about this track?
    has_notes = 1.0 if i.notes.strip() else 0.0

    # creative_connection — linked to DISENELO projects
    creative = min(len(i.creative_projects) * 0.4, 1.0)

    # emotional_intensity — non-neutral emotion, or explicit mood tags
    has_emotion   = 1.0 if i.emotion not in ("neutral", "", "unknown") else 0.0
    has_mood_tags = min(len(i.mood_tags) * 0.25, 1.0)
    emotional     = max(has_emotion, has_mood_tags)

    # time_association — linked to a specific life period
    time_assoc = 1.0 if i.life_period else 0.0

    dims = {
        "play_frequency":      play_freq,
        "personal_notes":      has_notes,
        "creative_connection": creative,
        "emotional_intensity": emotional,
        "time_association":    time_assoc,
    }

    total = sum(_WEIGHTS[k] * v for k, v in dims.items())
    return round(min(total, 1.0), 3)


def score_and_update(memory: MusicMemory) -> MusicMemory:
    """Compute significance and return a new MusicMemory with it set."""
    from dataclasses import replace
    return replace(memory, significance=score(memory))


def significance_label(sig: float) -> str:
    if sig >= 0.85:
        return "core"
    if sig >= 0.65:
        return "important"
    if sig >= 0.45:
        return "notable"
    if sig >= 0.20:
        return "emerging"
    return "candidate"


def vault_weight(sig: float) -> int:
    """Map significance → vault weight (matches vault_layer weight scale 0–9)."""
    if sig >= 0.85:
        return 8
    if sig >= 0.65:
        return 7
    if sig >= 0.45:
        return 5
    return 3
