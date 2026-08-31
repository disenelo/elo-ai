"""
tests/test_lifecycle.py — Acceptance tests for eLo Cognitive Lifecycle
Four-Layer Identity Model (2026-08-31)

AT-1  LifecycleState enum contains all 8 canonical states
AT-2  LifecycleManager boots in AWAKE
AT-3  on_turn() transitions to ENGAGED
AT-4  tick() transitions LOW_LOAD after 2+ min idle, RECHARGING after 10+ min idle
AT-5  enter_dream() / exit_dream() set DREAMING then RESTORED
AT-6  on_turn() during RESTORED returns to ENGAGED (new interaction wakes eLo)
AT-7  lifecycle_state in _PRESERVE_KEYS survives a _write()
AT-8  MemoryOrigin: DREAM_SIMULATION is not auto-storable; all others are
AT-9  lifecycle_state field exists on CognitiveState and EmbodimentState
AT-10 lifecycle_state field exists on EloSelfState
"""
import json
import os
import sys
import time
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# AT-1
def test_lifecycle_state_enum_values():
    from runtime.lifecycle import LifecycleState
    expected = {"awake", "engaged", "processing", "low_load",
                "recharging", "consolidating", "dreaming", "restored"}
    actual = {s.value for s in LifecycleState}
    assert actual == expected, f"Missing states: {expected - actual}"


# AT-2
def test_lifecycle_manager_boots_awake():
    from runtime.lifecycle import LifecycleManager, LifecycleState
    mgr = LifecycleManager()
    assert mgr.state == LifecycleState.AWAKE


# AT-3
def test_on_turn_enters_engaged():
    from runtime.lifecycle import LifecycleManager, LifecycleState
    mgr = LifecycleManager()
    mgr.on_turn()
    assert mgr.state == LifecycleState.ENGAGED


# AT-4
def test_tick_transitions_on_idle():
    from runtime.lifecycle import LifecycleManager, LifecycleState, _LOW_LOAD_IDLE, _RECHARGING_IDLE
    mgr = LifecycleManager()
    mgr.on_turn()
    # Simulate 2+ min idle by backdating last activity
    mgr._last_activity_ts = time.time() - (_LOW_LOAD_IDLE + 1)
    state = mgr.tick()
    assert state == LifecycleState.LOW_LOAD, f"Expected LOW_LOAD, got {state}"

    # Simulate 10+ min idle
    mgr._last_activity_ts = time.time() - (_RECHARGING_IDLE + 1)
    state = mgr.tick()
    assert state == LifecycleState.RECHARGING, f"Expected RECHARGING, got {state}"


# AT-5
def test_dream_cycle():
    from runtime.lifecycle import LifecycleManager, LifecycleState
    mgr = LifecycleManager()
    mgr.enter_dream()
    assert mgr.state == LifecycleState.DREAMING
    mgr.exit_dream()
    assert mgr.state == LifecycleState.RESTORED


# AT-6
def test_on_turn_wakes_from_restored():
    from runtime.lifecycle import LifecycleManager, LifecycleState
    mgr = LifecycleManager()
    mgr.enter_dream()
    mgr.exit_dream()
    assert mgr.state == LifecycleState.RESTORED
    mgr.on_turn()
    assert mgr.state == LifecycleState.ENGAGED


# AT-7
def test_lifecycle_state_survives_write():
    import blender_bridge.state_writer as _sw
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        fake_path = f.name
    original_path = _sw._STATE_PATH
    try:
        _sw._STATE_PATH = fake_path
        # Write lifecycle_state via patch
        _sw.patch({"lifecycle_state": "recharging"})
        # Write a new turn via write() — without lifecycle_state param → should preserve it
        _sw.write(
            motion={"animation": "idle", "speed": 0.5, "intensity": 0.5, "duration": 4.0},
        )
        with open(fake_path, encoding="utf-8") as f2:
            data = json.load(f2)
        assert data.get("lifecycle_state") == "recharging", \
            f"lifecycle_state not preserved: {data.get('lifecycle_state')}"
    finally:
        _sw._STATE_PATH = original_path
        os.unlink(fake_path)


# AT-8
def test_memory_origin_dream_not_auto_storable():
    from runtime.memory_origin import MemoryOrigin, is_auto_storable
    assert not is_auto_storable(MemoryOrigin.DREAM_SIMULATION)
    assert is_auto_storable(MemoryOrigin.REAL_EXPERIENCE)
    assert is_auto_storable(MemoryOrigin.CONSOLIDATED)
    assert is_auto_storable(MemoryOrigin.DREAM_INSIGHT)
    assert is_auto_storable(MemoryOrigin.EPISODIC_TRACE)
    assert is_auto_storable(MemoryOrigin.SELF_MODEL)
    assert is_auto_storable(MemoryOrigin.SEMANTIC)


# AT-9
def test_lifecycle_state_on_contracts():
    from runtime.contracts import CognitiveState, EmbodimentState
    cs = CognitiveState()
    assert hasattr(cs, "lifecycle_state"), "CognitiveState missing lifecycle_state"
    assert cs.lifecycle_state == "awake"
    es = EmbodimentState()
    assert hasattr(es, "lifecycle_state"), "EmbodimentState missing lifecycle_state"
    assert es.lifecycle_state == "awake"


# AT-10
def test_lifecycle_state_on_self_state():
    from self.elo_self_model import EloSelfState
    s = EloSelfState()
    assert hasattr(s, "lifecycle_state"), "EloSelfState missing lifecycle_state"
    assert s.lifecycle_state == "awake"


if __name__ == "__main__":
    tests = [
        test_lifecycle_state_enum_values,
        test_lifecycle_manager_boots_awake,
        test_on_turn_enters_engaged,
        test_tick_transitions_on_idle,
        test_dream_cycle,
        test_on_turn_wakes_from_restored,
        test_lifecycle_state_survives_write,
        test_memory_origin_dream_not_auto_storable,
        test_lifecycle_state_on_contracts,
        test_lifecycle_state_on_self_state,
    ]
    failed = []
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed.append(t.__name__)
    print(f"\n{'ALL PASS' if not failed else f'FAILED: {failed}'}")
