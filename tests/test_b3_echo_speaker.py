"""B3 — tools/echo_speaker: finding the Echo as an output, caching, play only when connected. Offline."""
import pytest
from tools import echo_speaker as es


@pytest.fixture(autouse=True)
def _clean(tmp_path, monkeypatch):
    monkeypatch.setattr(es, "_SETTING", str(tmp_path / "voice_output.json"))
    monkeypatch.setattr(es, "_EVENTS", str(tmp_path / "unity_events.json"))
    monkeypatch.setattr(es, "_CONNECT", str(tmp_path / "alexa_connect.json"))
    es._ac_cache.update(ts=0.0, value=None)
    es._vo_cache.update(ts=0.0, value=None)
    es._idx_cache.update(ts=0.0, idx=None); es.stop_wanting(); es.release_voice()
    yield
    es._idx_cache.update(ts=0.0, idx=None); es.stop_wanting(); es._vo_cache.update(ts=0.0, value=None)

LIST = """[AudioToolbox @ 0x1] CoreAudio devices:
[AudioToolbox @ 0x1] [0]            Mac Studio Speakers, BuiltInSpeakerDevice
[AudioToolbox @ 0x1] [1]            Echo Dot-Studio, 28-73-F6-8F-71-E5:output
"""


class _P:
    def __init__(self, err="", out="", rc=0): self.stderr, self.stdout, self.returncode = err, out, rc


def test_device_index_found_and_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(es, "_run", lambda cmd, timeout=10: calls.append(cmd) or _P(err=LIST))
    es._idx_cache.update(ts=0.0, idx=None)
    assert es.device_index() == 1 and es.device_index() == 1 and len(calls) == 1


def test_not_an_output_means_no_play(monkeypatch):
    monkeypatch.setattr(es, "_run", lambda cmd, timeout=10: _P(err=LIST.splitlines()[0]))
    es._idx_cache.update(ts=0.0, idx=None)
    assert es.device_index() is None and es.play("/tmp/x.mp3") is False and es.popen_play("/tmp/x.mp3") is None
    assert es.speaking() is False


def test_off_unless_a_turn_wants_it(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)   # connected
    es.stop_wanting()
    assert es.speaking() is False            # connected alone never routes eLo's voice
    es.want_for(5)
    assert es.speaking() is True
    monkeypatch.setenv("ECHO_SPEAKER", "off")
    assert es.speaking() is False
    es.stop_wanting()


def test_connect_puts_mac_output_back(monkeypatch):
    out = {"now": "Mac Studio Speakers"}
    def run(cmd, timeout=10):
        if cmd[:2] == ["blueutil", "--connect"]:
            out["now"] = "Echo Dot-Studio"          # macOS auto-switch
            return _P()
        if cmd[:1] == ["SwitchAudioSource"] and "-c" in cmd:
            return _P(out=out["now"])
        if cmd[:1] == ["SwitchAudioSource"] and "-s" in cmd:
            out["now"] = cmd[-1]; return _P()
        if cmd[:1] == ["ffmpeg"]:
            return _P(err=LIST)
        return _P()
    monkeypatch.setattr(es, "_run", run)
    monkeypatch.setattr(es, "_address", lambda: "28:73:F6:8F:71:E5")
    monkeypatch.setattr(es.time, "sleep", lambda s: None)
    assert es.connect() is True and out["now"] == "Mac Studio Speakers"


def test_default_is_auto_and_at_desk_means_mac(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)     # Echo connected
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 3.0)            # typing at the desk
    assert es.voice_output() == "auto" and es.speaking() is False
    assert es.output_decision() == ("mac", "auto: David at the desk")


# ── WO-B3-0018: the two Board scenarios + idle + overrides ─────────────────────

def test_scenario_1_desk_mac(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 10.0)
    assert es.output_decision()[0] == "mac"


def test_scenario_2_spoke_through_alexa_echo(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 1.0)           # even if at the desk
    es.want_for(60)
    assert es.output_decision() == ("echo", "David just spoke through Alexa")


