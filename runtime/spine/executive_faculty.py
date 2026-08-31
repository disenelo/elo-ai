"""
runtime/spine/executive_faculty.py — eLo OS v1.5 Executive Faculty

The only entity permitted to make decisions.

Receives all faculty outputs. Produces ONE CognitivePlan.
No other faculty makes decisions.

Architecture spec: docs/architecture/09_executive_faculty.md

NOTE: The identity/personality layer lives in runtime/executive.py and
is protected by FREEZE_V1_LOCK.md. This module wraps it — never replaces it.
"""
from __future__ import annotations
import logging
from dataclasses import asdict

from runtime.spine.plan import CognitivePlan, EmotionalVector
from runtime.spine.relationship_faculty import RelationshipContext

_log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# EMOTIONAL VECTOR COMPUTATION
# Maps Executive outputs (attention + action + valence) → EmotionalVector
# The Vector is fed downstream to the Emotional Light Engine.
# ─────────────────────────────────────────────────────────────────────────────

_ACTION_TO_STATE = {
    "answer":    "focus",
    "build":     "creative_discovery",
    "connect":   "exploring",
    "celebrate": "joy",
    "reflect":   "reflection",
    "ground":    "comfort",
    "challenge": "challenge",
    "witness":   "listening",
    "silence":   "witnessing",
}

_VALENCE_WARMTH = {
    "positive": 0.82,
    "high":     0.80,
    "neutral":  0.60,
    "negative": 0.40,
    "low":      0.38,
}

_MOMENTUM_ENERGY = {
    "building":  0.82,
    "stable":    0.55,
    "declining": 0.34,
}


def _compute_emotional_vector(
    plan:             CognitivePlan,
    relationship:     RelationshipContext,
) -> EmotionalVector:
    """
    Derive the EmotionalVector from Executive outputs and relationship context.

    All values are continuous 0.0–1.0.
    The canonical state name maps to the ELE spectrum (docs/architecture/11_...).
    """
    action   = plan.conversation_action
    valence  = plan.valence
    momentum = plan.momentum

    state   = _ACTION_TO_STATE.get(action, "exploring")
    warmth  = _VALENCE_WARMTH.get(valence, 0.60)
    energy  = _MOMENTUM_ENERGY.get(momentum, 0.55)

    # Relationship enriches the vector
    warmth     = min(warmth + relationship.familiarity * 0.12, 0.98)
    connection = min(relationship.trust, 0.98)

    # Action-specific vector shaping
    if action == "build":
        return EmotionalVector(
            state=state, energy=energy, warmth=warmth, curiosity=0.88,
            focus=0.82, playfulness=0.70, confidence=plan.confidence,
            reflection=0.20, momentum=energy, connection=connection, calm=0.30,
        )
    if action == "celebrate":
        return EmotionalVector(
            state=state, energy=min(energy + 0.25, 0.98), warmth=min(warmth + 0.15, 0.98),
            curiosity=0.60, focus=0.50, playfulness=0.80, confidence=plan.confidence,
            reflection=0.15, momentum=0.85, connection=connection, calm=0.25,
        )
    if action == "reflect":
        return EmotionalVector(
            state=state, energy=max(energy - 0.20, 0.20), warmth=warmth,
            curiosity=0.55, focus=0.60, playfulness=0.20, confidence=plan.confidence,
            reflection=0.80, momentum=max(energy - 0.30, 0.15), connection=connection, calm=0.65,
        )
    if action == "ground":
        return EmotionalVector(
            state=state, energy=0.35, warmth=min(warmth + 0.20, 0.98),
            curiosity=0.30, focus=0.45, playfulness=0.15, confidence=0.70,
            reflection=0.55, momentum=0.25, connection=min(connection + 0.15, 0.98), calm=0.80,
        )
    if action == "witness":
        return EmotionalVector(
            state=state, energy=0.28, warmth=min(warmth + 0.25, 0.98),
            curiosity=0.25, focus=0.50, playfulness=0.10, confidence=0.65,
            reflection=0.70, momentum=0.18, connection=min(connection + 0.20, 0.98), calm=0.75,
        )
    if action == "challenge":
        return EmotionalVector(
            state=state, energy=min(energy + 0.10, 0.90), warmth=warmth,
            curiosity=0.72, focus=0.78, playfulness=0.35, confidence=plan.confidence,
            reflection=0.45, momentum=energy, connection=connection, calm=0.40,
        )
    if action == "connect":
        return EmotionalVector(
            state=state, energy=energy, warmth=warmth,
            curiosity=0.85, focus=0.70, playfulness=0.55, confidence=plan.confidence,
            reflection=0.40, momentum=energy, connection=min(connection + 0.10, 0.98), calm=0.45,
        )

    # Default: answer / conversation
    return EmotionalVector(
        state=state, energy=energy, warmth=warmth,
        curiosity=0.60, focus=0.68, playfulness=0.40, confidence=plan.confidence,
        reflection=0.30, momentum=energy, connection=connection, calm=0.50,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

def enrich(
    plan:         CognitivePlan,
    relationship: RelationshipContext | None = None,
    attention:    dict | None = None,
) -> CognitivePlan:
    """
    Apply relationship context and compute the EmotionalVector.

    Called by spine.py AFTER the raw executive decision (from executive.py)
    has already been loaded into the plan.

    Args:
        plan:         CognitivePlan with executive decision already populated
        relationship: RelationshipContext from Relationship Faculty
        attention:    attention dict (for additional enrichment)

    Returns: the same plan object, enriched in-place.
    This keeps the Executive as a single pass.
    """
    if relationship is None:
        from runtime.spine.relationship_faculty import RelationshipContext
        relationship = RelationshipContext()

    # Apply relationship context to plan
    plan.relationship_type  = relationship.relationship_type
    plan.familiarity        = relationship.familiarity
    plan.trust              = relationship.trust
    plan.expression_posture = relationship.expression_posture
    plan.active_projects    = relationship.active_projects
    plan.relationship_mode  = relationship.relationship_mode  # WO-RELATIONSHIP-STYLE

    # Override register from relationship if not set by language faculty
    if not plan.register and relationship.register:
        plan.register = relationship.register

    # Compute and attach emotional vector
    vec = _compute_emotional_vector(plan, relationship)
    plan.emotional_vector = vec.to_dict()

    return plan
