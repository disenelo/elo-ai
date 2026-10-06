"""
B3 — tools/capability_status.py + the {success, result, error} standard.
Wiring tests (offline; live probes stubbed). Not live evidence.
"""
import pytest

from tools import capability_status as cs


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(cs, "spotify_status", lambda: cs.tool_result(True, {
        "state": "playing", "track": "Somebody to Love", "artist": "Jefferson Airplane",
        "device": "Mac", "can": ["pause", "resume", "skip"]}))
    monkeypatch.setattr(cs, "_presence_running", lambda: False)
    monkeypatch.delenv("ALEXA_SKILL_ID", raising=False)
    cs._cache.update(ts=0.0, data=None)


def test_tool_result_shape():
    assert cs.tool_result(True, {"x": 1}) == {"success": True, "result": {"x": 1}, "error": None}
    assert cs.tool_result(0, None, "boom") == {"success": False, "result": None, "error": "boom"}


def test_every_registry_capability_has_a_status():
    from runtime.capabilities.registry import ALL_CAPABILITIES
    caps = cs.get_active_capabilities(refresh=True)
    for c in ALL_CAPABILITIES:
        assert caps[c.id]["status"] in ("ACTIVE", "INACTIVE")


def test_live_overlay_reflects_state():
    caps = cs.get_active_capabilities(refresh=True)
    assert caps["spotify"]["status"] == "ACTIVE"
    assert caps["spotify"]["live"]["state"] == "playing"
    assert caps["alexa_ingress"]["status"] == "INACTIVE" and caps["alexa_ingress"]["reason"]
    assert caps["show_brain"]["status"] == "INACTIVE"


def test_block_leads_with_live_spotify_and_fits():
    b = cs.capabilities_block()
    assert len(b) <= 1600
    first_line = b.splitlines()[1]
    assert first_line.startswith("You CAN: Spotify — now playing: Somebody to Love by Jefferson Airplane")


def test_results_are_recorded_newest_last():
    cs.record_result("spotify", cs.tool_result(False, {"line": "x"}, "nothing playing"))
    cs.record_result("web_search", cs.tool_result(True, {"line": "y"}))
    last = cs.last_results()[-2:]
    assert [r["tool"] for r in last] == ["spotify", "web_search"]
    assert last[0]["success"] is False and last[0]["error"] == "nothing playing"
