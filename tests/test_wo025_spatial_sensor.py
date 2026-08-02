"""
WO-025 acceptance tests — Perception spatial sensor stub.

AT-1  ELO_SPATIAL_SENSOR=1 → perceive_from_live_state() returns spatial_frame not None
AT-2  ELO_SPATIAL_SENSOR=0 (unset) → spatial_frame is None (flag gate, byte-identical)
AT-3  SpatialFrame validates Vol XV §2 schema: points list, frame_id, ts, source
AT-4  spatial_trace.json is written when sensor is enabled (atomic, required keys)
AT-5  Frame has ≥1 point; each point has x/y/z/conf all floats
AT-6  All point coordinates clamped: x/y/z in [-1, 1]; conf in [0, 1]
AT-7  source_health["spatial"] = "live" when frame present; "absent" when not
AT-8  Frozen kernel untouched (executive.py + prompts/ unchanged)
"""
import importlib.util
import json
import os
import sys
import tempfile
import types as _types

_ROOT    = os.path.join(os.path.dirname(__file__), "..")
_PF_PATH = os.path.join(_ROOT, "faculties", "perception", "perception_faculty.py")

# ── Load module directly — avoids importing desktop.* and blender_bridge.* ───

_spec = importlib.util.spec_from_file_location("perception_faculty_test", _PF_PATH)
_mod  = importlib.util.module_from_spec(_spec)
sys.modules["perception_faculty_test"] = _mod  # required for dataclass __module__ lookup

# Stubs needed by perceive_from_live_state() lazy imports
_desktop_stub = _types.ModuleType("desktop.window_state")
_desktop_stub.get_active_window = lambda: {"app": "Code", "title": "test.py"}
sys.modules.setdefault("desktop", _types.ModuleType("desktop"))
sys.modules["desktop.window_state"] = _desktop_stub

_blender_stub = _types.ModuleType("blender_bridge.state_writer")
_blender_stub.read = lambda: {}
sys.modules.setdefault("blender_bridge", _types.ModuleType("blender_bridge"))
sys.modules["blender_bridge.state_writer"] = _blender_stub

_spec.loader.exec_module(_mod)

