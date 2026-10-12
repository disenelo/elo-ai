"""WO-B3-0016: direct Tuya LAN control. Offline: tinytuya devices faked; no packets sent."""
import json
import pytest
import tools.tuya_agent as ta
import tools.device_control as dc


class _Dev:
    calls = []
    def __init__(self, *a): pass
    def set_version(self, v): pass
    def set_socketTimeout(self, t): pass
    def turn_on(self): _Dev.calls.append("on"); return {"dps": {"20": True}}
    def turn_off(self): _Dev.calls.append("off"); return {"dps": {"20": False}}


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    import tinytuya
    monkeypatch.setattr(tinytuya, "BulbDevice", _Dev)
    _Dev.calls = []
    f = tmp_path / "tuya.json"
    monkeypatch.setattr(ta, "_CONFIG", str(f))
    return f


def test_not_configured_is_honest(cfg):
    assert ta.configured() is False
    r = ta.lights_off()
    assert not r["success"] and "set up" in r["result"]["line"]


def test_off_and_on_send_to_every_light(cfg):
    cfg.write_text(json.dumps({"lights": [{"name": "Studio", "id": "a", "ip": "1.2.3.4", "key": "k", "version": 3.5},
                                          {"name": "Lamp", "id": "b", "ip": "1.2.3.5", "key": "k"}]}))
    assert ta.configured()
    r = ta.lights_off()
    assert r["success"] and r["result"]["via"] == "tuya" and _Dev.calls == ["off", "off"]
    assert ta.lights_on()["result"]["line"] == "Lights on."


def test_device_error_reported(cfg, monkeypatch):
    cfg.write_text(json.dumps({"lights": [{"name": "Studio", "id": "a", "ip": "1.2.3.4", "key": "k"}]}))
    monkeypatch.setattr(_Dev, "turn_off", lambda self: {"Error": "Network Error: Device Unreachable"})
    r = ta.lights_off()
    assert not r["success"] and "Unreachable" in r["result"]["line"]


def test_device_control_prefers_tuya_when_configured(cfg, monkeypatch, tmp_path):
    cfg.write_text(json.dumps({"lights": [{"name": "Studio", "id": "a", "ip": "1.2.3.4", "key": "k"}]}))
    monkeypatch.delenv("ELO_DEVICE_ROUTE", raising=False)
    monkeypatch.setattr(dc, "_ALLOW_FILE", str(tmp_path / "x.json"))
    monkeypatch.setattr(dc, "_say_on_mac", lambda t: pytest.fail("no spoken Alexa command when Tuya works"))
    r = dc.run("Lights Out")
    assert r["success"] and r["result"]["via"] == "tuya" and _Dev.calls == ["off"]
