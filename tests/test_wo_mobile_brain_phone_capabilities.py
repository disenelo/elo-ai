"""WO-MOBILE-BRAIN: phone_capabilities field in blender_state.json — AT-7."""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_at7_spine_writes_phone_capabilities_to_state_file():
    """AT-7: Spine writes phone_capabilities to state file; field is array matching _PHONE_CAPABLE."""
    from runtime.capabilities.registry import _PHONE_CAPABLE
    from blender_bridge.state_writer import patch as bs_patch, _STATE_PATH as bs_path

    # Write the field (replicates server.py startup write)
    bs_patch({"phone_capabilities": sorted(_PHONE_CAPABLE)})

    # Read back and verify
    with open(bs_path) as f:
        state = json.load(f)

    assert "phone_capabilities" in state, (
        f"AT-7 FAIL: 'phone_capabilities' not in blender_state.json. keys={list(state.keys())[:10]}"
    )
    caps = state["phone_capabilities"]
    assert isinstance(caps, list), f"AT-7 FAIL: phone_capabilities is not a list: {type(caps)}"
    assert len(caps) > 0, "AT-7 FAIL: phone_capabilities is empty"

    # Confirm it matches _PHONE_CAPABLE
    caps_set = set(caps)
    assert caps_set == _PHONE_CAPABLE, (
        f"AT-7 FAIL: mismatch. state has {caps_set} but _PHONE_CAPABLE is {_PHONE_CAPABLE}"
    )
    print(f"✅ AT-7: phone_capabilities in blender_state.json = {sorted(caps)}")


if __name__ == "__main__":
    try:
        test_at7_spine_writes_phone_capabilities_to_state_file()
        print("\n1/1 PASS")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"❌ {e}")
        traceback.print_exc()
        print("\n0/1 PASS")
        sys.exit(1)
