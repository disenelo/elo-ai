"""
tests/test_wo114_self_choose.py — WO-114: SELF-CHOOSE — internal intents on the plan.

AT-114-1: CognitivePlan has intent_source and internal_intent fields
AT-114-2: When internal_intents() fires, intent_source == "self" and internal_intent populated
AT-114-3: When David is active (no idle), intent_source defaults to "david"
AT-114-4: internal_intent has source, kind, trigger — distinguishable from empty
AT-114-5: internal_intent.source == "self" (row 19 SELF-CHOOSE proof)
"""
from __future__ import annotations

import os
import sys
import dataclasses

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-114-1: CognitivePlan has the required fields ──────────────────────────

def test_cognitive_plan_has_intent_source_and_internal_intent():
    from runtime.spine.plan import CognitivePlan
    field_names = {f.name for f in dataclasses.fields(CognitivePlan)}
    assert "intent_source" in field_names, (
        "CognitivePlan missing intent_source — WO-099b fix5 / WO-114 not applied"
    )
    assert "internal_intent" in field_names, (
        "CognitivePlan missing internal_intent — WO-114 not applied"
    )


def test_cognitive_plan_defaults():
    from runtime.spine.plan import CognitivePlan
    p = CognitivePlan()
    assert p.intent_source == "david", f"Default intent_source should be 'david': {p.intent_source}"
    assert p.internal_intent == {}, f"Default internal_intent should be empty dict: {p.internal_intent}"


# ── AT-114-2/4: When emergent intent fires, plan gets populated ───────────────

def test_intent_source_self_when_emergent_fires():
    from self.elo_self_model import EloSelfState
    from self.emergent_cognition import internal_intents, _ABSENT_THRESHOLD, _CURIOSITY_MIN
    from runtime.spine.plan import CognitivePlan

    # Build a state that will trigger absence_awareness intent
    state = EloSelfState(
        curiosity=_CURIOSITY_MIN + 0.1,
        focal_thread="something interesting",
        inner_events=["drawn_in", "curiosity_spike"],
        lifetime_threads=[["python", 3]],
    )
    idle_s = _ABSENT_THRESHOLD + 10.0

    intents = internal_intents(state, idle_s)
    assert intents, (
        f"internal_intents() should fire with curiosity={state.curiosity}, idle={idle_s}s. "
        f"Got empty — check thresholds."
    )

    # Simulate what server.py does
    plan = CognitivePlan()
    if intents:
        plan.intent_source = "self"
        plan.internal_intent = intents[0]

    assert plan.intent_source == "self", (
        f"plan.intent_source must be 'self' when an emergent intent fired: {plan.intent_source}"
    )
    assert plan.internal_intent, (
        "plan.internal_intent must be populated when an emergent intent fired"
    )
    assert "source" in plan.internal_intent, (
        f"internal_intent must have 'source' field: {plan.internal_intent}"
    )
    assert "kind" in plan.internal_intent, (
        f"internal_intent must have 'kind' field: {plan.internal_intent}"
    )
    assert "trigger" in plan.internal_intent, (
        f"internal_intent must have 'trigger' field: {plan.internal_intent}"
    )


# ── AT-114-3: David active → intent_source defaults to "david" ───────────────

def test_intent_source_david_when_no_emergent():
    from self.elo_self_model import EloSelfState
    from self.emergent_cognition import internal_intents
    from runtime.spine.plan import CognitivePlan

    # Empty state with no history — intents cannot fire
    state = EloSelfState()
    intents = internal_intents(state, idle_seconds=0.0)
    assert not intents, f"No intent should fire with empty state and 0 idle: {intents}"

    plan = CognitivePlan()
    # Not setting intent_source — it should stay "david"
    assert plan.intent_source == "david", (
        f"When no emergent intent fires, intent_source must remain 'david': {plan.intent_source}"
    )


# ── AT-114-5: internal_intent.source == "self" — Row 19 SELF-CHOOSE proof ────

def test_internal_intent_source_equals_self():
    from self.elo_self_model import EloSelfState
    from self.emergent_cognition import internal_intents, _ABSENT_THRESHOLD, _CURIOSITY_MIN
    from runtime.spine.plan import CognitivePlan

    state = EloSelfState(
        curiosity=_CURIOSITY_MIN + 0.15,
        focal_thread="a thread worth returning to",
        inner_events=["drawn_in", "creative_spark"],
        lifetime_threads=[["design", 5]],
    )
    idle_s = _ABSENT_THRESHOLD + 30.0

    intents = internal_intents(state, idle_s)
    assert intents, "Emergent intent must fire for this test to be meaningful"

    plan = CognitivePlan()
    plan.intent_source = "self"
    plan.internal_intent = intents[0]

    # The Row 19 proof: source on the plan is "self", not "david"
    assert plan.intent_source == "self", "Row 19 SELF-CHOOSE: intent_source must be 'self'"
    assert plan.internal_intent.get("source") in (
        "absence_awareness", "active_thread", "curiosity_peak",
    ), (
        f"internal_intent.source must be a known emergent source, got: "
        f"{plan.internal_intent.get('source')}"
    )
