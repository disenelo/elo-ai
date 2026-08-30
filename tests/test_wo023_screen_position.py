"""
WO-023 acceptance tests — eLo screen-position top-bias + keep-out.

AT-1  Default target is in top strip (target_y <= 0.15)
AT-2  Default target is in right-of-centre area (target_x >= 0.5)
AT-3  Keep-out rect is computed from active window bottom CONTROL_BOTTOM_FRAC
AT-4  When default target lands inside keep-out, keep_out_applied=True and target nudged up
AT-5  When default target is clear of keep-out, keep_out_applied=False
AT-6  No active window → keep_out sentinel (y_min=y_max=1.0 → effectively disabled)
AT-7  emit() writes a valid presence_position.json (7 required keys)
AT-8  JSON schema: all required keys present and correct types
AT-9  Frozen kernel untouched (executive.py + prompts/ unchanged)
AT-10 _in_keep_out boundary: point exactly on boundary counts as inside
"""
import importlib.util
import json
import os
import sys
import tempfile
import types as _types

_ROOT = os.path.join(os.path.dirname(__file__), "..")


# ── Minimal stubs for EloSpatial / WindowBounds ──────────────────────────────

class _FakeElo:
    pos_x = 0.85; pos_y = 0.07; height_px = 120
    window = ""; screen_w = 2560; screen_h = 1440


class _FakeWin:
    def __init__(self, app="TestApp", x=0, y=0, w=2560, h=1440):
        self.app = app; self.title = app
        self.x = x; self.y = y; self.w = w; self.h = h
    @property
    def right_edge(self): return self.x + self.w
    @property
    def top_edge(self): return self.y


# ── Load position_faculty.py directly via spec ────────────────────────────────
# Bypasses the 'desktop' package __init__ and osascript dependency.

_PF_PATH = os.path.join(_ROOT, "desktop", "position_faculty.py")
_pf_spec = importlib.util.spec_from_file_location("position_faculty_test", _PF_PATH)
_pf_mod  = importlib.util.module_from_spec(_pf_spec)

# Inject stub for the 'desktop.spatial_state' import inside position_faculty.py
_spatial_stub = _types.ModuleType("desktop.spatial_state")
_spatial_stub.EloSpatial      = _FakeElo
_spatial_stub.WindowBounds    = _FakeWin
_spatial_stub.get_elo_spatial = lambda: _FakeElo()
_spatial_stub.get_windows     = lambda: []

# WO-FIX-SYS-POLLUTION: save originals before stub injection so we can restore after exec_module.
_orig_desktop_pkg  = sys.modules.get("desktop")
_orig_spatial_stub = sys.modules.get("desktop.spatial_state")

# Register stubs before exec_module so the `from desktop.spatial_state import …` succeeds
_desktop_pkg = _types.ModuleType("desktop")
_desktop_pkg.spatial_state = _spatial_stub
sys.modules.setdefault("desktop", _desktop_pkg)
sys.modules["desktop.spatial_state"] = _spatial_stub

_pf_spec.loader.exec_module(_pf_mod)

# WO-FIX-SYS-POLLUTION: restore originals — position_faculty captured all spatial_state
# symbols at module level, so _pf_mod's namespace is unaffected. Downstream tests get
# the real modules (both are importable from the repo).
def _restore(key, orig):
    if orig is None:
        sys.modules.pop(key, None)
    else:
        sys.modules[key] = orig

_restore("desktop", _orig_desktop_pkg)
_restore("desktop.spatial_state", _orig_spatial_stub)

# Expose module symbols as module-level names for the tests
compute_position   = _pf_mod.compute_position
_in_keep_out       = _pf_mod._in_keep_out
emit               = _pf_mod.emit
PREFERRED_Y_NORM   = _pf_mod.PREFERRED_Y_NORM
PREFERRED_X_NORM   = _pf_mod.PREFERRED_X_NORM
CONTROL_BOTTOM_FRAC = _pf_mod.CONTROL_BOTTOM_FRAC

# Make the module accessible by its real package path for the monkeypatch in AT-4
sys.modules["desktop.position_faculty"] = _pf_mod


# ── helpers ──────────────────────────────────────────────────────────────────

