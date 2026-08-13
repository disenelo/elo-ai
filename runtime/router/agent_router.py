"""
runtime/router/agent_router.py — Stage 05: Agent Selection

Select which agent(s) to call based on intent and cleaned input.
Max 2 agents. Priority: reason → memory → tool → system.

Output: [(agent_name, query), ...]
"""
from __future__ import annotations
import re

# ── Intent → agent mapping ────────────────────────────────────────────────────
# Each intent maps to one primary agent. Chain intents map to two.

_INTENT_AGENT: dict[str, str] = {
    "memory":              "obsidian",
    "system":              "system",
    "utility_timer":       "timer",
    "utility_reminder":    "reminders",
    "utility_weather":     "weather",
    "utility_time":        "time",
    "utility_calendar":    "calendar",
    "utility_spotify":     "spotify",
    "utility_messages":    "messages",
    "utility_clipboard":   "clipboard",
    "utility_notes":       "notes",
    "utility_news":        "news",
    "utility_translate":   "translate",
    "utility_calculator":  "calculator",
    "utility_github":      "github",
    "utility_vision":      "vision",
    "file_read":           "file_read",
    "file_ops":            "system",
    "vault_write":         "vault_write",
    "draft":               "draft",
    "lookup":              "search",
    "social":              None,       # no agent — conversation only
    "planning":            None,       # reasoning only
    "creation":            None,       # reasoning only
    "conversation":        None,       # no agent
}

# ── Chain intent → two agents ─────────────────────────────────────────────────
_CHAIN_AGENTS: dict[str, list[str]] = {
    "file_read_or_obsidian": ["obsidian", "draft"],
    "memory":                ["obsidian", "file_read"],
}


def _extract_query(intent: str, cleaned: str) -> str:
    """
    Extract the relevant query string for the selected agent.
    Strips intent-trigger words to leave just the subject.
    """
    t = cleaned.strip()

    # Strip leading action verbs for cleaner agent queries
    _STRIP_PREFIXES = [
        r"^(?:can\s+you\s+)?(?:play|search|find|look\s+up|translate|open|launch|set|turn|remind\s+me\s+to)\s+",
        r"^(?:what(?:'s|\s+is)\s+(?:the\s+)?)",
        r"^(?:tell\s+me\s+(?:about\s+)?)",
        r"^(?:help\s+me\s+(?:with\s+)?)",
        r"^(?:check|read|show|list)\s+",
    ]
    for p in _STRIP_PREFIXES:
        t = re.sub(p, "", t, flags=re.IGNORECASE).strip()

    return t or cleaned


def route(intent: str, cleaned: str, chain: list[str] | None = None) -> list[tuple[str, str]]:
    """
    Stage 05 — select agents from intent.

    Returns:
        List of (agent_name, query) tuples — max 2 entries.
        Empty list = conversation only, no agent needed.
    """
    query = _extract_query(intent, cleaned)

    # Multi-agent chain
    if chain:
        agents_out = []
        for ch_intent in chain[:2]:
            agent = _INTENT_AGENT.get(ch_intent) or _CHAIN_AGENTS.get(ch_intent, [None])[0]
            if agent:
                agents_out.append((agent, query))
        return agents_out

    # Single agent
    agent = _INTENT_AGENT.get(intent)
    if agent is None:
        return []
    return [(agent, query)]


def is_conversation_only(intent: str) -> bool:
    """True if this intent needs no tool — pure eLo response."""
    return _INTENT_AGENT.get(intent) is None
