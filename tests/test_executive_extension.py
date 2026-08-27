"""
tests/test_executive_extension.py

WP_F gap: runtime/spine/executive_extension.py
Executive-Delegated Capability Selection — designated extension point for
Executive-layer decisions that cannot be placed in the frozen executive.py.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_executive_extension.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.spine.executive_extension import select_capabilities


def _cap(id_: str, health: str = "OK") -> dict:
    return {"id": id_, "health": health}


def test_silence_aware_tone_returns_empty():
    """AT-1: SILENCE-AWARE tone → no capabilities authorised."""
    result = select_capabilities(
        plan_meaning="hello",
        plan_is_system_turn=False,
        capabilities=[_cap("time")],
        intent_chain=[],
        conversation_action="converse",
        tone="SILENCE-AWARE",
    )
    assert result == [], f"AT-1: SILENCE-AWARE must return []; got {result!r}"


def test_silence_action_returns_empty():
    """AT-2: conversation_action='silence' → no capabilities authorised."""
    result = select_capabilities(
        plan_meaning="okay",
        plan_is_system_turn=False,
        capabilities=[_cap("time")],
        intent_chain=[],
        conversation_action="silence",
        tone="GENTLE",
    )
    assert result == [], f"AT-2: silence action must return []; got {result!r}"


def test_ground_action_returns_empty():
    """AT-3: conversation_action='ground' → no capabilities authorised."""
    result = select_capabilities(
        plan_meaning="breathe",
        plan_is_system_turn=False,
        capabilities=[_cap("weather")],
        intent_chain=[],
        conversation_action="ground",
        tone="DIRECT",
    )
    assert result == [], f"AT-3: ground action must return []; got {result!r}"


def test_system_turn_returns_empty():
    """AT-4: plan_is_system_turn=True → no capabilities authorised."""
    result = select_capabilities(
        plan_meaning="tick",
        plan_is_system_turn=True,
        capabilities=[_cap("time"), _cap("weather")],
        intent_chain=["time", "weather"],
        conversation_action="converse",
        tone="DIRECT",
    )
    assert result == [], f"AT-4: system turn must return []; got {result!r}"


def test_healthy_capability_selected():
    """AT-5: healthy capability → returns [(cap_id, plan_meaning)]."""
    result = select_capabilities(
        plan_meaning="what time is it",
        plan_is_system_turn=False,
        capabilities=[_cap("time", "OK")],
        intent_chain=[],
        conversation_action="converse",
        tone="DIRECT",
    )
    assert result == [("time", "what time is it")], (
        f"AT-5: healthy capability must be selected; got {result!r}"
    )


def test_offline_capability_skipped():
    """AT-6: OFFLINE/AUTH_REQUIRED/DISABLED capabilities are skipped."""
    for health in ("OFFLINE", "AUTH_REQUIRED", "DISABLED"):
        result = select_capabilities(
            plan_meaning="what time",
            plan_is_system_turn=False,
            capabilities=[_cap("time", health)],
            intent_chain=[],
            conversation_action="converse",
            tone="DIRECT",
        )
        assert result == [], (
            f"AT-6: capability with health={health!r} must be skipped; got {result!r}"
        )


def test_intent_chain_of_two_returns_both():
    """AT-7: len(intent_chain) == 2 → returns both as 2-agent chain."""
    result = select_capabilities(
        plan_meaning="research topic",
        plan_is_system_turn=False,
        capabilities=[],
        intent_chain=["research", "summarise"],
        conversation_action="converse",
        tone="CREATIVE",
    )
    assert result == [("research", "research topic"), ("summarise", "research topic")], (
        f"AT-7: 2-agent chain must be returned; got {result!r}"
    )


def test_no_capabilities_no_chain_returns_empty():
    """AT-8: empty capabilities and empty chain → empty result."""
    result = select_capabilities(
        plan_meaning="hello",
        plan_is_system_turn=False,
        capabilities=[],
        intent_chain=[],
        conversation_action="converse",
        tone="CONVERSATIONAL",
    )
    assert result == [], f"AT-8: no capabilities + no chain must return []; got {result!r}"


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_silence_aware_tone_returns_empty),
        ("AT-2", test_silence_action_returns_empty),
        ("AT-3", test_ground_action_returns_empty),
        ("AT-4", test_system_turn_returns_empty),
        ("AT-5", test_healthy_capability_selected),
        ("AT-6", test_offline_capability_skipped),
        ("AT-7", test_intent_chain_of_two_returns_both),
        ("AT-8", test_no_capabilities_no_chain_returns_empty),
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
    print(f"executive_extension   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
