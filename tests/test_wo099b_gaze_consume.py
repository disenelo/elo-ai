"""
tests/test_wo099b_gaze_consume.py — WO-099 Builder C: gaze awareness UP.

AT-GAZE-1: get_elo_spatial() reads Unity key names (x/y/height, not pos_x/pos_y/height_px)
AT-GAZE-2: get_elo_spatial() parses gaze field and populates GazeSpatial
AT-GAZE-3: spatial_summary() includes gaze window when on_window=True (verified speech)
AT-GAZE-4: spatial_summary() does NOT claim gaze when gaze is None (no fabrication)
AT-GAZE-5: consume_gaze_events() reads gaze_target_changed from unity_events.json
AT-GAZE-6: LiveWorldState.gaze populated from elo_spatial.json
AT-GAZE-7: describe_gaze() returns verified string for on_window event, "" for missing
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _tmp_json(data: dict) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(data, f)
    f.close()
    return f.name


# ── AT-GAZE-1: Unity key names (x/y/height not pos_x/pos_y/height_px) ────────

def test_get_elo_spatial_reads_unity_key_names():
    from desktop.spatial_state import get_elo_spatial, EloSpatial, _SPATIAL_PATH
    import desktop.spatial_state as _ss_mod

    tmp = _tmp_json({
        "x": 0.7, "y": 0.3, "height": 200,
        "window": "Xcode", "edge": "top",
        "screen_w": 2560, "screen_h": 1440,
    })
    orig = _ss_mod._SPATIAL_PATH
    _ss_mod._SPATIAL_PATH = tmp
    try:
        elo = get_elo_spatial()
        assert abs(elo.pos_x - 0.7) < 0.001, f"pos_x wrong: {elo.pos_x}"
        assert abs(elo.pos_y - 0.3) < 0.001, f"pos_y wrong: {elo.pos_y}"
        assert elo.height_px == 200, f"height_px wrong: {elo.height_px}"
        assert elo.window == "Xcode"
        assert elo.edge == "top"
    finally:
        _ss_mod._SPATIAL_PATH = orig
        os.unlink(tmp)


# ── AT-GAZE-2: gaze field parsed into GazeSpatial ────────────────────────────

def test_get_elo_spatial_parses_gaze():
    import desktop.spatial_state as _ss_mod
    from desktop.spatial_state import get_elo_spatial

    tmp = _tmp_json({
        "x": 0.6, "y": 0.2, "height": 120,
        "window": "Terminal", "screen_w": 2560, "screen_h": 1440,
        "gaze": {
            "x": 0.35, "y": 0.59,
            "win_id": 77856, "window": "Claude",
            "on_window": True, "issued_by": "reflex",
        },
    })
    orig = _ss_mod._SPATIAL_PATH
    _ss_mod._SPATIAL_PATH = tmp
    try:
        elo = get_elo_spatial()
        assert elo.gaze is not None, "gaze should be parsed"
        assert abs(elo.gaze.x - 0.35) < 0.001
        assert elo.gaze.window == "Claude"
        assert elo.gaze.on_window is True
        assert elo.gaze.issued_by == "reflex"
        assert elo.gaze.win_id == 77856
    finally:
        _ss_mod._SPATIAL_PATH = orig
        os.unlink(tmp)


# ── AT-GAZE-3: spatial_summary includes gaze when on_window=True ─────────────

def test_spatial_summary_includes_gaze_window():
    from desktop.spatial_state import EloSpatial, GazeSpatial, spatial_summary

    elo = EloSpatial(
        pos_x=0.6, pos_y=0.2, window="Terminal",
        gaze=GazeSpatial(x=0.35, y=0.59, window="Claude", on_window=True, issued_by="reflex"),
    )
    summary = spatial_summary(elo, [])
    assert "Claude" in summary, f"spatial_summary must mention gaze window; got: {summary}"
    assert "gaze" in summary.lower(), f"spatial_summary must say 'gaze'; got: {summary}"


# ── AT-GAZE-4: no fabrication — gaze None → no gaze claim ────────────────────

def test_spatial_summary_no_gaze_claim_when_absent():
    from desktop.spatial_state import EloSpatial, spatial_summary

    elo = EloSpatial(pos_x=0.5, pos_y=0.1, window="Finder", gaze=None)
    summary = spatial_summary(elo, [])
    assert "gaze" not in summary.lower(), (
        f"spatial_summary must NOT claim gaze when gaze is None; got: {summary}"
    )


# ── AT-GAZE-5: consume_gaze_events reads gaze_target_changed ─────────────────

def test_consume_gaze_events_reads_event():
    from faculties.window_event_faculty import consume_gaze_events

    event_data = {
        "type": "gaze_target_changed",
        "win_id": 54676,
        "on_window": True,
        "window": "VS Code",
        "gaze": {"x": 0.77, "y": 0.04},
        "issued_by": "reflex",
        "_ts": 1786644332.073,
    }
    tmp = _tmp_json(event_data)
    try:
        events = consume_gaze_events(events_path=tmp)
        assert len(events) == 1, f"Expected 1 gaze event, got {len(events)}"
        assert events[0]["type"] == "gaze_target_changed"
        assert events[0]["window"] == "VS Code"
    finally:
        os.unlink(tmp)


# ── AT-GAZE-6: LiveWorldState.gaze populated from elo_spatial.json ───────────

def test_live_world_state_gaze_populated():
    # Evict any stub world.live_world_state that canon_vii tests may have planted
    for _k in [k for k in sys.modules if "world.live_world_state" in k]:
        del sys.modules[_k]
    from world.live_world_state import assemble_world_state, GazeState
    import world.live_world_state as _lws_mod

    tmp = _tmp_json({
        "x": 0.4, "y": 0.5, "height": 120,
        "window": "Finder", "screen_w": 2560, "screen_h": 1440,
        "gaze": {
            "x": 0.4, "y": 0.5,
            "win_id": 12345, "window": "Finder",
            "on_window": True, "issued_by": "brain",
        },
    })
    orig = _lws_mod._SPATIAL_PATH
    _lws_mod._SPATIAL_PATH = tmp
    try:
        world = assemble_world_state(turn_id="test-gaze")
        assert world.gaze is not None, "LiveWorldState.gaze must be populated from elo_spatial.json"
        assert isinstance(world.gaze, GazeState)
        assert world.gaze.window == "Finder"
        assert world.gaze.on_window is True
        assert world.gaze.issued_by == "brain"
        assert world.domain_health.get("gaze", {}).get("status") == "live"
    finally:
        _lws_mod._SPATIAL_PATH = orig
        os.unlink(tmp)


# ── AT-GAZE-7: describe_gaze returns verified string ─────────────────────────

def test_describe_gaze_verified_speech():
    from faculties.window_event_faculty import describe_gaze

    ev_on = {
        "type": "gaze_target_changed",
        "on_window": True,
        "window": "Terminal",
        "issued_by": "reflex",
        "gaze": {"x": 0.5, "y": 0.5},
    }
    result = describe_gaze(ev_on)
    assert "Terminal" in result, f"describe_gaze must name the window; got: '{result}'"

    ev_off = {
        "type": "gaze_target_changed",
        "on_window": False,
        "gaze": {"x": 0.5, "y": 0.5},
    }
    result_off = describe_gaze(ev_off)
    assert result_off == "", f"describe_gaze must return '' when not on_window; got: '{result_off}'"

    result_none = describe_gaze({})
    assert result_none == "", f"describe_gaze({{}}) must return ''; got: '{result_none}'"


# ── Self-runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _tests = [
        ("AT-GAZE-1", test_get_elo_spatial_reads_unity_key_names),
        ("AT-GAZE-2", test_get_elo_spatial_parses_gaze),
        ("AT-GAZE-3", test_spatial_summary_includes_gaze_window),
        ("AT-GAZE-4", test_spatial_summary_no_gaze_claim_when_absent),
        ("AT-GAZE-5", test_consume_gaze_events_reads_event),
        ("AT-GAZE-6", test_live_world_state_gaze_populated),
        ("AT-GAZE-7", test_describe_gaze_verified_speech),
    ]
    _passed = 0
    _failed = 0
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
    print(f"WO-099b gaze consume   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
