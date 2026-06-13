"""
core/continuity.py — Phase B: RELATIONSHIP → CONTINUITY.

eLo develops stable internal structure across sessions.

Exposes:
    get_viewpoint(question) → str | None
    get_entity_why(name)    → str | None
    cross_session_delta(state) → str | None
    update_from_session(pattern_log, identity_map_path)

Questions eLo can now answer:
    Why does Chunk matter?
    Why does the robot exist?
    What is eLo becoming?
    What changed since last week?
"""

from __future__ import annotations
import json
import os
import re
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_WORLD_GRAPH_PATH  = os.path.join(_ROOT, "identity", "world_graph.json")
_VIEWPOINTS_PATH   = os.path.join(_ROOT, "identity", "viewpoints.json")
_IDENTITY_MAP_PATH = os.path.join(_ROOT, "identity", "identity_map.json")

# ── lazy-loaded caches ────────────────────────────────────────────────────────

_world_graph: dict  = {}
_viewpoints:  dict  = {}
_identity_map: dict = {}
_loaded: bool       = False


def _load() -> None:
    global _world_graph, _viewpoints, _identity_map, _loaded
    if _loaded:
        return
    try:
        with open(_WORLD_GRAPH_PATH)  as f: _world_graph  = json.load(f)
    except Exception: pass
    try:
        with open(_VIEWPOINTS_PATH)   as f: _viewpoints   = json.load(f)
    except Exception: pass
    try:
        with open(_IDENTITY_MAP_PATH) as f: _identity_map = json.load(f)
    except Exception: pass
    _loaded = True


# ── keyword → viewpoint key mapping ──────────────────────────────────────────

_VIEWPOINT_TRIGGERS: dict[str, str] = {
    # question fragments → viewpoint key
    "chunk":      "chunk",
    "robot":      "robot",
    "becoming":   "elo_becoming",
    "what is elo": "what_elo_is",
    "converge":   "convergence",
    "together":   "convergence",
    "connect":    "convergence",
    "calm":       "calm_is_the_action",
    "kickstart":  "kickstarter",
    "disenelo":   "disenelo_mission",
    "free":       "disenelo_mission",
}

_ENTITY_TRIGGERS: dict[str, str] = {
    "chunk":    "Chunk",
    "robot":    "robot",
    "elo-os":   "eLo-OS",
    "elo os":   "eLo-OS",
    "elo-planet": "eLo-Planet",
    "game":     "eLo-Planet",
    "book":     "book",
    "k-7":      "K-7",
    "k7":       "K-7",
    "disenelo": "DISENELO",
}


def get_viewpoint(question: str) -> Optional[str]:
    """Return eLo's viewpoint relevant to the question, or None."""
    _load()
    t = question.lower()
    for trigger, key in _VIEWPOINT_TRIGGERS.items():
        if trigger in t:
            return _viewpoints.get(key)
    return None


def get_entity_why(question: str) -> Optional[str]:
    """Answer 'why does X matter?' from world_graph entities."""
    _load()
    t = question.lower()
    for trigger, entity_key in _ENTITY_TRIGGERS.items():
        if trigger in t:
            entities = _world_graph.get("entities", {})
            entity   = entities.get(entity_key, {})
            why      = entity.get("why")
            if why:
                return why
    return None


def cross_session_delta(state: dict) -> Optional[str]:
    """
    Synthesise what changed across recent sessions.
    Used to answer: 'What changed since last week?'
    """
    _load()
    summaries = state.get("session_summaries", [])
    if len(summaries) < 2:
        return None

    # take last 3 summaries and surface the most recent shift
    recent = summaries[-3:]

    # look for topic words that appeared in newer but not older summaries
    older_text = " ".join(s.get("summary", "") for s in recent[:-1]).lower()
    newer_text = recent[-1].get("summary", "").lower()

    if not newer_text:
        return None

    _SHIFT_KEYWORDS = ["avatar", "robot", "book", "continuity", "presence", "desktop",
                       "blender", "scene", "found", "opened", "started", "finished"]

    new_topics = [w for w in _SHIFT_KEYWORDS if w in newer_text and w not in older_text]
    if new_topics:
        topic = new_topics[0]
        return f"Last time the conversation moved toward {topic}."

    return None


def context_block() -> str:
    """
    Build a short continuity context string for prompt injection.
    Returns key viewpoints relevant to current OS state.
    """
    _load()
    # always include the convergence viewpoint — it's the through-line
    lines = []
    convergence = _viewpoints.get("convergence", "")
    if convergence:
        lines.append(convergence)
    becoming = _viewpoints.get("elo_becoming", "")
    if becoming:
        lines.append(becoming)
    return " ".join(lines)


def update_from_session(pattern_log: list) -> None:
    """
    Called at session end. Persists observed patterns to identity_map.json.
    """
    _load()
    if not pattern_log:
        return

    try:
        imap = dict(_identity_map)
        plog = imap.get("pattern_log", [])
        plog.extend(pattern_log)
        imap["pattern_log"] = plog[-50:]  # keep last 50 observations
        imap["sessions_since_update"] = imap.get("sessions_since_update", 0) + 1

        # update about_user from log tone data
        about = imap.get("about_user", {})
        open_topics  = [e["topic"] for e in pattern_log if e.get("tone") == "open"]
        tight_topics = [e["topic"] for e in pattern_log if e.get("tone") == "tight"]
        recurring    = list({e["topic"] for e in pattern_log})

        if open_topics:
            existing = about.get("opens_up_on", [])
            about["opens_up_on"] = list(set(existing + open_topics))[-10:]
        if tight_topics:
            existing = about.get("tightens_on", [])
            about["tightens_on"] = list(set(existing + tight_topics))[-10:]
        if recurring:
            existing = about.get("keeps_returning_to", [])
            about["keeps_returning_to"] = list(set(existing + recurring))[-10:]

        imap["about_user"] = about
        _identity_map.update(imap)

        with open(_IDENTITY_MAP_PATH, "w") as f:
            json.dump(imap, f, indent=2)
    except Exception:
        pass
