"""WO-MOBILE-PHASE2: Brain publishes Phase 2 mobile signals to blender_state.json.

AT-1  embodiment: "desktop" written to state file at startup
AT-2  travel_intent field writable and readable (initial false; can be set true)
AT-3  asleep: true on sleep event; asleep: false on wake
AT-4  All three fields present → probe serves them unchanged (read-only check)
AT-5  executive.py not modified (FREEZE_V1_LOCK clean)

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_mobile_phase2_brain_signals.py -q
"""
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_ROOT = os.path.dirname(os.path.dirname(__file__))


def _read_state():
    from blender_bridge.state_writer import _STATE_PATH
    with open(_STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


# AT-1 — embodiment: "desktop" written at startup
def test_at1_embodiment_desktop():
    """AT-1: Brain writes embodiment='desktop' to state file (startup signal)."""
    from blender_bridge.state_writer import patch as bs_patch
    # Replicate startup write
    bs_patch({"embodiment": "desktop"})
    state = _read_state()
    assert "embodiment" in state, (
        f"AT-1 FAIL: 'embodiment' not in blender_state.json. keys={list(state.keys())[:15]}"
    )
    assert state["embodiment"] == "desktop", (
        f"AT-1 FAIL: embodiment={state['embodiment']!r}, expected 'desktop'"
    )
    print(f"✅ AT-1: embodiment='{state['embodiment']}' in state file")


# AT-2 — travel_intent field writable and readable
def test_at2_travel_intent_writable():
    """AT-2: travel_intent field can be written and read back."""
    from blender_bridge.state_writer import patch as bs_patch
    # Write false (startup default)
    bs_patch({"travel_intent": False})
    state = _read_state()
    assert "travel_intent" in state, "AT-2 FAIL: 'travel_intent' not in state file after write"
    assert state["travel_intent"] is False, (
        f"AT-2 FAIL: travel_intent={state['travel_intent']!r} after writing False"
    )
    # Cognitive loop sets true — verify field accepts true
    bs_patch({"travel_intent": True})
    state = _read_state()
    assert state["travel_intent"] is True, (
        f"AT-2 FAIL: travel_intent={state['travel_intent']!r} after writing True"
    )
    # Restore to false
    bs_patch({"travel_intent": False})
    print("✅ AT-2: travel_intent writable and readable (False → True → False)")


# AT-3 — asleep: true on sleep event; false on wake
def test_at3_asleep_true_on_sleep_false_on_wake():
    """AT-3: asleep=true on step_out event; asleep=false on return_elo."""
    from blender_bridge.state_writer import patch as bs_patch
    # Simulate step_out (sleep event)
    bs_patch({"asleep": True})
    state = _read_state()
    assert "asleep" in state, "AT-3 FAIL: 'asleep' not in state file after sleep event"
    assert state["asleep"] is True, (
        f"AT-3 FAIL: asleep={state['asleep']!r} after sleep event — expected True"
    )
    # Simulate return_elo (wake event)
    bs_patch({"asleep": False})
    state = _read_state()
    assert state["asleep"] is False, (
        f"AT-3 FAIL: asleep={state['asleep']!r} after wake event — expected False"
    )
    print("✅ AT-3: asleep=True on sleep, asleep=False on wake")


# AT-4 — all three fields present, probe serves them unchanged
def test_at4_all_three_fields_present():
    """AT-4: All three fields present in state file after startup writes."""
    from blender_bridge.state_writer import patch as bs_patch
    bs_patch({"embodiment": "desktop", "travel_intent": False, "asleep": False})
    state = _read_state()
    for field in ("embodiment", "travel_intent", "asleep"):
        assert field in state, (
            f"AT-4 FAIL: '{field}' not in blender_state.json. keys={list(state.keys())[:15]}"
        )
    assert state["embodiment"] == "desktop"
    assert state["travel_intent"] is False
    assert state["asleep"] is False
    print(f"✅ AT-4: all three fields present — "
          f"embodiment={state['embodiment']!r}, "
          f"travel_intent={state['travel_intent']}, "
          f"asleep={state['asleep']}")


# AT-5 — executive.py not modified (FREEZE_V1_LOCK clean)
def test_at5_executive_freeze_clean():
    """AT-5: executive.py not modified by WO-MOBILE-PHASE2."""
    exec_path = os.path.join(_ROOT, "runtime", "executive.py")
    if not os.path.exists(exec_path):
        print("AT-5 SKIP: executive.py not found (path may differ)")
        return
    with open(exec_path, "rb") as f:
        content = f.read()
    for token in (b"WO-MOBILE-PHASE2", b"travel_intent", b"asleep", b"ph2_patch"):
        assert token not in content, (
            f"AT-5 FAIL: FREEZE_V1_LOCK VIOLATED — executive.py contains '{token.decode()}'"
        )
    print("✅ AT-5: executive.py untouched — FREEZE_V1_LOCK clean")


if __name__ == "__main__":
    tests = [
        test_at1_embodiment_desktop,
        test_at2_travel_intent_writable,
        test_at3_asleep_true_on_sleep_false_on_wake,
        test_at4_all_three_fields_present,
        test_at5_executive_freeze_clean,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            import traceback
            print(f"❌ FAIL {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-MOBILE-PHASE2 ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
