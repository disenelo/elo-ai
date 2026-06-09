"""
memory/state_manager.py — Persistent session state for eLo OS.

Manages elo_state.json — the only source of long-term continuity.
Loaded at startup, updated after every response.
"""

import json
import os
import re
from datetime import datetime

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "elo_state.json")

_DEFAULT_STATE = {
    "user_info": {
        "name": "",
        "known_since": ""
    },
    "session_count":    0,
    "last_active":      "",
    "identity_anchor":  "eLo is a stable, grounded conversational presence in the DISENELO world.",
    "emotional_history": [],
    "last_topics":      [],
    "session_summaries": [],
    "session_anchor": {
        "current_session_summary":  "",
        "emotional_tone_signature": "neutral",
        "open_loops":               [],
        "resolved_loops":           []
    },
    # continuity fields — updated every turn, persisted across sessions
    "emotion":       "neutral",     # current emotional state string
    "last_intent":   "conversation", # last classified intent
    "loop_counter":  0,             # increments on repetition/confusion signals
}


def load() -> dict:
    """Load state from disk. Returns default state if file missing or corrupt."""
    if not os.path.exists(_STATE_PATH):
        return dict(_DEFAULT_STATE)
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
        # ensure all default keys exist
        for k, v in _DEFAULT_STATE.items():
            if k not in state:
                state[k] = v
        return state
    except Exception:
        return dict(_DEFAULT_STATE)


def save(state: dict):
    """Write state to disk. Silently fails — never crashes the main loop."""
    try:
        with open(_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def update(
    state:       dict,
    user_input:  str,
    response:    str,
    intent:      str = "",
    loop_signal: bool = False,
) -> dict:
    """
    Update state after one exchange.
    Appends topics, emotional tone, session summary, and timestamp.

    Args:
        state:       Current state dict.
        user_input:  Raw user message.
        response:    eLo response text.
        intent:      Classified intent from attention layer (optional).
        loop_signal: True if a repetition/confusion signal was detected.
    """
    state = dict(state)
    state["last_active"] = datetime.now().isoformat()

    # extract simple topics (meaningful words)
    _STOPWORDS = {"the","a","an","is","it","in","on","at","to","of","and",
                  "or","but","i","my","me","this","that","for","with","be"}
    words = [w.lower() for w in re.findall(r"\b\w{4,}\b", user_input)
             if w.lower() not in _STOPWORDS]
    if words:
        topics = list(state.get("last_topics", []))
        topics = (topics + words[:3])[-10:]
        state["last_topics"] = topics

    # emotional tone detection
    text = user_input.lower()
    if any(w in text for w in ["tired","exhaust","drain","stuck","overwhelm"]):
        tone = "low-energy"
    elif any(w in text for w in ["excited","great","love","amazing","happy"]):
        tone = "positive"
    elif any(w in text for w in ["frustrat","angry","annoyed","broken","fail"]):
        tone = "frustrated"
    else:
        tone = "neutral"

    history = list(state.get("emotional_history", []))
    history.append({"timestamp": state["last_active"], "tone": tone})
    state["emotional_history"] = history[-20:]

    # persist current emotion snapshot and last intent
    state["emotion"]     = tone
    state["last_intent"] = intent or _classify_intent(text)

    # loop counter — increments on signals, decays on clean turns
    lc = state.get("loop_counter", 0)
    state["loop_counter"] = (lc + 1) if loop_signal else max(0, lc - 1)

    # compact session summary
    summaries = list(state.get("session_summaries", []))
    summaries.append({
        "timestamp": state["last_active"],
        "user":      user_input[:100],
        "elo":       response[:100],
    })
    state["session_summaries"] = summaries[-20:]

    return state


def _classify_intent(text: str) -> str:
    """Lightweight intent classifier for state persistence."""
    if any(w in text for w in ["build", "create", "design", "make"]):
        return "creation"
    if any(w in text for w in ["why", "what", "how", "explain"]):
        return "inquiry"
    if any(w in text for w in ["sad", "tired", "confused", "overwhelmed", "feel"]):
        return "emotional"
    return "conversation"


def as_context_string(state: dict) -> str:
    """Format state as a compact string for prompt injection."""
    lines = []

    anchor = state.get("session_anchor", {})
    if anchor.get("current_session_summary"):
        lines.append(f"Ongoing thread: {anchor['current_session_summary']}")
    if anchor.get("emotional_tone_signature") and anchor["emotional_tone_signature"] != "neutral":
        lines.append(f"Emotional carry: {anchor['emotional_tone_signature']}")

    if state.get("last_topics"):
        lines.append(f"Recent topics: {', '.join(state['last_topics'][-5:])}")

    if state.get("emotional_history"):
        recent_tone = state["emotional_history"][-1].get("tone", "neutral")
        lines.append(f"Recent tone: {recent_tone}")

    if state.get("session_summaries"):
        last = state["session_summaries"][-1]
        lines.append(f"Last exchange: '{last['user'][:60]}'")

    if state.get("last_active"):
        lines.append(f"Last active: {state['last_active'][:16]}")

    return "\n".join(lines)


def increment_session(state: dict) -> dict:
    state = dict(state)
    state["session_count"] = state.get("session_count", 0) + 1
    state["last_active"]   = datetime.now().isoformat()
    state["loop_counter"]  = 0   # reset loop counter on new session
    if "session_anchor" not in state:
        state["session_anchor"] = dict(_DEFAULT_STATE["session_anchor"])
    return state


# Public alias — matches the function name used in the prompt_builder sketch
load_state = load


def close_session(state: dict) -> dict:
    """
    Compress the current session into a meaning-based anchor.
    Called on /exit — updates session_anchor with what this session meant,
    not what was literally said.
    """
    state = dict(state)
    summaries = state.get("session_summaries", [])
    emotional_history = state.get("emotional_history", [])

    # derive emotional tone signature
    if emotional_history:
        recent = [h.get("tone", "neutral") for h in emotional_history[-10:]]
        counts: dict = {}
        for t in recent:
            counts[t] = counts.get(t, 0) + 1
        dominant = max(counts, key=counts.get)
        last_tone = recent[-1] if recent else "neutral"
        sig = dominant if dominant == last_tone else f"{dominant}, shifting to {last_tone}"
    else:
        sig = "neutral"

    # derive session meaning
    if summaries:
        user_texts = " ".join(s.get("user", "") for s in summaries[-10:]).lower()
        themes = []
        _THEME_MAP = {
            "building":    ["build", "create", "design", "implement", "add"],
            "exploration": ["what if", "could we", "try", "explore"],
            "uncertainty": ["don't know", "not sure", "confused", "stuck"],
            "emotion":     ["feel", "tired", "overwhelm", "worried"],
            "identity":    ["who", "what are you", "what is elo"],
            "system":      ["memory", "kernel", "backend", "system"],
        }
        for theme, words in _THEME_MAP.items():
            if any(w in user_texts for w in words):
                themes.append(theme)
        theme_str = ", ".join(themes[:3]) if themes else "general conversation"
        session_summary = f"User explored {theme_str} with a {sig} tone."
    else:
        session_summary = ""

    anchor = dict(state.get("session_anchor", _DEFAULT_STATE["session_anchor"]))
    anchor["current_session_summary"]  = session_summary
    anchor["emotional_tone_signature"] = sig
    state["session_anchor"] = anchor
    return state
