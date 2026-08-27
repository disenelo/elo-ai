"""
tests/test_executive_override_guard.py

WP_F gap: runtime/executive_override.py — D7 ruling (Card 0035).
Post-Executive safety overrides must use only REGISTERED_GROUNDS.
Unregistered grounds must raise UnregisteredOverrideGround (loud failure,
not silent drift). This is a One-Brain enforcement module.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_executive_override_guard.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.executive_override import (
    REGISTERED_GROUNDS,
    UnregisteredOverrideGround,
    apply_executive_override,
)


def test_registered_grounds_whitelist_has_two_entries():
    """AT-1: REGISTERED_GROUNDS contains exactly the two documented grounds."""
    assert "safety-stabilisation" in REGISTERED_GROUNDS, (
        "AT-1: 'safety-stabilisation' must be a registered override ground"
    )
    assert "seam-a-routing" in REGISTERED_GROUNDS, (
        "AT-1: 'seam-a-routing' must be a registered override ground"
    )
    assert len(REGISTERED_GROUNDS) == 2, (
        f"AT-1: only 2 grounds are registered (D7 ruling); got {sorted(REGISTERED_GROUNDS)}"
    )


def test_unregistered_ground_raises():
    """AT-2: an unregistered override ground raises UnregisteredOverrideGround."""
    decision = {"action": "walk", "confidence": 0.7}
    raised = False
    try:
        apply_executive_override(
            decision,
            ground="rogue-override",
            rule="some-undocumented-rule",
            updates={"action": "run"},
        )
    except UnregisteredOverrideGround:
        raised = True
    assert raised, (
        "AT-2: UnregisteredOverrideGround must be raised for unregistered grounds"
    )


def test_safety_stabilisation_applies_correctly():
    """AT-3: safety-stabilisation ground sets overridden_by_safety + preserves original_action."""
    decision = {"action": "walk", "confidence": 0.7}
    result = apply_executive_override(
        decision,
        ground="safety-stabilisation",
        rule="loop-detection",
        updates={"action": "stabilise"},
    )
    assert result["action"] == "stabilise", (
        f"AT-3: action must be updated to 'stabilise'; got {result['action']!r}"
    )
    assert result["original_action"] == "walk", (
        f"AT-3: original_action must be 'walk'; got {result['original_action']!r}"
    )
    assert result.get("overridden_by_safety") is True, (
        "AT-3: overridden_by_safety must be True for safety-stabilisation"
    )
    assert result["executive_override"]["ground"] == "safety-stabilisation", (
        "AT-3: executive_override.ground must be 'safety-stabilisation'"
    )


def test_seam_a_routing_applies_correctly():
    """AT-4: seam-a-routing ground sets overridden_by_routing, not overridden_by_safety."""
    decision = {"action": "converse", "confidence": 0.8}
    result = apply_executive_override(
        decision,
        ground="seam-a-routing",
        rule="WO-020 seam-A plain imperative",
        updates={"action": "direct_response"},
    )
    assert result["action"] == "direct_response", (
        f"AT-4: action must be 'direct_response'; got {result['action']!r}"
    )
    assert result.get("overridden_by_routing") is True, (
        "AT-4: overridden_by_routing must be True for seam-a-routing"
    )
    assert "overridden_by_safety" not in result or not result.get("overridden_by_safety"), (
        "AT-4: overridden_by_safety must NOT be set for seam-a-routing"
    )


def test_chained_overrides_preserve_earliest_original_action():
    """AT-5: a second override does not overwrite the first original_action."""
    decision = {"action": "jump", "confidence": 0.6}
    first = apply_executive_override(
        decision,
        ground="safety-stabilisation",
        rule="loop-detection",
        updates={"action": "stabilise"},
    )
    # Apply a second override on top — original_action must still be "jump"
    second = apply_executive_override(
        first,
        ground="seam-a-routing",
        rule="WO-029",
        updates={"action": "direct_response"},
    )
    assert second["original_action"] == "jump", (
        f"AT-5: chained override must not overwrite original_action; "
        f"expected 'jump', got {second['original_action']!r}"
    )


def test_apply_does_not_mutate_input():
    """AT-6: apply_executive_override returns a NEW dict — input is unchanged."""
    decision = {"action": "walk", "confidence": 0.9}
    original_id = id(decision)
    result = apply_executive_override(
        decision,
        ground="safety-stabilisation",
        rule="loop-detection",
        updates={"action": "stabilise"},
    )
    assert id(result) != original_id, (
        "AT-6: apply_executive_override must return a new dict"
    )
    assert decision["action"] == "walk", (
        "AT-6: input dict must not be mutated; action is still 'walk'"
    )


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_registered_grounds_whitelist_has_two_entries),
        ("AT-2", test_unregistered_ground_raises),
        ("AT-3", test_safety_stabilisation_applies_correctly),
        ("AT-4", test_seam_a_routing_applies_correctly),
        ("AT-5", test_chained_overrides_preserve_earliest_original_action),
        ("AT-6", test_apply_does_not_mutate_input),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"executive_override guard   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
