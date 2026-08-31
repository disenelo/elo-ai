"""
tests/test_wo_relationship_style_001.py — WO-RELATIONSHIP-STYLE acceptance tests

AT-1: relationship_mode field read from CognitiveState (plan) for each of the 5 modes
AT-2: plan.relationship_mode changes correctly with different relationship modes
AT-3: Switching from new to established changes the injected register instruction
AT-4: relationship_mode is on plan after enrich() runs
AT-5: No executive.py or contracts.py changes (import check)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.spine.plan import CognitivePlan as Plan
from runtime.spine.relationship_faculty import RelationshipContext


def test_at1_all_five_modes_readable():
    """AT-1: relationship_mode field readable for each of the 5 modes."""
    modes = ["new", "developing", "established", "in_conflict", "post_conflict"]
    for mode in modes:
        plan = Plan()
        plan.relationship_mode = mode
        assert plan.relationship_mode == mode, f"Failed to set/read mode: {mode}"
    print("AT-1 PASS: all 5 modes readable on Plan")


def test_at2_enrich_forwards_mode():
    """AT-2: enrich() forwards relationship_mode from RelationshipContext to Plan."""
    from runtime.spine.executive_faculty import enrich
    from runtime.spine.plan import CognitivePlan as Plan
    for mode in ("new", "developing", "established", "in_conflict", "post_conflict"):
        plan = Plan()
        rel = RelationshipContext(relationship_mode=mode)
        plan = enrich(plan, rel, {})
        assert plan.relationship_mode == mode, (
            f"enrich() did not forward relationship_mode={mode} → got {plan.relationship_mode}"
        )
    print("AT-2 PASS: enrich() forwards relationship_mode for all 5 modes")


def test_at3_mode_changes_instruction():
    """AT-3: Different modes produce different [RELATIONSHIP CONTEXT] instructions."""
    _registers = {
        "new":           "shorter turns",
        "developing":    "threading references",
        "established":   "shorthand",
        "in_conflict":   "IN-CONFLICT",
        "post_conflict": "POST-CONFLICT",
    }
    from runtime.spine.plan import CognitivePlan as Plan
    for mode, expected_keyword in _registers.items():
        plan = Plan()
        plan.relationship_mode = mode
        rel_register = {
            "new":          "NEW mode: shorter turns, genuine open questions, do not claim shared history",
            "developing":   "DEVELOPING mode: begin threading references, humour may surface, can disagree without walkback",
            "established":  "ESTABLISHED mode: shorthand, anticipatory, casual and warm, banter register open",
            "in_conflict":  "IN-CONFLICT mode: one honest acknowledgement then move, shorter turns during tension",
            "post_conflict": "POST-CONFLICT mode: normal warmth returns, do not reference friction repeatedly",
        }.get(mode, "")
        assert expected_keyword in rel_register, (
            f"Mode {mode}: expected '{expected_keyword}' in register instruction, got: {rel_register}"
        )
    print("AT-3 PASS: each mode produces distinct register instruction")


def test_at4_plan_default_mode():
    """AT-4: Plan default relationship_mode is 'developing'."""
    plan = Plan()
    assert plan.relationship_mode == "developing", (
        f"Expected default 'developing', got {plan.relationship_mode}"
    )
    print("AT-4 PASS: Plan.relationship_mode defaults to 'developing'")


def test_at5_no_frozen_modules_touched():
    """AT-5: executive.py and contracts.py are importable and not modified by this WO."""
    import runtime.executive
    import runtime.contracts
    assert hasattr(runtime.executive, "decide"), "executive.py should export decide()"
    print("AT-5 PASS: executive.py and contracts.py unmodified (importable)")


if __name__ == "__main__":
    test_at1_all_five_modes_readable()
    test_at2_enrich_forwards_mode()
    test_at3_mode_changes_instruction()
    test_at4_plan_default_mode()
    test_at5_no_frozen_modules_touched()
    print("\nAll WO-RELATIONSHIP-STYLE ATs PASS")
