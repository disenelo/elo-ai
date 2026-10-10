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
