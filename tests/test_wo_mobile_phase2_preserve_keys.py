"""
tests/test_wo_mobile_phase2_preserve_keys.py — WO-MOBILE-PHASE2 acceptance tests

AT-1: _PRESERVE_KEYS contains all four Phase-2 embodiment fields
AT-2: A _write() after a boot patch does NOT erase phone_capabilities
AT-3: A _write() after a boot patch does NOT erase embodiment
AT-4: A _write() after a boot patch does NOT erase asleep
AT-5: A _write() after a boot patch does NOT erase travel_intent
"""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch _STATE_PATH to a temp file so we don't touch the live state
import blender_bridge.state_writer as _sw

_FOUR = {"phone_capabilities", "embodiment", "asleep", "travel_intent"}


def _with_temp_state(fn):
    """Context manager: redirect state_writer to a temp file."""
    td = tempfile.mkdtemp()
    fake_path = os.path.join(td, "blender_state.json")
    orig = _sw._STATE_PATH
    _sw._STATE_PATH = fake_path
    try:
        fn(fake_path)
    finally:
        _sw._STATE_PATH = orig
        shutil.rmtree(td, ignore_errors=True)


def test_at1_preserve_keys_contains_four():
    """AT-1: All four Phase-2 fields are in _PRESERVE_KEYS."""
    missing = _FOUR - _sw._PRESERVE_KEYS
    assert not missing, f"Missing from _PRESERVE_KEYS: {missing}"
    print("AT-1 PASS: all four fields in _PRESERVE_KEYS")


def test_at2_phone_capabilities_survives_write():
    """AT-2: phone_capabilities survives a _write() after boot patch."""
    def run(path):
        with open(path, "w") as f:
            json.dump({"phone_capabilities": ["CAP_A", "CAP_B"]}, f)
        _sw._write({"state": {"mode": "idle"}, "expression": {}})
        with open(path) as f:
            data = json.load(f)
        assert "phone_capabilities" in data, "phone_capabilities was erased"
        assert data["phone_capabilities"] == ["CAP_A", "CAP_B"], f"Value changed: {data['phone_capabilities']}"
        print("AT-2 PASS: phone_capabilities survived _write()")
    _with_temp_state(run)


def test_at3_embodiment_survives_write():
    """AT-3: embodiment survives a _write() after boot patch."""
    def run(path):
        with open(path, "w") as f:
            json.dump({"embodiment": "mobile"}, f)
        _sw._write({"state": {"mode": "idle"}})
        with open(path) as f:
            data = json.load(f)
        assert "embodiment" in data, "embodiment was erased"
        assert data["embodiment"] == "mobile", f"Value changed: {data['embodiment']}"
        print("AT-3 PASS: embodiment survived _write()")
    _with_temp_state(run)


def test_at4_asleep_survives_write():
    """AT-4: asleep survives a _write() after boot patch."""
    def run(path):
        with open(path, "w") as f:
            json.dump({"asleep": False}, f)
        _sw._write({"state": {"mode": "idle"}})
        with open(path) as f:
            data = json.load(f)
        assert "asleep" in data, "asleep was erased"
        print("AT-4 PASS: asleep survived _write()")
    _with_temp_state(run)


def test_at5_travel_intent_survives_write():
    """AT-5: travel_intent survives a _write() after boot patch."""
    def run(path):
        with open(path, "w") as f:
            json.dump({"travel_intent": False}, f)
        _sw._write({"state": {"mode": "idle"}})
        with open(path) as f:
            data = json.load(f)
        assert "travel_intent" in data, "travel_intent was erased"
        print("AT-5 PASS: travel_intent survived _write()")
    _with_temp_state(run)


if __name__ == "__main__":
    test_at1_preserve_keys_contains_four()
    test_at2_phone_capabilities_survives_write()
    test_at3_embodiment_survives_write()
    test_at4_asleep_survives_write()
    test_at5_travel_intent_survives_write()
    print("\nAll WO-MOBILE-PHASE2 ATs PASS")