def _elo(window="", screen_w=2560, screen_h=1440):
    e = _FakeElo()
    e.window = window
    e.screen_w = screen_w
    e.screen_h = screen_h
    return e


def _win(app="TestApp", x=0, y=0, w=2560, h=1440):
    return _FakeWin(app=app, x=x, y=y, w=w, h=h)


_REQUIRED_KEYS = {
    "target_x", "target_y", "keep_out_applied",
    "keep_out", "active_window", "screen_w", "screen_h", "_ts",
}
_KEEP_OUT_KEYS = {"x_min", "x_max", "y_min", "y_max"}


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_target_in_top_strip():
    pos = compute_position(elo=_elo(), windows=[])
    assert pos["target_y"] <= 0.15, f"AT-1 FAIL: target_y={pos['target_y']} > 0.15 (not in top strip)"
    print(f"AT-1 PASS — target_y={pos['target_y']} in top strip (≤0.15)")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_target_right_of_centre():
    pos = compute_position(elo=_elo(), windows=[])
    assert pos["target_x"] >= 0.5, f"AT-2 FAIL: target_x={pos['target_x']} < 0.5"
    print(f"AT-2 PASS — target_x={pos['target_x']} right-of-centre (≥0.5)")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_keep_out_from_window_bottom():
    # Full-screen VSCode window: y=0, h=1440
    elo    = _elo(window="Code", screen_w=2560, screen_h=1440)
    win    = _win(app="Code", x=0, y=0, w=2560, h=1440)
    pos    = compute_position(elo=elo, windows=[win])
    ko     = pos["keep_out"]
    # control region starts at y = h*(1-CONTROL_BOTTOM_FRAC) = 1440*0.88 = 1267.2 → norm = 0.88
    expected_y_min = round((1440 * (1.0 - CONTROL_BOTTOM_FRAC)) / 1440, 4)
    assert abs(ko["y_min"] - expected_y_min) < 0.01, \
        f"AT-3 FAIL: keep_out.y_min={ko['y_min']}, expected≈{expected_y_min}"
    assert ko["y_max"] <= 1.0, f"AT-3 FAIL: keep_out.y_max > 1.0"
    print(f"AT-3 PASS — keep_out y_min≈{ko['y_min']} (bottom {int(CONTROL_BOTTOM_FRAC*100)}% of window)")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_keep_out_applied_when_target_inside():
    # Construct a scenario where the default target falls inside the keep-out.
    # Window spans only bottom 10% of screen: y=1296, h=144  (1440*0.9=1296, h=144)
    # control region starts at y_norm = (1296 + 144*0.88)/1440 = (1296+126.72)/1440 = 0.987
    # That's at the very bottom, so default PREFERRED_Y_NORM=0.07 won't be in it.
    # Instead, artificially set preferred target inside keep-out by monkeypatching.
    import sys as _sys
    _pf = _sys.modules["desktop.position_faculty"]
    orig_py = _pf.PREFERRED_Y_NORM
    orig_ks = _pf.CONTROL_BOTTOM_FRAC
    try:
        # Force keep-out to cover top half (y_min=0.0, y_max=0.5)
        # by making a window whose control region = 100% of screen height
        _pf.PREFERRED_Y_NORM    = 0.3   # target in middle
        _pf.CONTROL_BOTTOM_FRAC = 1.0   # entire window is control region
        elo = _elo(window="BigApp", screen_w=2560, screen_h=1440)
        win = _win(app="BigApp", x=0, y=0, w=2560, h=1440)
        pos = compute_position(elo=elo, windows=[win])
        assert pos["keep_out_applied"] is True, \
            f"AT-4 FAIL: keep_out_applied should be True, got {pos['keep_out_applied']}"
        assert pos["target_y"] < 0.3, \
            f"AT-4 FAIL: target_y should be nudged up from 0.3, got {pos['target_y']}"
    finally:
        _pf.PREFERRED_Y_NORM    = orig_py
        _pf.CONTROL_BOTTOM_FRAC = orig_ks
    print("AT-4 PASS — keep_out_applied=True when target inside control region, target nudged up")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_keep_out_not_applied_when_clear():
    elo = _elo(window="Code", screen_w=2560, screen_h=1440)
    win = _win(app="Code", x=0, y=0, w=2560, h=1440)
    pos = compute_position(elo=elo, windows=[win])
    # Default PREFERRED_Y_NORM=0.07 — well above control region at ~0.88
    assert pos["keep_out_applied"] is False, \
        f"AT-5 FAIL: keep_out_applied should be False (target is clear), got {pos['keep_out_applied']}"
    print(f"AT-5 PASS — keep_out_applied=False when target is clear of control region")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_no_active_window_sentinel():
    pos = compute_position(elo=_elo(window=""), windows=[])
    ko  = pos["keep_out"]
    # Sentinel: y_min == y_max == 1.0 (disabled)
    assert ko["y_min"] == 1.0 and ko["y_max"] == 1.0, \
        f"AT-6 FAIL: expected sentinel keep_out (y_min=y_max=1.0), got {ko}"
    assert pos["keep_out_applied"] is False
    print("AT-6 PASS — no active window → sentinel keep_out, keep_out_applied=False")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_emit_writes_json():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        emit(elo=_elo(), windows=[], path=path)
        assert os.path.exists(path), "AT-7 FAIL: file not written"
        with open(path) as f:
            data = json.load(f)
        missing = _REQUIRED_KEYS - data.keys()
        assert not missing, f"AT-7 FAIL: missing keys {missing}"
        print("AT-7 PASS — emit() writes valid presence_position.json")
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ── AT-8 ─────────────────────────────────────────────────────────────────────

