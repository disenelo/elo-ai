"""
memory/summariser.py — experience compression for eLo OS.

Converts raw logs and exchange history into meaning-based summaries.
Does NOT produce transcripts. Produces interpretation.

Output is what this session felt like, not what was said.
"""

from __future__ import annotations
import re


_THEME_MAP = {
    "identity":    [r"\bwho\b", r"\bwhat\s+am\b", r"\bwhat\s+are\b", r"\bwhat\s+is\s+elo\b"],
    "uncertainty": [r"\bdon'?t\s+know\b", r"\bnot\s+sure\b", r"\bconfused\b", r"\bstuck\b"],
    "building":    [r"\bbuild\b", r"\bcreate\b", r"\bdesign\b", r"\bimplement\b"],
    "exploration": [r"\bwhat\s+if\b", r"\bcould\s+we\b", r"\bexplore\b", r"\btry\b"],
    "emotion":     [r"\bfeel\b", r"\btired\b", r"\boverwhel\b", r"\bworried\b", r"\bscared\b"],
    "continuity":  [r"\bremember\b", r"\blast\s+time\b", r"\bcontinue\b", r"\bbefore\b"],
    "system":      [r"\bsystem\b", r"\bmemory\b", r"\bkernel\b", r"\bbackend\b"],
}

_TONE_MAP = {
    "low-energy":  ["tired", "exhaust", "drain", "overwhelm", "stuck", "can't"],
    "positive":    ["excited", "great", "love", "amazing", "happy", "yes"],
    "frustrated":  ["frustrat", "angry", "annoyed", "broken", "fail", "wrong"],
    "constructive":["build", "create", "design", "implement", "add", "make"],
    "exploratory": ["what if", "could", "maybe", "try", "explore", "what about"],
}


def _detect_themes(text: str) -> list:
    t = text.lower()
    return [theme for theme, patterns in _THEME_MAP.items()
            if any(re.search(p, t) for p in patterns)]


def _detect_tone(text: str) -> str:
    t = text.lower()
    for tone, words in _TONE_MAP.items():
        if any(w in t for w in words):
            return tone
    return "neutral"


def compress_session(session_summaries: list) -> str:
    """
    Convert recent exchange history into a meaning-based session summary.

    Returns a single sentence describing what the session felt like.
    Not a transcript — an interpretation.
    """
    if not session_summaries:
        return ""

    user_messages = [s.get("user", "") for s in session_summaries[-10:]]
    all_text      = " ".join(user_messages)

    themes = _detect_themes(all_text)
    tones  = [_detect_tone(m) for m in user_messages if m]

    dominant_tone = max(set(tones), key=tones.count) if tones else "exploratory"
    theme_str     = ", ".join(themes[:3]) if themes else "general conversation"

    return f"User explored {theme_str} with a {dominant_tone} tone."


def compress_obsidian(context_block: str) -> str:
    """Extract named entities from vault context block."""
    if not context_block:
        return ""
    entities = []
    for line in context_block.splitlines():
        if line.startswith("**") and "**:" in line:
            name = line.split("**")[1]
            if name:
                entities.append(name)
    return ", ".join(entities[:8]) if entities else ""


def emotional_summary(emotional_history: list) -> str:
    """
    Summarise emotional history into a single descriptive phrase.
    Used for the emotional_summary field in memory_pack.
    """
    if not emotional_history:
        return "neutral"
    recent  = emotional_history[-10:]
    counts: dict = {}
    for h in recent:
        tone = h.get("tone", "neutral")
        counts[tone] = counts.get(tone, 0) + 1
    dominant  = max(counts, key=counts.get)
    last_tone = recent[-1].get("tone", "neutral") if recent else "neutral"
    if dominant == last_tone:
        return f"consistently {dominant}"
    return f"{dominant} overall, recently shifting to {last_tone}"