def test_away_from_desk_auto_echo(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 900.0)
    assert es.output_decision()[0] == "echo"


def test_mac_override_wins_over_idle(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 900.0)
    es.set_voice_output("mac")
    assert es.output_decision() == ("mac", "setting: Mac")


def test_never_echo_when_not_connected(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: None)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 900.0)
    es.want_for(60)
    assert es.output_decision() == ("mac", "Echo not connected")


def test_presence_setting_event_wins_and_is_remembered(monkeypatch, tmp_path):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 1.0)
    ev = tmp_path / "unity_events.json"
    ev.write_text('{"seq":1,"type":"gaze_target_changed","subject":"1","_ts":1}\n'
                  '{"seq":2,"type":"voice_output","subject":"echo","_ts":100}\n')
    assert es.voice_output() == "echo" and es.speaking() is True
    ev.write_text('{"seq":3,"type":"gaze_target_changed","subject":"2","_ts":200}\n')   # event trimmed away
    es._vo_cache.update(ts=0.0, value=None)
    assert es.voice_output() == "echo"                                   # remembered
    ev.write_text('{"seq":4,"type":"voice_output","subject":"mac","_ts":300}\n')
    es._vo_cache.update(ts=0.0, value=None)
    assert es.voice_output() == "mac" and es.speaking() is False


def test_echo_chosen_but_not_connected_falls_back_to_mac(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: None)
    monkeypatch.setattr(es, "connect", lambda *a, **k: False)
    es.set_voice_output("echo")
    assert es.speaking() is False      # eLo still speaks, on the Mac



# ── Designer ALEXA-CONNECT-BUTTON (2026-10-12) ─────────────────────────────────

def _events(tmp_path, *lines):
    (tmp_path / "unity_events.json").write_text("\n".join(lines) + "\n")
    es._ac_cache.update(ts=0.0, value=None); es._vo_cache.update(ts=0.0, value=None)


def test_presence_alexa_name_means_echo(monkeypatch, tmp_path):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 1.0)
    _events(tmp_path, '{"type":"voice_output","subject":"alexa","_ts":10}')
    assert es.voice_output() == "echo" and es.output_decision() == ("echo", "setting: Alexa speaker")


def test_connect_button_start_then_stop(monkeypatch, tmp_path):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "mac_idle_seconds", lambda: 1.0)          # still "at the desk" when pressed
    _events(tmp_path, '{"type":"alexa_connect","subject":"start","_ts":10}')
    assert es.output_decision() == ("echo", "David pressed connect: he's at the Echo")
    _events(tmp_path, '{"type":"gaze_target_changed","_ts":11}')       # start trimmed away
    assert es.alexa_connected() is True                                 # remembered
    _events(tmp_path, '{"type":"alexa_connect","subject":"stop","_ts":20}')
    assert es.alexa_connected() is False and es.output_decision()[0] == "mac"


def test_connect_start_connects_bluetooth_silently(monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(es, "device_index", lambda fresh=False: None)
    monkeypatch.setattr(es, "connect", lambda *a, **k: called.append(1) or True)
    monkeypatch.setattr(es, "play", lambda path: True)
    _events(tmp_path, '{"type":"alexa_connect","subject":"start","_ts":10}')
    assert es.alexa_connected() is True
    import time as _t; _t.sleep(0.2)
    assert called == [1]



def test_connect_start_chimes_on_the_echo_only(monkeypatch, tmp_path):
    played = []
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
    monkeypatch.setattr(es, "play", lambda path: played.append(path) or True)
    import capabilities.alexa_ingress as ai
    monkeypatch.setattr(ai, "_chime_mp3", lambda: b"CHIME")
    _events(tmp_path, '{"type":"alexa_connect","subject":"start","_ts":30}')
    assert es.alexa_connected() is True
    import time as _t; _t.sleep(0.3)
    assert len(played) == 1                     # once, on the Echo (play() targets the Echo device)
