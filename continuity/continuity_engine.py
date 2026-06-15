"""
continuity/continuity_engine.py — derives meaning-memory from session state.

Reads from session_state (output of state_manager.load()).
Extracts emotion, theme, project, direction — not raw text.
Answers: "What changed?" / "What stayed?" / "What matters?"
"""
from __future__ import annotations
from collections import Counter

from continuity.identity_state import (
    IdentityState,
    _TONE_TO_DIRECTION,
    _PROJECT_KEYWORDS,
    _THEME_KEYWORDS,
)


def from_state(session_state: dict) -> IdentityState:
    """
    Derive IdentityState from session_state dict.
    All extraction is meaning-based — no raw text stored.
    """
    topics           = session_state.get("last_topics", [])
    emotional_history = session_state.get("emotional_history", [])
    session_count    = session_state.get("session_count", 0)
    summaries        = session_state.get("session_summaries", [])
    anchor           = session_state.get("session_anchor", {})

    # ── theme ─────────────────────────────────────────────────────────────────
    theme      = _extract_theme(topics, summaries)
    confidence = _confidence(session_count, theme, topics)

    # ── emotional direction ───────────────────────────────────────────────────
    direction = _extract_direction(emotional_history)

    # ── active project ────────────────────────────────────────────────────────
    project = _active_project(topics, summaries)

    # ── what changed / stayed ────────────────────────────────────────────────
    changed, stayed = _session_delta(summaries, topics)

    # ── what matters ─────────────────────────────────────────────────────────
    matters = _what_matters(anchor, theme, project, stayed)

    # ── relationship shift ────────────────────────────────────────────────────
    shift = _relationship_shift(emotional_history)

    return IdentityState(
        session_theme       = theme,
        confidence          = confidence,
        emotional_direction = direction,
        active_project      = project,
        relationship_shift  = shift,
        what_changed        = changed,
        what_stayed         = stayed,
        what_matters        = matters,
    )


# ── private helpers ────────────────────────────────────────────────────────────

def _extract_theme(topics: list, summaries: list) -> str:
    all_text = " ".join(topics).lower()
    for text in summaries[-3:]:
        all_text += " " + text.get("summary", "").lower()

    counts = Counter()
    for theme, keywords in _THEME_KEYWORDS.items():
        counts[theme] = sum(all_text.count(k) for k in keywords)

    if not counts or max(counts.values()) == 0:
        return ""
    return counts.most_common(1)[0][0]


def _confidence(session_count: int, theme: str, topics: list) -> float:
    base = min(0.9, session_count / 10.0)
    if theme and any(k in " ".join(topics).lower()
                     for k in _THEME_KEYWORDS.get(theme, [])):
        base += 0.1
    return round(min(1.0, base), 2)


def _extract_direction(emotional_history: list) -> str:
    if not emotional_history:
        return "settling"
    recent = emotional_history[-3:]
    tones  = [e.get("tone", "present") for e in recent]
    for tone in reversed(tones):
        if tone in _TONE_TO_DIRECTION:
            return _TONE_TO_DIRECTION[tone]
    return "settling"


def _active_project(topics: list, summaries: list) -> str:
    all_text = " ".join(topics).lower()
    for s in summaries[-2:]:
        all_text += " " + s.get("summary", "").lower()

    counts = Counter()
    for proj, keywords in _PROJECT_KEYWORDS.items():
        counts[proj] = sum(all_text.count(k) for k in keywords)

    if not counts or max(counts.values()) == 0:
        return ""
    return counts.most_common(1)[0][0]


def _session_delta(summaries: list, current_topics: list) -> tuple:
    if len(summaries) < 2:
        return [], list(set(current_topics))[:3]

    older_text  = " ".join(s.get("summary", "") for s in summaries[-4:-1]).lower()
    recent_text = summaries[-1].get("summary", "").lower() if summaries else ""

    _WATCH = ["clarity", "momentum", "presence", "robot", "book", "os", "game",
              "avatar", "voice", "kickstarter", "prototype", "design", "build",
              "connect", "found", "opened", "decided", "shifted"]

    changed = [w for w in _WATCH if w in recent_text and w not in older_text][:3]
    stayed  = [t for t in current_topics if any(k in t.lower() for k in _WATCH)][:3]

    return changed, stayed


def _what_matters(anchor: dict, theme: str, project: str, stayed: list) -> str:
    summary = anchor.get("current_session_summary", "")
    if summary:
        return summary[:120]
    if project:
        return f"The {project} direction."
    if theme:
        return f"The {theme} thread."
    return ""


def _relationship_shift(emotional_history: list) -> str:
    if len(emotional_history) < 2:
        return "uncertain"
    recent = emotional_history[-1].get("tone", "present")
    prior  = emotional_history[-2].get("tone", "present")
    _OPEN  = {"energised", "present"}
    _CLOSE = {"overwhelmed", "stressed", "low-energy"}
    if prior in _CLOSE and recent in _OPEN:
        return "closer"
    if prior in _OPEN and recent in _CLOSE:
        return "more distant"
    return "same"
