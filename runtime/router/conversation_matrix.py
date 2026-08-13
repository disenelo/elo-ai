"""
runtime/router/conversation_matrix.py — Stage 03: Conversational Context

Connect current input to session history, detect hidden goals and continuity.
Never overwrites — adds to the understanding.

Output: {direct_request, hidden_goal, references, continuity}
"""
from __future__ import annotations
import re

# ── Session window — last N turns in memory ───────────────────────────────────
_SESSION_WINDOW: list[dict] = []
_MAX_WINDOW = 12

# ── Active project/entity tracking ───────────────────────────────────────────
_active_project: str = ""
_active_entity:  str = ""
_last_agent:     str = ""
_last_action:    str = ""

# ── Temporal reference patterns ───────────────────────────────────────────────
_TEMPORAL_BACK = re.compile(
    r"\b(earlier|before|last\s+time|yesterday|a\s+moment\s+ago|"
    r"what\s+(?:i|we)\s+(?:said|did|were\s+doing)|from\s+before)\b",
    re.IGNORECASE
)

# ── Continuity markers — user is extending a previous thread ─────────────────
_CONTINUITY_MARKERS = re.compile(
    r"^\s*(?:and|also|now|then|but|what\s+about|on\s+that|following\s+that|"
    r"going\s+back\s+to|back\s+to\s+the)\b",
    re.IGNORECASE
)

# ── Hidden goal map — surface phrasing → underlying intent ───────────────────
_HIDDEN_GOALS = [
    (r"\bi\s+should\s+(?:work|get\s+going|start)", "progress"),
    (r"\bi\s+(?:can't|cannot|don't\s+know)\s+how\s+to", "guidance"),
    (r"\bmaybe\s+i\s+(?:should|need\s+to)", "uncertainty"),
    (r"\bam\s+i\s+(?:doing\s+this\s+right|on\s+the\s+right\s+track)", "validation"),
    (r"\bi(?:'m|\s+am)\s+(?:stuck|blocked|not\s+sure)", "unblocking"),
    (r"\bi(?:'m|\s+am)\s+(?:tired|exhausted|done)", "rest"),
    (r"\bthis\s+(?:is\s+(?:hard|difficult|taking\s+forever)|isn(?:'t|\s+not)\s+working)", "frustration"),
    (r"\bwhat(?:'s|\s+is)\s+(?:the\s+)?(?:point|use)", "doubt"),
]

# ── Pronoun reference — "it", "that", "this" map to last entity ──────────────
_PRONOUN_RE = re.compile(r"\b(it|that|this|them|those|these)\b", re.IGNORECASE)


def push(user_input: str, elo_response: str = "") -> None:
    """Record a completed turn into the session window."""
    global _SESSION_WINDOW
    _SESSION_WINDOW.append({"user": user_input, "elo": elo_response})
    if len(_SESSION_WINDOW) > _MAX_WINDOW:
        _SESSION_WINDOW.pop(0)


def set_active(project: str = "", entity: str = "", agent: str = "", action: str = "") -> None:
    """Update tracking state after a successful turn."""
    global _active_project, _active_entity, _last_agent, _last_action
    if project: _active_project = project
    if entity:  _active_entity  = entity
    if agent:   _last_agent     = agent
    if action:  _last_action    = action


def _resolve_pronouns(text: str) -> str:
    """Replace bare pronouns with the last known entity if present."""
    if not _active_entity:
        return text
    if _PRONOUN_RE.search(text) and _active_entity:
        return _PRONOUN_RE.sub(_active_entity, text)
    return text


def _recent_context() -> str:
    """Return a short string summarising what was happening recently."""
    if not _SESSION_WINDOW:
        return ""
    recent = _SESSION_WINDOW[-3:]
    parts = [f"user said: '{t['user']}'" for t in recent if t.get("user")]
    return " | ".join(parts)


def analyse(user_input: str, session: dict | None = None, memory: dict | None = None) -> dict:
    """
    Stage 03 — build conversational context matrix.

    Returns:
        direct_request  — what was literally asked
        hidden_goal     — underlying intent if different ("progress", "validation" etc.)
        references      — list of what this input references (project, entity, previous turn)
        continuity      — True if input continues a previous thread
        resolved_input  — input with pronouns resolved to entities
    """
    t = user_input.strip()
    tl = t.lower()

    # Resolve pronoun references
    resolved = _resolve_pronouns(t)

    # Detect continuity
    continuity = bool(_CONTINUITY_MARKERS.match(tl)) or bool(_TEMPORAL_BACK.search(tl))

    # Detect hidden goal
    hidden_goal = ""
    for pattern, goal in _HIDDEN_GOALS:
        if re.search(pattern, tl, re.IGNORECASE):
            hidden_goal = goal
            break

    # Build references list
    references: list[str] = []
    if _active_project:
        references.append(f"project:{_active_project}")
    if _active_entity and _PRONOUN_RE.search(tl):
        references.append(f"entity:{_active_entity}")
    if continuity and _last_action:
        references.append(f"previous:{_last_action}")
    if _TEMPORAL_BACK.search(tl):
        references.append("memory:session")

    return {
        "direct_request": t,
        "hidden_goal":    hidden_goal,
        "references":     references,
        "continuity":     continuity,
        "resolved_input": resolved,
        "recent_context": _recent_context() if continuity else "",
    }


def get_window() -> list[dict]:
    """Return current session window (read-only view)."""
    return list(_SESSION_WINDOW)
