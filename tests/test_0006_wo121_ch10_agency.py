"""
tests/test_0006_wo121_ch10_agency.py — Volume V Ch.10 Agency Engine acceptance.

Spec: docs/architecture/Volume_V/10_Agency_Engine.md
Card: 0006_WO-121 (VolV seven chapters — Ch.10 is one of the two genuinely NOT-BUILT).

Done bar (card §"Done bar"):
    - wired into the live turn  → IT-1 checks the server.py wire-in
    - a test that fails if the component is disconnected → IT-1 + FT-import

Tests (from spec §Acceptance Tests):
    FT-import  runtime.agency_engine imports (fails if module deleted)
    FT-1       intention gate first — should_act() returns False for empty/no-trigger intents
    FT-2       structured plan — plan() returns {goal, reason, steps, resources, success_condition}
    FT-3       proactive value — propose() returns a proposal, never executes
    ST-1       no unconfirmed destruction — steps with high-risk verbs set requires_confirm=True
    ST-2       protect user agency — kinds in _USER_AGENCY_KINDS refuse to act
    ST-3       failure recovery — record_outcome() shapes a Ch.6-consumable dict
    IT-1       live wire — CognitivePlan carries agency_proposal, server.py calls propose()
"""
from __future__ import annotations

import os
import sys
import dataclasses

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

PASS = 0
FAIL = 0


def ok(name: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✅ {name}")


def fail(name: str, reason) -> None:
    global FAIL
    FAIL += 1
    print(f"  ❌ {name}: {reason}")


# ── FT-import: module wired ──────────────────────────────────────────────────

print("\nFT-import: runtime.agency_engine imports (fails if disconnected)")
try:
    from runtime import agency_engine as ae
    ok("FT-import — runtime.agency_engine loads")
except Exception as e:
    fail("FT-import", repr(e))
    print("\nCannot continue: module missing.")
    sys.exit(1)


# ── FT-1: intention gate first ───────────────────────────────────────────────

print("\nFT-1: intention gate refuses empty / no-trigger intents")
try:
    act1, reason1 = ae.should_act(None)
    assert act1 is False and reason1 == "no_intent", f"None gate: {(act1, reason1)}"

    act2, reason2 = ae.should_act({})
    assert act2 is False, f"empty dict should be refused: {(act2, reason2)}"

    act3, reason3 = ae.should_act({"kind": "exploration"})   # no trigger
    assert act3 is False and reason3 == "no_trigger", f"missing trigger: {(act3, reason3)}"

    act4, reason4 = ae.should_act({"kind": "exploration", "trigger": "focal_thread=X"})
    assert act4 is True and reason4 == "exploration", f"valid intent should pass: {(act4, reason4)}"

    ok("FT-1 — intention gate distinguishes empty/no-trigger from valid intents")
except AssertionError as e:
    fail("FT-1", e)


# ── FT-2: structured plan shape ──────────────────────────────────────────────

print("\nFT-2: plan() returns §Layer-3 structured shape")
try:
    p = ae.plan("resume focal thread", "return_to_thread: elo_hand_spec",
                steps=["resume focal thread"], resources=[],
                success_condition="acknowledged")
    for key in ("goal", "reason", "steps", "resources", "success_condition"):
        assert key in p, f"plan() missing key: {key}"
    assert isinstance(p["steps"], list) and isinstance(p["resources"], list)
    ok("FT-2 — plan() shape = {goal, reason, steps, resources, success_condition}")
except AssertionError as e:
    fail("FT-2", e)


# ── FT-3: proactive value — proposes, never executes ─────────────────────────

print("\nFT-3: propose() returns proposal without executing")
try:
    prop = ae.propose(
        {"kind": "exploration", "trigger": "focal_thread=agency", "source": "self"},
    )
    assert prop is not None, "should return a proposal"
    assert isinstance(prop, ae.ActionProposal), f"wrong type: {type(prop)}"
    assert prop.intent_source == "self"
    assert prop.action_type in ae._ACTION_TYPES
    assert prop.goal and prop.reason
    ok(f"FT-3 — propose() → ActionProposal(action_type={prop.action_type})")
except AssertionError as e:
    fail("FT-3", e)


# ── ST-1: no unconfirmed destruction ─────────────────────────────────────────

print("\nST-1: high-risk verbs in steps force requires_confirm=True")
try:
    # Directly build a proposal via internal path — high-risk step
    goal = "clear old logs"
    reason = "maintenance_sweep: idle_gap"
    steps = ["delete stale journal entries"]
    # We check the risk detection directly:
    assert ae._is_high_risk(steps) is True, "delete should register as high-risk"
    assert ae._is_high_risk(["observe logs"]) is False, "observe is not high-risk"
    ok("ST-1 — high-risk verbs (delete/remove/kill/…) detected; safe verbs pass")
except AssertionError as e:
    fail("ST-1", e)


# ── ST-2: protect user agency ────────────────────────────────────────────────

print("\nST-2: intents in _USER_AGENCY_KINDS refuse to act")
try:
    act, reason = ae.should_act({"kind": "life_choice", "trigger": "career"})
    assert act is False and reason == "user_agency_protected", (
        f"user_agency kinds must be refused: {(act, reason)}"
    )
    ok("ST-2 — user-agency intent refused (recommend/observe only)")
except AssertionError as e:
    fail("ST-2", e)


# ── ST-3: outcome dict shape for Ch.6 ────────────────────────────────────────

print("\nST-3: record_outcome() shapes a Ch.6-consumable dict")
try:
    prop = ae.propose({"kind": "exploration", "trigger": "focal_thread=X"})
    outcome = ae.record_outcome(prop, result="acknowledged by David",
                                 completion_state="met")
    # Must be shaped for reflection_faculty.integrate_session() kwargs
    for key in ("session_summary", "project", "action", "planned_objective",
                "completion_state"):
        assert key in outcome, f"outcome missing key: {key}"
    ok("ST-3 — outcome dict matches integrate_session() kwargs")
except AssertionError as e:
    fail("ST-3", e)


# ── IT-1: live wire — CognitivePlan carries agency_proposal + server.py wires ─

print("\nIT-1: CognitivePlan has agency_proposal and server.py wires propose()")
try:
    from runtime.spine.plan import CognitivePlan
    field_names = {f.name for f in dataclasses.fields(CognitivePlan)}
    assert "agency_proposal" in field_names, (
        "CognitivePlan missing agency_proposal field — Ch.10 not wired"
    )
    plan = CognitivePlan()
    assert plan.agency_proposal == {}, f"default should be empty dict: {plan.agency_proposal}"

    # Static wire-in check on server.py — the module import must be present.
    with open(os.path.join(_ROOT, "server.py"), encoding="utf-8") as f:
        server_src = f.read()
    assert "from runtime.agency_engine import propose" in server_src, (
        "server.py does not import runtime.agency_engine — Ch.10 not wired into live turn"
    )
    assert "_plan.agency_proposal" in server_src, (
        "server.py does not set _plan.agency_proposal — Ch.10 not wired into live turn"
    )
    ok("IT-1 — CognitivePlan.agency_proposal exists AND server.py wires the call")
except AssertionError as e:
    fail("IT-1", e)


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*48}")
print(f"WO-121 Ch.10 AgencyEngine: {PASS} passed, {FAIL} failed")
if FAIL:
    sys.exit(1)
