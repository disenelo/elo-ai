"""
runtime/agency_engine.py — Volume V Chapter 10: Autonomous Action & Agency Engine.

Spec:  docs/architecture/Volume_V/10_Agency_Engine.md
Canon: Agency Law — "Meaningful action becomes creation."
       Protect user agency — eLo never makes a decision that is David's to make.

Five-layer contract (§2 of the spec):
    INTENTION → DECISION → PLANNING → EXECUTION → REFLECTION

This module owns the InternalTick autonomy trigger. It runs after
self.emergent_cognition.internal_intents() has populated
CognitivePlan.internal_intent (intent_source == "self").

What this does:
    propose(internal_intent, ...) → ActionProposal | None
        Runs Layers 1-3 (intention gate → decision → planning) and returns
        a structured action_proposal. Never auto-executes side-effecting work.
    record_outcome(proposal, result)
        Layer 5 — feeds Ch.6 Reflection with a lesson-shaped outcome dict.

What this does NOT do:
    - Modify runtime/executive.py (FREEZE_V1_LOCK).
    - Execute destructive actions without confirmation (ST-1 — routed through
      runtime/router/execution_gate.py).
    - Override David's decisions (ST-2 — protect user agency).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any


# ── Action type routing (§3 of the spec) ─────────────────────────────────────

_ACTION_TYPES = ("Creative", "Technical", "Learning", "Relationship", "Maintenance")

_INTENT_KIND_TO_ACTION_TYPE: dict[str, str] = {
    "absence_awareness":   "Learning",
    "exploration":         "Learning",
    "return_to_thread":    "Relationship",
    "capability_practice": "Technical",
    "creative_expansion":  "Creative",
    "care_check_in":       "Relationship",
    "maintenance_sweep":   "Maintenance",
}

# Intent kinds that are David's call — Agency observes/recommends, never decides.
_USER_AGENCY_KINDS = frozenset({
    "life_choice", "money", "safety", "commit_decision",
})

# High-risk verbs on the eventual step list — force confirm-gate.
_HIGH_RISK_VERBS = frozenset({
    "delete", "remove", "wipe", "purge", "overwrite", "kill", "quit",
    "move", "rename", "install", "uninstall", "push",
})


# ── Proposal dataclass (§2 Layer 3 shape) ────────────────────────────────────

@dataclass
class ActionProposal:
    goal:              str                            # what
    reason:            str                            # why (intent kind + trigger)
    steps:             list[str]      = field(default_factory=list)
    resources:         list[str]      = field(default_factory=list)
    success_condition: str            = ""
    action_type:       str            = "Learning"    # one of _ACTION_TYPES
    requires_confirm:  bool           = False
    intent_source:     str            = "self"
    intent_kind:       str            = ""
    ts:                float          = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Layer 1 — Intention: "should something happen?" ──────────────────────────

def should_act(internal_intent: dict | None) -> tuple[bool, str]:
    """
    Evaluate whether an internal_intent justifies proposing an action.
    Returns (should_act, reason).

    Rules (§2 Layer 1):
      - No intent → do not act (SILENCE is valid — Ch.10 Failure Mode).
      - No trigger → intent is empty scaffolding; do not act.
      - Kind belongs to David's agency → observe/recommend only, never act.
    """
    if not internal_intent:
        return False, "no_intent"
    kind    = str(internal_intent.get("kind", "")).strip()
    trigger = str(internal_intent.get("trigger", "")).strip()
    if not kind:
        return False, "no_intent_kind"
    if not trigger:
        return False, "no_trigger"
    if kind in _USER_AGENCY_KINDS:
        return False, "user_agency_protected"
    return True, kind


# ── Layer 2 — Decision: what action type ─────────────────────────────────────

def _decide_action_type(intent_kind: str) -> str:
    return _INTENT_KIND_TO_ACTION_TYPE.get(intent_kind, "Learning")


# ── Layer 3 — Planning: structured {goal, reason, steps, resources, success_condition} ──

def plan(goal: str, reason: str, *, steps: list[str] | None = None,
         resources: list[str] | None = None,
         success_condition: str = "") -> dict:
    """Return the Layer-3 structured plan shape from §2 Layer 3 of the spec."""
    return {
        "goal":              goal,
        "reason":            reason,
        "steps":             list(steps or []),
        "resources":         list(resources or []),
        "success_condition": success_condition,
    }


# ── Layer 4 — Risk assessment (routes into execution_gate) ───────────────────

def _is_high_risk(steps: list[str]) -> bool:
    for step in steps:
        low = step.lower()
        for verb in _HIGH_RISK_VERBS:
            if verb in low.split():
                return True
    return False


# ── Public: propose(internal_intent) — Layers 1-3 combined ───────────────────

def propose(internal_intent: dict | None,
            *,
            state: Any = None,
            cognitive_state: dict | None = None) -> ActionProposal | None:
    """
    Runs the Layer 1-3 pipeline: intention gate → decision → planning.
    Returns an ActionProposal (never executes) or None if the intention gate
    said no.
    """
    act, reason = should_act(internal_intent)
    if not act:
        return None

    kind         = str(internal_intent.get("kind", ""))
    trigger      = str(internal_intent.get("trigger", ""))
    goal         = internal_intent.get("goal") or f"respond to {kind}"
    action_type  = _decide_action_type(kind)

    # Minimal step scaffold — Layer-3 shape is required, content is intent-derived.
    # The Executive/Reflection will refine on future ticks; the engine is not a planner
    # for arbitrary work, only a proposer for internal intents.
    steps: list[str] = []
    if kind == "return_to_thread":
        steps = [f"resume focal thread: {trigger}"]
    elif kind in ("exploration", "absence_awareness"):
        steps = [f"observe or ask about: {trigger}"]
    elif kind == "capability_practice":
        steps = [f"exercise capability tied to: {trigger}"]

    proposal = ActionProposal(
        goal              = str(goal)[:200],
        reason            = f"{kind}: {trigger}"[:300],
        steps             = steps,
        resources         = [],
        success_condition = "acknowledged_by_david_or_advanced_state",
        action_type       = action_type,
        requires_confirm  = _is_high_risk(steps),
        intent_source     = "self",
        intent_kind       = kind,
        ts                = time.time(),
    )
    return proposal


# ── Layer 5 — Reflection feed ────────────────────────────────────────────────

def record_outcome(proposal: ActionProposal | dict | None,
                   result: str,
                   *,
                   completion_state: str = "met") -> dict:
    """
    Emit a Ch.6-shaped outcome record. Never writes to memory directly — the
    caller passes this dict to runtime.reflection_faculty.integrate_session().
    """
    if proposal is None:
        return {"skipped": True, "reason": "no_proposal"}
    if isinstance(proposal, ActionProposal):
        p = proposal.to_dict()
    else:
        p = dict(proposal)
    return {
        "session_summary":   f"Agency proposal: {p.get('goal','')}. Outcome: {result}",
        "project":           "agency",
        "action":            p.get("action_type", "Learning").lower(),
        "planned_objective": p.get("goal", ""),
        "completion_state":  completion_state,
    }
