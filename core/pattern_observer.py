"""
core/pattern_observer.py — session-level pattern observation.

Phase A — PARTICIPATION → RELATIONSHIP:
    eLo stops responding to sentences and starts responding to meaning.

Tracks (topic, tone) per turn within a session.
Surfaces observations when patterns emerge — contrast or recurrence.

Fire rules:
    - At least 4 turns in session before first observation
    - At least 5 turns between observations
    - At least 2 data points for any pattern to be stated
    - Does not fire during ground/witness actions
"""

from __future__ import annotations
import re
from typing import Optional

# ── topic classification ───────────────────────────────────────────────────────

_TOPIC_PATTERNS: dict[str, list[str]] = {
    "narrative": [r"\bscene\b", r"\bstory\b", r"\bbook\b", r"\bact\b",
                  r"\bnarrative\b", r"\bcharacter\b", r"\bplot\b",
                  r"\bvoice\b", r"\bchapter\b", r"\bmoment\b", r"\bimagine\b",
                  r"\bworld\b", r"\bwrite\b", r"\bwriting\b"],
    "systems":   [r"\bsystem\b", r"\bstructure\b", r"\bcode\b", r"\bengine\b",
                  r"\bpipeline\b", r"\barchitecture\b", r"\bframework\b",
                  r"\bmodule\b", r"\bimplement\b", r"\bwire\b", r"\bapi\b"],
    "robot":     [r"\brobot\b", r"\bhardware\b", r"\bphysical\b",
                  r"\bservo\b", r"\braspberry\b", r"\borb\b"],
    "avatar":    [r"\bavatar\b", r"\bdesktop\b", r"\bpresence\b",
                  r"\bmotion\b", r"\banimate\b", r"\bembodi\b"],
    "concept":   [r"\bwhat\s+if\b", r"\bvision\b",
                  r"\bwhy\b.{1,20}\bexist\b", r"\bmeaning\b", r"\bbecome\b"],
}

# ── tone thresholds ────────────────────────────────────────────────────────────

_ENERGY_OPEN  = 0.62
_ENERGY_TIGHT = 0.38

# ── fire thresholds ────────────────────────────────────────────────────────────

_MIN_TURNS_TO_FIRE   = 4
_MIN_TURNS_BETWEEN   = 5
_MIN_PATTERN_ENTRIES = 2

# ── module-level session state ─────────────────────────────────────────────────

_log: list[dict] = []
_last_fire_turn: int = -10


def _topic(text: str) -> Optional[str]:
    t = text.lower()
    for name, patterns in _TOPIC_PATTERNS.items():
        if any(re.search(p, t) for p in patterns):
            return name
    return None


def _tone(attention_model: dict) -> str:
    emo     = attention_model.get("emotional_context", {})
    energy  = emo.get("energy", 0.5)
    tension = emo.get("tension", 0.4)
    valence = emo.get("valence", "neutral")
    if valence == "positive_high" or energy >= _ENERGY_OPEN:
        return "open"
    if energy <= _ENERGY_TIGHT or tension >= 0.6:
        return "tight"
    return "neutral"


def log(user_input: str, attention_model: dict) -> None:
    """Record this turn's topic + tone. Call after every response."""
    topic = _topic(user_input)
    if topic is None:
        return
    _log.append({
        "topic": topic,
        "tone":  _tone(attention_model),
        "turn":  len(_log),
    })


def observe(current_action: str = "", current_input: str = "") -> Optional[str]:
    """
    Check for a surfaceable pattern. Returns one observation string or None.

    Args:
        current_action: The CAL action for the current turn.
                        Ground and witness actions suppress observation.
        current_input:  The raw user input for the current turn (accepted for
                        call-site parity; not used internally).
    """
    global _last_fire_turn

    # never interrupt grounding or witnessing with an observation
    if current_action in ("ground", "witness", "silence"):
        return None

    turn = len(_log)
    if turn < _MIN_TURNS_TO_FIRE:
        return None
    if (turn - _last_fire_turn) < _MIN_TURNS_BETWEEN:
        return None

    # group entries by topic
    by_topic: dict[str, list[str]] = {}
    for entry in _log:
        t = entry["topic"]
        if t not in by_topic:
            by_topic[t] = []
        by_topic[t].append(entry["tone"])

    # check for tone contrast: one topic mostly open, another mostly tight
    open_topics  = [
        t for t, tones in by_topic.items()
        if tones.count("open")  > tones.count("tight")
        and len(tones) >= _MIN_PATTERN_ENTRIES
    ]
    tight_topics = [
        t for t, tones in by_topic.items()
        if tones.count("tight") > tones.count("open")
        and len(tones) >= _MIN_PATTERN_ENTRIES
    ]

    if open_topics and tight_topics:
        ot = open_topics[0]
        tt = tight_topics[0]
        _last_fire_turn = turn
        return (
            f"Interesting — you sound different when talking about {ot} than {tt}. "
            f"There's more energy when {ot} comes up."
        )

    # check for a recurring single topic (same topic 3+ times)
    recurring = [
        (t, len(tones))
        for t, tones in by_topic.items()
        if len(tones) >= 3
    ]
    if recurring:
        topic, count = max(recurring, key=lambda x: x[1])
        _last_fire_turn = turn
        if count >= 5:
            return f"{topic.capitalize()} keeps coming up. It might be the real thread."
        return f"You keep coming back to {topic}."

    return None


def get_log() -> list:
    """Return a copy of the current session log for persistence."""
    return list(_log)


def reset() -> None:
    """Call at session start."""
    global _log, _last_fire_turn
    _log           = []
    _last_fire_turn = -10