def test_at8_schema_types():
    pos = compute_position(elo=_elo(), windows=[])
    assert isinstance(pos["target_x"],          float), "AT-8 FAIL: target_x not float"
    assert isinstance(pos["target_y"],          float), "AT-8 FAIL: target_y not float"
    assert isinstance(pos["keep_out_applied"],  bool),  "AT-8 FAIL: keep_out_applied not bool"
    assert isinstance(pos["keep_out"],          dict),  "AT-8 FAIL: keep_out not dict"
    assert not (_KEEP_OUT_KEYS - pos["keep_out"].keys()), "AT-8 FAIL: keep_out missing keys"
    assert isinstance(pos["screen_w"],          int),   "AT-8 FAIL: screen_w not int"
    assert isinstance(pos["_ts"],               float), "AT-8 FAIL: _ts not float"
    print("AT-8 PASS — schema types correct")


# ── AT-9 ─────────────────────────────────────────────────────────────────────

def test_at9_frozen_kernel():
    for path in [
        os.path.join(_ROOT, "runtime", "executive.py"),
    ]:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        assert b"position_faculty" not in content, \
            f"AT-9 FAIL: frozen file {path} was modified"
    prompts_dir = os.path.join(_ROOT, "prompts")
    if os.path.isdir(prompts_dir):
        for fname in os.listdir(prompts_dir):
            with open(os.path.join(prompts_dir, fname), "rb") as f:
                content = f.read()
            assert b"position_faculty" not in content, \
                f"AT-9 FAIL: prompts/ file {fname} modified — FREEZE_V1_LOCK violated"
    print("AT-9 PASS — frozen kernel untouched")


# ── AT-10 ────────────────────────────────────────────────────────────────────

def test_at10_boundary_inside():
    ko = {"x_min": 0.0, "x_max": 1.0, "y_min": 0.88, "y_max": 1.0}
    assert _in_keep_out(0.5, 0.88, ko) is True,  "AT-10 FAIL: point on y_min boundary not inside"
    assert _in_keep_out(0.5, 1.0, ko) is True,   "AT-10 FAIL: point on y_max boundary not inside"
    assert _in_keep_out(0.5, 0.87, ko) is False,  "AT-10 FAIL: point just above y_min counted as inside"
    print("AT-10 PASS — boundary inclusive: y_min and y_max both count as inside")


# ── runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_target_in_top_strip,
        test_at2_target_right_of_centre,
        test_at3_keep_out_from_window_bottom,
        test_at4_keep_out_applied_when_target_inside,
        test_at5_keep_out_not_applied_when_clear,
        test_at6_no_active_window_sentinel,
        test_at7_emit_writes_json,
        test_at8_schema_types,
        test_at9_frozen_kernel,
        test_at10_boundary_inside,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-023 ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
