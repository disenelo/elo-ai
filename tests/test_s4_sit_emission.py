"""
tests/test_s4_sit_emission.py — S4 · WO-TIRED-SIT-001 Part B relay.

The policy is tested in test_s4_rest_decision.py. These tests cover the half
that touches the world: does eLo's decision actually reach Unity, in the shape
Unity reads, and does the relay stay out of the policy's way.

Why maybe_sit() is a module and not a block in server.py: the first version
was a block, and a wire-cut that disabled the relay left every test green —
they were reading server.py's source for an import that was still written,
not calling the code. A fix nothing can prove broken has not been proven to
work. This file calls the thing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import blender_bridge.state_writer as sw
import runtime.rest_action as ra

_SERVER = (Path(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")


@pytest.fixture
def _state(tmp_path, monkeypatch):
    path = tmp_path / "blender_state.json"
    path.write_text(json.dumps({"motion": {"animation": "walk", "mode": "walk"}}))
    monkeypatch.setattr(sw, "_STATE_PATH", str(path))
    monkeypatch.setattr(ra, "_STATE_PATH", str(path))
    monkeypatch.setattr(ra, "_is_speaking", lambda: False)
    monkeypatch.setattr(ra, "_is_commanded", lambda: False)
    monkeypatch.setattr(ra, "_is_dreaming", lambda: False)
    return path


# ── The relay, called ────────────────────────────────────────────────────────

def test_a_fatigued_elo_sits_and_unity_is_told(_state, monkeypatch):
    monkeypatch.setattr(ra, "_published_band", lambda: "fatigued")
    issued = ra.maybe_sit()
    assert issued is not None and issued["name"] == "sit"
    out = json.loads(_state.read_text())
    assert out["intent"]["name"] == "sit"
    assert out["intent"]["issued_by"] == "elo"
    assert "_ts" in out["sit_command"], "Unity reads sit_command, not intent"


def test_a_rested_elo_does_not_sit_and_nothing_is_written(_state, monkeypatch):
    monkeypatch.setattr(ra, "_published_band", lambda: "rested")
    before = _state.read_text()
    assert ra.maybe_sit() is None
    assert _state.read_text() == before


def test_untracked_never_sits(_state, monkeypatch):
    """
    The published band when the physical track is disengaged. eLo must not sit
    down over a body he has no signal from.
    """
    monkeypatch.setattr(ra, "_published_band", lambda: "untracked")
    assert ra.maybe_sit() is None


def test_the_sit_does_not_clobber_other_sections(_state, monkeypatch):
    monkeypatch.setattr(ra, "_published_band", lambda: "exhausted")
    ra.maybe_sit()
    assert json.loads(_state.read_text())["motion"]["animation"] == "walk"


@pytest.mark.parametrize("gate", ["_is_speaking", "_is_commanded", "_is_dreaming"])
def test_each_gate_stops_the_sit(_state, monkeypatch, gate):
    monkeypatch.setattr(ra, "_published_band", lambda: "exhausted")
    monkeypatch.setattr(ra, gate, lambda: True)
    before = _state.read_text()
    assert ra.maybe_sit() is None, gate
    assert _state.read_text() == before


def test_already_sitting_does_not_sit_again(_state, monkeypatch):
    _state.write_text(json.dumps({"motion": {"animation": "sit", "mode": "sit"}}))
    monkeypatch.setattr(ra, "_published_band", lambda: "exhausted")
    assert ra.maybe_sit() is None


def test_the_band_comes_from_the_snapshot_not_the_raw_reader():
    """
    get_physical_state() returns a band even when the track is disengaged.
    _published_band() must go through snapshot(), which says "untracked".
    """
    from core import health_battery as hb
    hb.reset()
    try:
        assert hb.get_physical_state() != "untracked", "precondition: raw reader returns a band"
        assert ra._published_band() == "untracked"
    finally:
        hb.reset()


# ── state_writer.issue_intent ────────────────────────────────────────────────

@pytest.mark.parametrize("intent", [
    {"name": "move", "direction": "left"}, {"name": ""}, {}, None, "sit", 42,
])
def test_issue_intent_emits_nothing_for_anything_but_sit(_state, intent):
    before = _state.read_text()
    sw.issue_intent(intent)
    assert _state.read_text() == before


# ── Deconfliction: one sit emitter, not two ──────────────────────────────────

def test_exactly_one_sit_emitter_in_the_turn_path():
    """
    Builder 1's block (9cc64f1) and maybe_sit() both reached the body from the
    same turn for a while — theirs patching motion Sit_hold, mine writing
    sit_command. Two emitters disagreeing about posture is worse than either
    one alone, and theirs is the dispatched route, so maybe_sit() is withdrawn
    from server.py.

    Counts emitters rather than asserting an absence, so re-wiring this module
    without first removing the other one fails here instead of in Unity.
    """
    emitters = 0
    if "maybe_sit()" in _SERVER and "# " not in _SERVER.split("maybe_sit()")[0].rsplit("\n", 1)[-1]:
        emitters += 1
    if "_PENDING_SIT[\"active\"] = True" in _SERVER:
        emitters += 1
    assert emitters == 1, f"{emitters} sit emitters in server.py"


def test_the_decision_modules_are_present_but_unwired():
    """
    They are tested and they work; nothing calls them. Stated here so the
    state is a recorded decision rather than something to rediscover.
    """
    assert "from runtime.rest_action import" not in _SERVER
    assert "from runtime.rest_decision import" not in _SERVER
    assert ra.maybe_sit is not None
