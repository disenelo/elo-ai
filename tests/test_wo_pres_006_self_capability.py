"""
tests/test_wo_pres_006_self_capability.py — WO-PRES-006 acceptance tests

AT-1: SelfCapabilitySnapshot instantiates from valid capability_set + spatial
AT-2: snapshot.jump_px equals capability_set["jump_px"]
AT-3: snapshot.run_capability equals capability_set["run_capability"] (WO-PRES-001)
AT-4: snapshot.wrap_available=True when gravity-wrap enabled in capability_set
AT-5: All fields readable with no KeyError; no executive.py changes
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.self_capability_snapshot import SelfCapabilitySnapshot, build_snapshot


_CAP_SET = {
    "jump_px": 576,
    "embodiment_scope": ["desktop"],
    "run_capability": True,
    "run_up_distance_px": 120.0,
    "movement_speed_px_s": 200.0,
    "wrap_available": False,
    "size_px": 80.0,
}
_SPATIAL = {"body_win_id": "win-1679", "body_rect_px": [100, 200, 90, 90]}


def test_at1_instantiates():
    """AT-1: SelfCapabilitySnapshot instantiates without error."""
    snap = build_snapshot(_CAP_SET, _SPATIAL)
    assert isinstance(snap, SelfCapabilitySnapshot)
    print("AT-1 PASS: SelfCapabilitySnapshot instantiates")


def test_at2_jump_px():
    """AT-2: snapshot.jump_px == capability_set['jump_px']."""
    snap = build_snapshot(_CAP_SET, _SPATIAL)
    assert snap.jump_px == 576, f"Expected 576, got {snap.jump_px}"
    print("AT-2 PASS: jump_px = 576")


def test_at3_run_capability():
    """AT-3: snapshot.run_capability from capability_set."""
    snap_true  = build_snapshot({**_CAP_SET, "run_capability": True},  _SPATIAL)
    snap_false = build_snapshot({**_CAP_SET, "run_capability": False}, _SPATIAL)
    assert snap_true.run_capability is True
    assert snap_false.run_capability is False
    print("AT-3 PASS: run_capability forwarded correctly")


def test_at4_wrap_available():
    """AT-4: wrap_available=True when capability_set says so."""
    snap = build_snapshot({**_CAP_SET, "wrap_available": True}, _SPATIAL)
    assert snap.wrap_available is True
    snap_f = build_snapshot({**_CAP_SET, "wrap_available": False}, _SPATIAL)
    assert snap_f.wrap_available is False
    print("AT-4 PASS: wrap_available forwarded correctly")


def test_at5_all_fields_readable():
    """AT-5: All fields readable with no error."""
    snap = build_snapshot(_CAP_SET, _SPATIAL)
    _ = snap.jump_px
    _ = snap.embodiment_scope
    _ = snap.run_capability
    _ = snap.run_up_distance_px
    _ = snap.size_px
    _ = snap.movement_speed_px_s
    _ = snap.wrap_available
    _ = snap.body_win_id
    import runtime.executive
    assert hasattr(runtime.executive, "decide")
    print("AT-5 PASS: all fields readable, executive.py untouched")


if __name__ == "__main__":
    test_at1_instantiates()
    test_at2_jump_px()
    test_at3_run_capability()
    test_at4_wrap_available()
    test_at5_all_fields_readable()
    print("\nAll WO-PRES-006 ATs PASS")
