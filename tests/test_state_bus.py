"""
tests/test_state_bus.py

WP_F gap: core/state_bus.py — immutability boundary between engines.
Architecture invariant: "No engine may write to the bus after it is created."
Covers IdentitySnapshot, StateSnapshot, EmotionSnapshot, MemorySnapshot, StateBus.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_state_bus.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.state_bus import (
    IdentitySnapshot,
    StateSnapshot,
    EmotionSnapshot,
    MemorySnapshot,
    StateBus,
)


def _identity() -> IdentitySnapshot:
    return IdentitySnapshot.from_dict({})


def _state() -> StateSnapshot:
    return StateSnapshot.from_dict({})


def _emotion() -> EmotionSnapshot:
    return EmotionSnapshot.from_dict({})


def _memory() -> MemorySnapshot:
    return MemorySnapshot({"tone_signal": "warm", "project": "test"})


def _bus() -> StateBus:
    return StateBus(
        user_input="hello",
        identity=_identity(),
        state=_state(),
        emotion=_emotion(),
        memory=_memory(),
    )


def test_identity_snapshot_is_frozen():
    """AT-1: IdentitySnapshot is a frozen dataclass — mutation raises FrozenInstanceError."""
    snap = _identity()
    raised = False
    try:
        snap.perspective = "changed"  # type: ignore
    except Exception:
        raised = True
    assert raised, "AT-1: IdentitySnapshot must be immutable (frozen dataclass)"


def test_state_snapshot_is_frozen():
    """AT-2: StateSnapshot is a frozen dataclass — mutation raises."""
    snap = _state()
    raised = False
    try:
        snap.name = "changed"  # type: ignore
    except Exception:
        raised = True
    assert raised, "AT-2: StateSnapshot must be immutable (frozen dataclass)"


def test_memory_snapshot_rejects_setattr():
    """AT-3: MemorySnapshot.__setattr__ raises AttributeError — read-only after creation."""
    mem = _memory()
    raised = False
    try:
        mem.tone_signal = "hostile"  # type: ignore
    except AttributeError:
        raised = True
    assert raised, "AT-3: MemorySnapshot must reject attribute writes"


def test_memory_snapshot_underlying_proxy_is_immutable():
    """AT-4: MemorySnapshot to_dict() returns a mutable copy — not the original."""
    mem = _memory()
    d = mem.to_dict()
    d["injected"] = "evil"  # mutate copy — must not affect snapshot
    assert mem.get("injected") is None, (
        "AT-4: mutating to_dict() result must not affect MemorySnapshot"
    )


def test_state_bus_rejects_setattr():
    """AT-5: StateBus.__setattr__ raises AttributeError — immutable after creation."""
    bus = _bus()
    raised = False
    try:
        bus.user_input = "hacked"  # type: ignore
    except AttributeError:
        raised = True
    assert raised, "AT-5: StateBus must be immutable — __setattr__ must raise"


def test_state_bus_properties_readable():
    """AT-6: StateBus exposes all 7 properties correctly."""
    bus = _bus()
    assert bus.user_input == "hello", f"AT-6: user_input wrong: {bus.user_input!r}"
    assert isinstance(bus.identity, IdentitySnapshot), "AT-6: identity type mismatch"
    assert isinstance(bus.state, StateSnapshot), "AT-6: state type mismatch"
    assert isinstance(bus.emotion, EmotionSnapshot), "AT-6: emotion type mismatch"
    assert isinstance(bus.memory, MemorySnapshot), "AT-6: memory type mismatch"
    assert bus.mode == "companion", f"AT-6: default mode wrong: {bus.mode!r}"
    assert bus.project == "elo_core", f"AT-6: default project wrong: {bus.project!r}"


def test_to_context_returns_independent_dict():
    """AT-7: to_context() returns a new dict — mutations don't affect the bus."""
    bus = _bus()
    ctx = bus.to_context()
    assert isinstance(ctx, dict), f"AT-7: to_context() must return dict; got {type(ctx)}"
    ctx["injected"] = "attack"
    # Calling again must not have the injected key
    ctx2 = bus.to_context()
    assert "injected" not in ctx2, (
        "AT-7: to_context() mutation must not persist on the StateBus"
    )


def test_to_context_contains_required_keys():
    """AT-8: to_context() dict contains project, mode, and identity/state/emotion keys."""
    ctx = _bus().to_context()
    for key in ("project", "mode", "identity_perspective", "state", "emotion"):
        assert key in ctx, f"AT-8: to_context() must contain '{key}'; got keys: {list(ctx)}"


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_identity_snapshot_is_frozen),
        ("AT-2", test_state_snapshot_is_frozen),
        ("AT-3", test_memory_snapshot_rejects_setattr),
        ("AT-4", test_memory_snapshot_underlying_proxy_is_immutable),
        ("AT-5", test_state_bus_rejects_setattr),
        ("AT-6", test_state_bus_properties_readable),
        ("AT-7", test_to_context_returns_independent_dict),
        ("AT-8", test_to_context_contains_required_keys),
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
    print(f"state_bus   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
