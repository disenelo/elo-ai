"""
runtime/self_knowledge.py — eLo's self-model: what it can and cannot do.

Answers from the 315 questions:
  "a system capable of knowing what he can currently do?"
  "a system capable of knowing what he cannot currently do?"
  "a system capable of knowing what his current embodiment can do?"
  "a system that knows what tools it has?"
  "a system that knows what tools it does not have?"
  "a system capable of identifying when its self-model is incomplete?"

Reads the capability registry at runtime — not a snapshot, not a description.
The self-model is always current: if a capability is removed from the registry,
it disappears from eLo's self-knowledge automatically.

This module does NOT make decisions. It provides a queryable self-model.
The Executive decides what to do with it.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

_log = logging.getLogger(__name__)

_EMBODIMENT_TERMINAL = "terminal"
_EMBODIMENT_DESKTOP  = "desktop"
_EMBODIMENT_MOBILE   = "mobile"
_EMBODIMENT_ROBOT    = "robot"

_KNOWN_EMBODIMENTS = {
    _EMBODIMENT_TERMINAL, _EMBODIMENT_DESKTOP,
    _EMBODIMENT_MOBILE,   _EMBODIMENT_ROBOT,
}

# The registry uses "desktop" as the canonical identifier for the Mac/terminal
# runtime. "terminal" is an eLo-OS alias that maps to the same embodiment.
_EMBODIMENT_ALIAS: dict[str, str] = {
    _EMBODIMENT_TERMINAL: _EMBODIMENT_DESKTOP,
}


# ── Schema ────────────────────────────────────────────────────────────────────

@dataclass
class CapabilitySnapshot:
    id:          str
    display_name: str
    description: str
    category:    str
    available:   bool   = True   # False = future=True, not yet built
    embodiments: list   = None   # which embodiments can use it

    def __post_init__(self):
        if self.embodiments is None:
            self.embodiments = ["desktop"]


@dataclass
class SelfKnowledge:
    embodiment:   str
    can_do:       list[CapabilitySnapshot]
    cannot_do:    list[CapabilitySnapshot]
    not_on_body:  list[CapabilitySnapshot]  # built but not available on this embodiment

    @property
    def can_do_ids(self) -> set[str]:
        return {c.id for c in self.can_do}

    @property
    def cannot_do_ids(self) -> set[str]:
        return {c.id for c in self.cannot_do}

    def gap_for_goal(self, goal_text: str) -> list[CapabilitySnapshot]:
        """
        Given a goal described in plain text, return capabilities that would help
        but are currently unavailable (future=True or not on this body).
        """
        goal_lower = goal_text.lower()
        gaps: list[CapabilitySnapshot] = []
        for cap in self.cannot_do + self.not_on_body:
            if (cap.description.lower() in goal_lower
                    or any(w in goal_lower for w in cap.display_name.lower().split())):
                gaps.append(cap)
        return gaps

    def knows_it_cannot(self, capability_id: str) -> bool:
        """eLo explicitly knows it cannot currently do this."""
        return capability_id in self.cannot_do_ids

    def is_self_model_complete(self) -> bool:
        """
        Returns True if the self-model accounts for every registered capability.
        A complete self-model means can_do + cannot_do + not_on_body covers everything.
        """
        all_ids = self.can_do_ids | self.cannot_do_ids | {c.id for c in self.not_on_body}
        try:
            from runtime.capabilities.registry import ALL_CAPABILITIES
            return all(c.id in all_ids for c in ALL_CAPABILITIES)
        except Exception:
            return False


# ── Builder ───────────────────────────────────────────────────────────────────

def build_self_knowledge(embodiment: str = _EMBODIMENT_TERMINAL) -> SelfKnowledge:
    """
    Build eLo's current self-model for the given embodiment.

    can_do:      enabled, not future=True, supports this embodiment
    not_on_body: enabled, not future=True, but not supported on this embodiment
    cannot_do:   future=True — built in the registry but not yet implemented

    "terminal" is aliased to "desktop" — the registry's canonical identifier for
    the Mac/terminal runtime.
    """
    try:
        from runtime.capabilities.registry import ALL_CAPABILITIES
    except Exception as exc:
        _log.error("self_knowledge: cannot load registry: %s", exc)
        return SelfKnowledge(embodiment=embodiment, can_do=[], cannot_do=[], not_on_body=[])

    # Map external alias → registry canonical identifier
    registry_embodiment = _EMBODIMENT_ALIAS.get(embodiment, embodiment)

    can_do:      list[CapabilitySnapshot] = []
    cannot_do:   list[CapabilitySnapshot] = []
    not_on_body: list[CapabilitySnapshot] = []

    for cap in ALL_CAPABILITIES:
        snap = CapabilitySnapshot(
            id=cap.id,
            display_name=cap.display_name,
            description=cap.description,
            category=cap.category,
            available=not cap.future,
            embodiments=list(cap.embodiment_scope),
        )

        if cap.future:
            # Not yet built — eLo cannot do this regardless of embodiment
            cannot_do.append(snap)
        elif registry_embodiment in cap.embodiment_scope or not cap.embodiment_scope:
            # Built and available on this embodiment
            can_do.append(snap)
        else:
            # Built but not available on this body
            not_on_body.append(snap)

    return SelfKnowledge(
        embodiment=embodiment,
        can_do=can_do,
        cannot_do=cannot_do,
        not_on_body=not_on_body,
    )


# ── Prompt block ──────────────────────────────────────────────────────────────

def self_knowledge_block(embodiment: str = _EMBODIMENT_TERMINAL) -> str:
    """
    Build a compact prompt block describing eLo's current capability self-model.

    Lists what eLo CAN do on the current body (by category), and acknowledges
    what it explicitly CANNOT yet do — so it never pretends to have a capability
    it lacks.

    Returns "" on failure (never blocks the turn).
    """
    try:
        sk = build_self_knowledge(embodiment)
        if not sk.can_do and not sk.cannot_do:
            return ""

        lines = [f"[SELF-KNOWLEDGE — capabilities on embodiment: {embodiment}]"]

        # Group can_do by category
        by_cat: dict[str, list[str]] = {}
        for c in sk.can_do:
            by_cat.setdefault(c.category, []).append(c.display_name)

        lines.append("CAN DO NOW:")
        for cat, names in sorted(by_cat.items()):
            lines.append(f"  {cat}: {', '.join(names)}")

        if sk.cannot_do:
            not_yet = [c.display_name for c in sk.cannot_do[:8]]
            if len(sk.cannot_do) > 8:
                not_yet.append(f"+ {len(sk.cannot_do) - 8} more")
            lines.append(f"NOT YET BUILT: {', '.join(not_yet)}")

        if sk.not_on_body:
            unavail = [c.display_name for c in sk.not_on_body[:5]]
            lines.append(f"NOT ON THIS BODY ({embodiment}): {', '.join(unavail)}")

        return "\n".join(lines)

    except Exception as exc:
        _log.warning("self_knowledge_block failed (non-fatal): %s", exc)
        return ""
