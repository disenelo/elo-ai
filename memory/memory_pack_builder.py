"""
memory/memory_pack_builder.py — merge obsidian vault + state + recent chat into memory_pack.json.

Output is under 2,000 tokens equivalent.
Does NOT include raw logs or full conversation history.
Only meaning, identity continuity, emotional tone, and project relationships.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from memory.summariser import compress_session, compress_obsidian, emotional_summary
from memory.obsidian_loader import get_context_block

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "elo_state.json")
_PACK_PATH  = os.path.join(_ROOT, "memory", "memory_pack.json")


def _load_state() -> dict:
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def build(state: dict = None, max_chars: int = 2000) -> dict:
    """
    Build a compressed memory pack from all available sources.

    Args:
        state:     Pre-loaded state dict. Loads from disk if None.
        max_chars: Rough character budget for the pack.

    Returns:
        memory_pack dict with: identity, entities, projects,
        user_patterns, recent_context, emotional_summary.
    """
    if state is None:
        state = _load_state()

    vault_ctx    = get_context_block(max_chars=800)
    session_sum  = compress_session(state.get("session_summaries", []))
    entity_str   = compress_obsidian(vault_ctx)
    emo_sum      = emotional_summary(state.get("emotional_history", []))

    # identity: session anchor wins, else session compression
    anchor   = state.get("session_anchor", {})
    identity = (anchor.get("current_session_summary") or session_sum)[:300]

    # entities: from vault
    entities = [e.strip() for e in entity_str.split(",")] if entity_str else []

    # projects: last meaningful topics from state
    projects = list(state.get("last_topics", []))[-5:]

    # user patterns: distinct emotional tones seen
    tones        = [h.get("tone", "neutral") for h in state.get("emotional_history", [])[-20:]]
    user_patterns = list(dict.fromkeys(tones))[:6]  # dedupe, preserve order

    # recent context: last 5 exchanges, stripped to meaning
    recent: list = []
    for s in state.get("session_summaries", [])[-5:]:
        recent.append({
            "user": s.get("user", "")[:60],
            "elo":  s.get("elo",  "")[:60],
        })

    # high_priority — pre-selected items always relevant to any turn.
    # Used directly by filter_memory() without needing the full attention layer.
    high_priority: list = []
    if identity:
        high_priority.append(identity)
    if anchor.get("emotional_tone_signature") and anchor["emotional_tone_signature"] != "neutral":
        high_priority.append(f"Emotional carry: {anchor['emotional_tone_signature']}")
    if recent:
        last_exchange = recent[-1]
        ex_text = f"{last_exchange.get('user', '')} → {last_exchange.get('elo', '')}".strip()
        if ex_text and ex_text != "→":
            high_priority.append(ex_text)

    pack = {
        "generated":        datetime.now().isoformat(),
        "identity":         identity,
        "entities":         entities[:10],
        "projects":         projects,
        "user_patterns":    user_patterns,
        "recent_context":   recent,
        "emotional_summary": emo_sum,
        "high_priority":    high_priority[:5],   # pre-ranked — used by filter_memory()
    }

    try:
        with open(_PACK_PATH, "w", encoding="utf-8") as f:
            json.dump(pack, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return pack


def load() -> dict:
    """Load the most recent memory pack from disk."""
    try:
        with open(_PACK_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


if __name__ == "__main__":
    pack = build()
    print(json.dumps(pack, indent=2))
