"""
WO-B3-0011 v1 — eLo runs David's allow-listed device Shortcuts. Offline: the
`shortcuts` command is stubbed; no real device is touched.
"""
import subprocess
import pytest
import tools.device_control as dc

HAVE = ["Blank auto launch ⚡︎", "Lights On", "Design Mode", "Lights Out", "Download file", "Living Room Sounds"]


class _R:
    def __init__(self, rc=0, out="", err=""): self.returncode, self.stdout, self.stderr = rc, out, err


@pytest.fixture
def ran(monkeypatch, tmp_path):
    calls = []
    def fake(args, **k):
        if args[:2] == ["shortcuts", "list"]:
            return _R(out="\n".join(HAVE))
        calls.append(args); return _R()
    monkeypatch.setattr(subprocess, "run", fake)
    monkeypatch.setattr(dc, "_ALLOW_FILE", str(tmp_path / "none.json"))
    monkeypatch.setattr(dc, "_ALEXA_FILE", str(tmp_path / "none2.json"))
    monkeypatch.delenv("VOICE_MONKEY_TOKEN", raising=False)
    dc._cache.update(ts=0.0, names=[])
    return calls


@pytest.mark.parametrize("q,name", [("turn off the lights", "Lights Out"), ("eLo, lights on please", "Lights On"),
                                    ("switch the lights off", "Lights Out"), ("design mode", "Design Mode"),
                                    ("do living room sounds", "Living Room Sounds")])
def test_commands_match_shortcuts(ran, q, name):
    assert dc.match(q) == name


@pytest.mark.parametrize("q", ["are the lights on?", "what's design mode", "I love these lights",
                               "download file", "run download file", "turn on spotify"])
def test_questions_and_unlisted_never_run(ran, q):
    assert dc.match(q) is None


def test_run_reports_what_it_did(ran):
    r = dc.run("Lights Out")
    assert r["success"] and r["result"]["line"] == "Ran your “Lights Out” shortcut."
    assert ran == [["shortcuts", "run", "Lights Out"]]


def test_never_runs_a_shortcut_outside_the_allow_list(ran):
    r = dc.run("Download file")
    assert not r["success"] and ran == []


def test_failure_is_reported(monkeypatch, ran):
    monkeypatch.setattr(subprocess, "run", lambda args, **k: _R(out="\n".join(HAVE)) if args[1] == "list"
                        else _R(rc=1, err="The operation couldn't be completed"))
    r = dc.run("Lights On")
    assert not r["success"] and "didn't run" in r["result"]["line"]


def test_router_runs_it_directly(ran):
    import tools.tool_router as tr
    out = tr._direct_intercepts("turn off the lights")
    assert out == ("Ran your “Lights Out” shortcut.", "devices")


def test_alexa_route_when_voice_monkey_is_set_up(ran, monkeypatch):
    import urllib.request, io
    monkeypatch.setenv("VOICE_MONKEY_TOKEN", "tok")
    hits = []
    class _Resp(io.BytesIO):
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout=10: hits.append(url) or _Resp(b'{"success":true}'))
    r = dc.run("Lights Out")
    assert r["success"] and r["result"]["via"] == "alexa" and r["result"]["line"] == "Asked Alexa: lights out."
    assert "device=elo-lights-off" in hits[0] and "token=tok" in hits[0]
    assert ran == []                                      # the Mac Shortcut was NOT used


def test_alexa_refusal_is_reported(ran, monkeypatch):
    import urllib.request, io
    monkeypatch.setenv("VOICE_MONKEY_TOKEN", "tok")
    class _Resp(io.BytesIO):
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout=10: _Resp(b'{"success": false, "error": "bad device"}'))
    r = dc.run("Lights On")
    assert not r["success"] and "didn't take" in r["result"]["line"]


def test_alexa_commands_controllable_even_without_mac_shortcut(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", lambda args, **k: _R(out=""))   # no shortcuts on the Mac
    monkeypatch.setattr(dc, "_ALEXA_FILE", str(tmp_path / "none.json"))
    dc._cache.update(ts=0.0, names=[])
    monkeypatch.setenv("VOICE_MONKEY_TOKEN", "tok")
    assert dc.match("turn off the lights") == "Lights Out"
