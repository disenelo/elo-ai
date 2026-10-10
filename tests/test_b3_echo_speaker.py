"""B3 — tools/echo_speaker: finding the Echo as an output, caching, play only when connected. Offline."""
import pytest
from tools import echo_speaker as es


@pytest.fixture(autouse=True)
def _clean(tmp_path, monkeypatch):
    monkeypatch.setattr(es, "_SETTING", str(tmp_path / "voice_output.json"))
    monkeypatch.setattr(es, "_EVENTS", str(tmp_path / "unity_events.json"))
    es._vo_cache.update(ts=0.0, value=None)
    es._idx_cache.update(ts=0.0, idx=None); es.stop_wanting()
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


def test_voice_output_defaults_to_mac_and_mac_never_routes(monkeypatch):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)     # Echo connected
    assert es.voice_output() == "mac" and es.speaking() is False


def test_presence_setting_event_wins_and_is_remembered(monkeypatch, tmp_path):
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)
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
