"""
tests/test_dream_request.py — S3: detect an external request to dream.

The dispatch says "server.py detects intent='dream' → call
executive.run_dream_window()". run_dream_window() declines unless
blender_state["asleep"] is true, and Builder 1's trigger only fires when
NOT asleep — so that wire would have returned {"action":"awake","ran":False}
every time, without raising. Dead on arrival, silently.

The request is therefore wired as an extra entry condition on the dream
executor that already works, not as a third executor.
"""
from __future__ import annotations

import pytest

import runtime.dream_request as dr


@pytest.fixture(autouse=True)
def _no_live_writes(monkeypatch):
    written: list[dict] = []
    monkeypatch.setattr("blender_bridge.state_writer.patch", written.append)
    return written


# ── Detection ────────────────────────────────────────────────────────────────

def test_an_intent_to_dream_is_a_request():
    assert dr.dream_requested({"intent": "dream"}, consume=False) is True


@pytest.mark.parametrize("intent", ["idle", "", "sit", "move", None])
def test_anything_else_is_not(intent):
    assert dr.dream_requested({"intent": intent}, consume=False) is False


def test_an_empty_state_is_not_a_request():
    assert dr.dream_requested({}, consume=False) is False


# ── It must not re-enter a dream already running ────────────────────────────

@pytest.mark.parametrize("field,value", [
    ("dream_phase", "NREM"),
    ("asleep", True),
    ("lifecycle_state", "dreaming"),
])
def test_a_dream_in_flight_is_not_a_new_request(field, value):
    """
    The dream path writes intent="dream" itself for Unity's lay-down pose
    (server.py:1050). Without this guard that write reads back as a fresh
    request and the dream re-enters itself every tick.
    """
    st = {"intent": "dream", field: value}
    assert dr.already_dreaming(st) is True
    assert dr.dream_requested(st, consume=False) is False


# ── Consumption ─────────────────────────────────────────────────────────────

def test_accepting_clears_the_request(_no_live_writes):
    assert dr.dream_requested({"intent": "dream"}) is True
    assert {"intent": "idle"} in _no_live_writes


def test_declining_clears_nothing(_no_live_writes):
    dr.dream_requested({"intent": "idle"})
    dr.dream_requested({"intent": "dream", "asleep": True})
    assert _no_live_writes == []


def test_consume_false_leaves_it_alone(_no_live_writes):
    assert dr.dream_requested({"intent": "dream"}, consume=False) is True
    assert _no_live_writes == []


# ── Causal ──────────────────────────────────────────────────────────────────

def test_removing_the_intent_removes_the_request():
    with_intent = dr.dream_requested({"intent": "dream"}, consume=False)
    without = dr.dream_requested({}, consume=False)
    assert with_intent is True and without is False


# ── No third executor ───────────────────────────────────────────────────────

def test_the_wire_does_not_add_another_run_dream_window_call():
    """
    Two dream executors already exist — server.py's ambient path and
    spine.py:894. A third call site for one behaviour is the mistake
    WO-TIRED-SIT-001 made with two sit emitters.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    raw = (root / "server.py").read_text(encoding="utf-8")
    # Comments only, stripped: the wire's comment EXPLAINS why it does not
    # call run_dream_window, and a substring scan would read that prose as
    # the call. Same mistake as reading a WO instead of the source.
    server = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("#"))
    assert "run_dream_window" not in server, (
        "server.py now calls run_dream_window — that is a third executor"
    )
    spine = (root / "runtime" / "spine" / "spine.py").read_text(encoding="utf-8")
    assert spine.count("run_dream_window") >= 1, "the spine's executor vanished"


def test_the_executive_is_untouched():
    """runtime/executive.py is treated as frozen."""
    import inspect
    import runtime.executive as ex
    src = inspect.getsource(ex.run_dream_window)
    assert "_read_asleep()" in src, "the asleep gate was modified"


# ── The wiring ──────────────────────────────────────────────────────────────

def _server() -> str:
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")


def test_the_ambient_dream_gate_consults_the_request():
    src = _server()
    assert "from runtime.dream_request import dream_requested" in src
    assert "or _dream_asked()" in src


def test_the_request_is_checked_after_should_dream_not_before():
    """
    Order matters: `or` short-circuits, so the request is consumed only when
    should_dream() has already declined and the request is the actual reason
    the dream runs. Checking it first would clear the intent on every tick
    where eLo was going to dream anyway.
    """
    src = _server()
    gate = src[src.index("if should_dream("):]
    line = gate.splitlines()[0]
    assert line.index("should_dream(") < line.index("_dream_asked()"), line
