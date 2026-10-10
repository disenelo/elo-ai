"""B3 — voice_engine._play_proc: eLo's main voice → Echo only when chosen + connected. Offline (no audio played)."""
import subprocess
import voice.voice_engine as ve
import tools.echo_speaker as es


class _FakeProc:
    def __init__(self, args): self.args = args


def test_mac_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(es, "speaking", lambda: False)
    monkeypatch.setattr(subprocess, "Popen", lambda args, **k: calls.append(args) or _FakeProc(args))
    ve._play_proc("/tmp/x.mp3")
    assert calls == [["afplay", "/tmp/x.mp3"]]


def test_echo_when_chosen_and_connected(monkeypatch):
    monkeypatch.setattr(es, "speaking", lambda: True)
    monkeypatch.setattr(es, "popen_play", lambda path: _FakeProc(["ffmpeg", path]))
    assert ve._play_proc("/tmp/x.mp3").args == ["ffmpeg", "/tmp/x.mp3"]


def test_echo_failure_falls_back_to_mac(monkeypatch):
    calls = []
    monkeypatch.setattr(es, "speaking", lambda: True)
    monkeypatch.setattr(es, "popen_play", lambda path: None)
    monkeypatch.setattr(subprocess, "Popen", lambda args, **k: calls.append(args) or _FakeProc(args))
    ve._play_proc("/tmp/x.mp3")
    assert calls == [["afplay", "/tmp/x.mp3"]]
