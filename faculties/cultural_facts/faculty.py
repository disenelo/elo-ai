"""
faculties/cultural_facts/faculty.py — Cultural Facts Faculty for eLo OS.

Architecture position:
    Faculty → Brain → ambient_thought() / triggered path → voice

This faculty draws curated historical facts from facts.json using weighted
group selection. The Brain decides when and how to surface them. No LLM
generation of facts — all content is pre-verified and pre-written in eLo's voice.

Delivery:
    - Ambient path: fact.fact (reference text) passed to Brain as context.
                    Brain wraps it in the moment. May choose not to use it.
    - Triggered path: fact.delivery spoken directly to TTS. No LLM needed.

Weight rules:
    - Standard draw: GROUP_WEIGHTS below.
    - Folklore / witchcraft categories: FOLKLORE_WEIGHTS — European proportion rises,
      African / indigenous spiritual traditions included.
    - Session dedup: last 25 drawn IDs skipped to avoid repeats.
"""
from __future__ import annotations

import json
import os
import random
from typing import Optional

from faculties.cultural_facts.models import CulturalFact

_FACTS_PATH = os.path.join(os.path.dirname(__file__), "facts.json")

# ── Group weights (standard draw) ────────────────────────────────────────────
# 90 / 10 split. Black / African civilisations weighted heaviest as primary history.

GROUP_WEIGHTS: dict[str, int] = {
    "black_african":         52,
    "moorish_north_african": 12,
    "arab_middle_eastern":    8,
    "asian":                 10,
    "south_asian":            6,
    "indigenous":             7,
    "european":               5,
}

# ── Folklore / witchcraft exception weights ───────────────────────────────────
# European and indigenous spiritual traditions have deep folklore density.

FOLKLORE_WEIGHTS: dict[str, int] = {
    "black_african":         25,
    "moorish_north_african":  8,
    "arab_middle_eastern":    5,
    "asian":                  8,
    "south_asian":            5,
    "indigenous":            24,
    "european":              25,
}

_FOLKLORE_CATEGORIES = {"folklore", "witchcraft"}

# ── Session dedup ─────────────────────────────────────────────────────────────
_session_drawn: list[str] = []
_DEDUP_WINDOW = 25


# ── Core draw ─────────────────────────────────────────────────────────────────

def _load_facts() -> list[CulturalFact]:
    """Load and parse facts.json. Reloads on every draw — David can add entries live."""
    try:
        with open(_FACTS_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        return [CulturalFact(**entry) for entry in raw]
    except Exception as e:
        import sys
        print(f"[cultural_facts] _load_facts error: {e}", file=sys.stderr)
        return []


def draw(category_hint: str = "") -> Optional[CulturalFact]:
    """
    Draw one fact respecting group weights and session dedup.

    Args:
        category_hint — if provided and matches a category, bias toward it.
                        Pass 'folklore' or 'witchcraft' to use FOLKLORE_WEIGHTS.

    Returns:
        CulturalFact or None if the library is empty or all facts exhausted.
    """
    facts = _load_facts()
    if not facts:
        return None

    # Choose weight table
    weights = FOLKLORE_WEIGHTS if category_hint in _FOLKLORE_CATEGORIES else GROUP_WEIGHTS

    # Filter out recently drawn
    available = [f for f in facts if f.id not in _session_drawn[-_DEDUP_WINDOW:]]
    if not available:
        # All facts seen — reset dedup and try again
        _session_drawn.clear()
        available = facts

    # Group-weighted draw
    groups = list(weights.keys())
    group_wts = list(weights.values())
    chosen_group = random.choices(groups, weights=group_wts, k=1)[0]

    pool = [f for f in available if f.group == chosen_group]
    if not pool:
        # Chosen group has no facts yet — fall back to any available
        pool = available
    if not pool:
        return None

    fact = random.choice(pool)
    _session_drawn.append(fact.id)
    return fact


# ── Trigger detection ─────────────────────────────────────────────────────────

_TRIGGERS = (
    "tell me a fact",
    "drop a fact",
    "give me a fact",
    "random fact",
    "fun fact",
    "drop some knowledge",
    "educate me",
    "say something real",
    "drop something",
    "tell me something random",
    "something random",
    "give me something random",
    "tell me something real",
    "give me something real",
    "who made",
    "who invented",
    "who built",
    "who discovered",
    "what's a fact",
    "give me history",
    "black history",
    "real history",
    "teach me something",
    "hit me with something",
)


def is_fact_trigger(text: str) -> bool:
    """Return True if the message is a direct fact request."""
    lowered = text.lower()
    return any(t in lowered for t in _TRIGGERS)


# ── Status ────────────────────────────────────────────────────────────────────

def status() -> str:
    """Quick stats for debug/memory-status reports."""
    facts = _load_facts()
    groups = {}
    for f in facts:
        groups[f.group] = groups.get(f.group, 0) + 1
    breakdown = ", ".join(f"{g}: {n}" for g, n in sorted(groups.items()))
    return f"Cultural facts: {len(facts)} entries. {breakdown}. {len(_session_drawn)} drawn this session."


# ── Module-level singleton draw ───────────────────────────────────────────────
# Use draw() and is_fact_trigger() directly — no class instantiation needed.
