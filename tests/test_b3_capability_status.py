"""
B3 — tools/capability_status.py + the {success, result, error} standard.
Wiring tests (offline; live probes stubbed). Not live evidence.
"""
import pytest

from tools import capability_status as cs



@pytest.fixture(autouse=True)
def _never_speak(monkeypatch):
    """Tests must never make eLo talk on David's Mac (pre_ack / voice_engine)."""
    import runtime.pre_ack as _pa, voice.voice_engine as _ve
    if not getattr(_pa.emit, "_b3_test_stub", False):
        monkeypatch.setattr(_pa, "emit", lambda *a, **k: None)
    monkeypatch.setattr(_ve, "speak", lambda *a, **k: None)
    monkeypatch.setattr(_ve, "speak_inner", lambda *a, **k: None)
    monkeypatch.setattr(_ve, "is_speaking", lambda: False)

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


@pytest.mark.parametrize("t", ["can you open a scene in Blender and render it", "can you connect to your robot body",
                               "what does the robot camera see", "can you start the heat press",
                               "can you run a shell command for me"])
def test_not_built_is_an_honest_no(t, monkeypatch):
    import runtime.capabilities.registry  # noqa: F401  (real registry: these are future)
    line = cs.not_built_answer(t)
    assert line and ("Not yet" in line or "Can't do that one yet" in line)


@pytest.mark.parametrize("t", ["I love Blender", "my robot vacuum is broken", "what's the weather like"])
def test_mentions_are_not_refused(t):
    assert cs.not_built_answer(t) is None


# ── devices live probe (WO-B3-0011, 2026-10-11) ────────────────────────────────

def test_devices_live_entry_marks_speak_route_inactive_without_echo(monkeypatch):
    import tools.device_control as dc
    import tools.echo_speaker as es
    monkeypatch.setattr(dc, "_route", lambda: "speak")
    monkeypatch.setattr(dc, "controllable", lambda: ["Lights On", "Lights Out"])
    monkeypatch.setattr(es, "device_index", lambda fresh=False: None)
    cs._cache.update(ts=0.0, data=None)
    caps = cs.get_active_capabilities(refresh=True)
    d = caps["devices"]
    assert d["status"] == "INACTIVE"
    assert "Bluetooth" in (d["reason"] or "")
    assert d["live"]["route"] == "speak" and d["live"]["echo_connected"] is False


def test_devices_live_entry_marks_speak_route_active_with_echo(monkeypatch):
    import tools.device_control as dc
    import tools.echo_speaker as es
    monkeypatch.setattr(dc, "_route", lambda: "speak")
    monkeypatch.setattr(dc, "controllable", lambda: ["Lights On", "Lights Out"])
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 7)
    cs._cache.update(ts=0.0, data=None)
    caps = cs.get_active_capabilities(refresh=True)
    d = caps["devices"]
    assert d["status"] == "ACTIVE" and d["live"]["echo_connected"] is True


def test_devices_live_entry_shortcut_route_is_active_when_anything_listed(monkeypatch):
    import tools.device_control as dc
    monkeypatch.setattr(dc, "_route", lambda: "shortcut")
    monkeypatch.setattr(dc, "controllable", lambda: ["Lights On"])
    cs._cache.update(ts=0.0, data=None)
    caps = cs.get_active_capabilities(refresh=True)
    assert caps["devices"]["status"] == "ACTIVE"


def test_devices_appear_in_live_first_block(monkeypatch):
    import tools.device_control as dc
    import tools.echo_speaker as es
    monkeypatch.setattr(dc, "_route", lambda: "speak")
    monkeypatch.setattr(dc, "controllable", lambda: ["Lights On", "Lights Out"])
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 9)
    cs._cache.update(ts=0.0, data=None)
    b = cs.capabilities_block()
    assert "Devices — via Alexa over the Mac speakers" in b or "Devices — via macOS Shortcuts" in b


def test_devices_status_shape():
    r = cs.devices_status()
    assert set(r) == {"success", "result", "error"}
    assert set(r["result"]) >= {"route", "controllable", "echo_connected", "can"}
