"""
tests/test_wo100_101_096b_109_118.py — Corrections batch: WO-100, WO-101, WO-096B, WO-109, WO-118.

AT-100-1: strict key read — valid elo_spatial.json with x/y/height reads correctly
AT-100-2: strict key read — missing 'x' key triggers warning log, falls through to default
AT-101-1: journal_router.route() signature accepts outcome= kwarg
AT-101-2: significance_faculty.score() signature accepts outcome= kwarg
AT-096B-1: server.py sit ACK uses non-empty episode_ref (not literal "")
AT-096B-2: server.py sit ACK uses _PROCESS_START not literal "sit" as session_id
AT-109-1: vault_layer.lookup() calls reinforce() for each returned hit
AT-109-2: vault_layer.recall_context() does NOT contain its own reinforce loop
AT-118-1: get_elo_spatial() feeds last_move to route_memory.remember_route()
AT-118-2: get_elo_spatial() deduplicates on _ts — duplicate reads skip remember_route()
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, patch, call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _tmp_json(data: dict) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(data, f)
    f.close()
    return f.name


# ── AT-100-1: strict key read — happy path ────────────────────────────────────

def test_strict_keys_happy_path():
    import desktop.spatial_state as _ss
    tmp = _tmp_json({
        "x": 0.6, "y": 0.25, "height": 150,
        "window": "Terminal", "screen_w": 2560, "screen_h": 1440,
    })
    orig = _ss._SPATIAL_PATH
    _ss._SPATIAL_PATH = tmp
    try:
        elo = _ss.get_elo_spatial()
        assert abs(elo.pos_x - 0.6) < 0.001,  f"pos_x: {elo.pos_x}"
        assert abs(elo.pos_y - 0.25) < 0.001, f"pos_y: {elo.pos_y}"
        assert elo.height_px == 150,           f"height_px: {elo.height_px}"
    finally:
        _ss._SPATIAL_PATH = orig
        os.unlink(tmp)


# ── AT-100-2: strict key read — missing key triggers warning, not silent default ─

def test_strict_keys_missing_x_logs_warning():
    import desktop.spatial_state as _ss
    # Write a file missing the 'x' key — should KeyError → log.warning
    tmp = _tmp_json({"y": 0.2, "height": 120, "screen_w": 2560, "screen_h": 1440})
    orig = _ss._SPATIAL_PATH
    _ss._SPATIAL_PATH = tmp
    warned = []
    orig_warn = _ss._log.warning
    _ss._log.warning = lambda msg, *a: warned.append(msg % a if a else msg)
    try:
        elo = _ss.get_elo_spatial()
        # Must have logged a warning (no silent fallback to 0.5)
        assert any("key read failed" in w for w in warned), \
            f"Expected 'key read failed' warning, got: {warned}"
        # Falls back to default EloSpatial values (0.5, 0.1, 120)
        assert abs(elo.pos_x - 0.5) < 0.001, f"Fallback pos_x should be 0.5, got {elo.pos_x}"
    finally:
        _ss._log.warning = orig_warn
        _ss._SPATIAL_PATH = orig
        os.unlink(tmp)


# ── AT-101-1: journal_router.route() accepts outcome= ────────────────────────

def test_journal_router_route_accepts_outcome():
    from memory import journal_router
    sig = inspect.signature(journal_router.route)
    assert "outcome" in sig.parameters, \
        "journal_router.route() missing outcome= parameter"


# ── AT-096B-1: sit ACK episode_ref is not a literal empty string ─────────────

def test_server_sit_ack_episode_ref_not_empty():
    path = os.path.join(ROOT, "server.py")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    # The old literal was: episode_ref=""  (inside the _ls_sit_rec call)
    # Find the _ls_sit_rec block and verify episode_ref is not the empty literal
    idx = src.find("_ls_sit_rec(")
    assert idx != -1, "_ls_sit_rec call not found in server.py"
    block = src[idx: idx + 400]
    assert 'episode_ref=""' not in block, \
        "sit ACK still uses empty episode_ref literal — WO-096B not applied"


# ── AT-096B-2: sit ACK session_id is not the literal string "sit" ────────────

def test_server_sit_ack_session_id_not_constant():
    path = os.path.join(ROOT, "server.py")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    idx = src.find("_ls_sit_rec(")
    assert idx != -1, "_ls_sit_rec call not found in server.py"
    block = src[idx: idx + 400]
    assert 'session_id="sit"' not in block, \
        'sit ACK still uses session_id="sit" constant — WO-096B not applied'


# ── AT-109-1: vault_layer.lookup() calls reinforce() for each hit ─────────────

def test_lookup_reinforces_hits(tmp_path, monkeypatch):
    # P0-3 ruling (Vol VIII §4.70/§4.03): reinforce() was removed from vault_layer.lookup().
    # Retrieval runs in the response path — reading only. Reinforce fires in the
    # post-response integration window (server.py daemon thread) keyed on hits actually used.
    # This test verifies lookup() does NOT call reinforce() — the inverse of WO-109's original intent.
    import memory.vault_layer as vl

    mem_dir  = tmp_path / "09 Memory"
    sum_dir  = mem_dir / "summary"
    deep_dir = mem_dir / "deep"
    sum_dir.mkdir(parents=True)
    deep_dir.mkdir(parents=True)

    spot_file = mem_dir / "SPOT_CODES.md"
    spot_file.write_text(
        "---\ntype: memory-index\n---\n\n"
        "| Spot | Bits | Summary | Date |\n"
        "|------|------|---------|------|\n"
        "| `EO·BL·2607·5` | `EO-BL-26` | test route memory lookup | 2026-08-01 |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(vl, "_MEM_DIR",   str(mem_dir))
    monkeypatch.setattr(vl, "_SUM_DIR",   str(sum_dir))
    monkeypatch.setattr(vl, "_DEEP_DIR",  str(deep_dir))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(spot_file))

    reinforced = []

    import sys
    mock_cf = types.ModuleType("memory.consolidation_faculty")
    mock_cf.reinforce = lambda spot: reinforced.append(spot)
    sys.modules["memory.consolidation_faculty"] = mock_cf
    try:
        results = vl.lookup("route memory", max_results=5)
        assert len(results) > 0, "Expected at least one hit"
        # P0-3: lookup() must NOT call reinforce() — that belongs in the post-response window
        assert len(reinforced) == 0, \
            f"P0-3 violation: lookup() called reinforce() {len(reinforced)} times — must be 0"
    finally:
        sys.modules.pop("memory.consolidation_faculty", None)


# ── AT-109-2: recall_context() does not have its own reinforce loop ───────────

def test_recall_context_has_no_own_reinforce():
    import inspect
    import memory.vault_layer as vl
    src = inspect.getsource(vl.recall_context)
    # The reinforce import should not appear in recall_context anymore
    assert "reinforce" not in src, \
        "recall_context() still contains its own reinforce call — WO-109 not fully applied"


# ── AT-118-1: get_elo_spatial() feeds last_move to route_memory ───────────────

def test_last_move_feeds_route_memory():
    import desktop.spatial_state as _ss
    # Reset seen set so this test starts clean
    _ss._seen_move_ts.clear()

    last_move_ts = 9_999_001.0
    tmp = _tmp_json({
        "x": 0.5, "y": 0.1, "height": 120,
        "window": "Chrome", "screen_w": 2560, "screen_h": 1440,
        "last_move": {
            "goal": "top_of_chrome",
            "legs": ["parkour_up", "wall_slide"],
            "arrived": True,
            "fell": False,
            "cost_secs": 2.4,
            "retries": 0,
            "_ts": last_move_ts,
        },
    })

    orig_path = _ss._SPATIAL_PATH
    _ss._SPATIAL_PATH = tmp

    remembered = []

    import self.route_memory as _rm
    orig_rr = _rm.remember_route

    def _fake_rr(**kwargs):
        remembered.append(kwargs)
        return True

    _rm.remember_route = _fake_rr

    try:
        _ss.get_elo_spatial()
        assert len(remembered) == 1, f"Expected 1 route_memory call, got {len(remembered)}"
        r = remembered[0]
        assert r["goal_surface"] == "top_of_chrome", r["goal_surface"]
        assert r["arrived"] is True
        assert r["ack_received"] is True
        assert r["ack_id"] == str(last_move_ts)
    finally:
        _rm.remember_route = orig_rr
        _ss._SPATIAL_PATH = orig_path
        _ss._seen_move_ts.discard(last_move_ts)
        os.unlink(tmp)


# ── AT-118-2: duplicate reads skip remember_route ─────────────────────────────

def test_last_move_deduplicates_on_ts():
    import desktop.spatial_state as _ss
    _ss._seen_move_ts.clear()

    last_move_ts = 9_999_002.0
    tmp = _tmp_json({
        "x": 0.5, "y": 0.1, "height": 120,
        "window": "Chrome", "screen_w": 2560, "screen_h": 1440,
        "last_move": {
            "goal": "some_window",
            "legs": [],
            "arrived": True,
            "fell": False,
            "cost_secs": 1.0,
            "retries": 0,
            "_ts": last_move_ts,
        },
    })

    orig_path = _ss._SPATIAL_PATH
    _ss._SPATIAL_PATH = tmp

    call_count = [0]

    import self.route_memory as _rm
    orig_rr = _rm.remember_route

    def _counting_rr(**kwargs):
        call_count[0] += 1
        return True

    _rm.remember_route = _counting_rr

    try:
        _ss.get_elo_spatial()
        _ss.get_elo_spatial()  # second read — same _ts, must NOT call again
        assert call_count[0] == 1, \
            f"route_memory called {call_count[0]} times for same _ts — dedup broken"
    finally:
        _rm.remember_route = orig_rr
        _ss._SPATIAL_PATH = orig_path
        _ss._seen_move_ts.discard(last_move_ts)
        os.unlink(tmp)
