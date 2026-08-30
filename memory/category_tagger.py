"""
memory/category_tagger.py — WO-MEMORY-TURN-TYPES

Turn-type → memory category mapping for the 10 canonical categories (David L3 ruling 2026-08-30).

Called by spine.py's assemble_cognitive_state() to populate CognitiveState.memory_categories.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.contracts import CognitiveState


def tag_turn(
    turn: str,
    intent_output: dict | None = None,
    cognitive_state: "CognitiveState | None" = None,
) -> list[str]:
    """
    Return the list of canonical memory categories applicable to this turn.

    Uses the signals in turn text + intent_output. cognitive_state is accepted
    for future extension (significance gating, relationship context) but is not
    required — text-only tagging is the baseline.

    The 10 canonical categories (David L3 ruling 2026-08-30):
        identity · relationship · preferences · plans · commitments
        projects · decisions · experiences · contextual_state · learning
    """
    from core.memory_engine import _classify_memory_categories

    # Combine turn text with any enriched context from intent_output
    text = turn
    if intent_output and isinstance(intent_output, dict):
        enriched = intent_output.get("enriched_context", "") or ""
        if enriched:
            text = turn + " " + enriched

    categories = _classify_memory_categories(text)

    # Filter to only the 10 canonical categories — legacy keys (creative, world, user) excluded
    _CANONICAL = frozenset({
        "identity", "relationship", "preferences", "plans", "commitments",
        "projects", "decisions", "experiences", "contextual_state", "learning",
    })
    return [c for c in categories if c in _CANONICAL]