perceive               = _mod.perceive
perceive_from_live_state = _mod.perceive_from_live_state
SpatialFrame           = _mod.SpatialFrame
SpatialPoint           = _mod.SpatialPoint
_stub_spatial_frame    = _mod._stub_spatial_frame


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_sensor_enabled():
    orig = os.environ.get("ELO_SPATIAL_SENSOR", "")
    _mod._SPATIAL_TRACE_PATH = os.path.join(tempfile.gettempdir(), "spatial_trace_test.json")
    try:
        os.environ["ELO_SPATIAL_SENSOR"] = "1"
        result = perceive_from_live_state()
        assert result.spatial_frame is not None, "AT-1 FAIL: spatial_frame is None when sensor=1"
        assert isinstance(result.spatial_frame, SpatialFrame), "AT-1 FAIL: wrong type"
    finally:
        if orig:
            os.environ["ELO_SPATIAL_SENSOR"] = orig
        else:
            os.environ.pop("ELO_SPATIAL_SENSOR", None)
    print("AT-1 PASS — ELO_SPATIAL_SENSOR=1 → spatial_frame present")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_sensor_disabled():
    os.environ.pop("ELO_SPATIAL_SENSOR", None)
    result = perceive_from_live_state()
    assert result.spatial_frame is None, \
        f"AT-2 FAIL: spatial_frame should be None when sensor flag off, got {result.spatial_frame}"
    print("AT-2 PASS — ELO_SPATIAL_SENSOR unset → spatial_frame is None (flag gate)")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_frame_schema():
    frame = _stub_spatial_frame()
    d = frame.as_dict()
    assert "points" in d and isinstance(d["points"], list), "AT-3 FAIL: missing/invalid 'points'"
    assert "frame_id" in d and isinstance(d["frame_id"], str) and d["frame_id"], \
        "AT-3 FAIL: missing/empty 'frame_id'"
    assert "ts" in d and isinstance(d["ts"], float), "AT-3 FAIL: missing/invalid 'ts'"
    assert "source" in d and isinstance(d["source"], str), "AT-3 FAIL: missing/invalid 'source'"
    print(f"AT-3 PASS — SpatialFrame schema valid: {len(d['points'])} points, id={d['frame_id']}")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_trace_written():
    tmp = os.path.join(tempfile.gettempdir(), "spatial_trace_at4.json")
    orig_path = _mod._SPATIAL_TRACE_PATH
    orig_env  = os.environ.get("ELO_SPATIAL_SENSOR", "")
    _mod._SPATIAL_TRACE_PATH = tmp
    try:
        os.environ["ELO_SPATIAL_SENSOR"] = "1"
        perceive_from_live_state()
        assert os.path.exists(tmp), "AT-4 FAIL: spatial_trace.json not written"
        with open(tmp, encoding="utf-8") as f:
            trace = json.load(f)
        for key in ("frame_id", "point_count", "source", "_ts"):
            assert key in trace, f"AT-4 FAIL: trace missing key '{key}'"
        assert isinstance(trace["point_count"], int) and trace["point_count"] > 0, \
            "AT-4 FAIL: point_count not positive int"
    finally:
        _mod._SPATIAL_TRACE_PATH = orig_path
        if orig_env:
            os.environ["ELO_SPATIAL_SENSOR"] = orig_env
        else:
            os.environ.pop("ELO_SPATIAL_SENSOR", None)
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(f"AT-4 PASS — spatial_trace.json written with {trace['point_count']} points")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_points_have_required_fields():
    frame = _stub_spatial_frame()
    assert len(frame.points) >= 1, "AT-5 FAIL: no points in stub frame"
    for i, p in enumerate(frame.points):
        for attr in ("x", "y", "z", "conf"):
            assert isinstance(getattr(p, attr), float), \
                f"AT-5 FAIL: point[{i}].{attr} not float"
    print(f"AT-5 PASS — {len(frame.points)} points, all have x/y/z/conf floats")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_coordinates_in_range():
    frame = _stub_spatial_frame()
    for i, p in enumerate(frame.points):
        for axis, v in (("x", p.x), ("y", p.y), ("z", p.z)):
            assert -1.0 <= v <= 1.0, f"AT-6 FAIL: point[{i}].{axis}={v} outside [-1, 1]"
        assert 0.0 <= p.conf <= 1.0, f"AT-6 FAIL: point[{i}].conf={p.conf} outside [0, 1]"
    print("AT-6 PASS — all coordinates in [-1,1]; conf in [0,1]")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_source_health():
    frame  = _stub_spatial_frame()
    result = perceive(window_app="Code", spatial_data=frame)
    assert result.source_health["spatial"]["status"] == "live", \
        f"AT-7 FAIL: spatial health should be 'live', got {result.source_health['spatial']}"

    result2 = perceive(window_app="Code", spatial_data=None)
    assert result2.source_health["spatial"]["status"] == "absent", \
        f"AT-7 FAIL: spatial health should be 'absent', got {result2.source_health['spatial']}"
    print("AT-7 PASS — source_health[spatial] = 'live' / 'absent' correctly")


# ── AT-8 ─────────────────────────────────────────────────────────────────────

def test_at8_frozen_kernel():
    for path in [os.path.join(_ROOT, "runtime", "executive.py")]:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        for token in (b"spatial_sensor", b"SpatialFrame", b"ELO_SPATIAL_SENSOR"):
            assert token not in content, \
                f"AT-8 FAIL: frozen file {path} contains WO-025 token '{token.decode()}'"
    prompts_dir = os.path.join(_ROOT, "prompts")
    if os.path.isdir(prompts_dir):
        for fname in os.listdir(prompts_dir):
            with open(os.path.join(prompts_dir, fname), "rb") as f:
                content = f.read()
            assert b"ELO_SPATIAL_SENSOR" not in content, \
                f"AT-8 FAIL: prompts/{fname} modified — FREEZE_V1_LOCK violated"
    print("AT-8 PASS — frozen kernel untouched")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_sensor_enabled,
        test_at2_sensor_disabled,
        test_at3_frame_schema,
        test_at4_trace_written,
        test_at5_points_have_required_fields,
        test_at6_coordinates_in_range,
        test_at7_source_health,
        test_at8_frozen_kernel,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-025 ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
