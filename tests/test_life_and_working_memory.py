"""
tests/test_life_and_working_memory.py — card 0010.

A. Working memory: "What am I working on?" answered by LOOKUP, not by asking
   a model to reinterpret something eLo already knows.
   [SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08 §Tier 1]

B. LIFE: "eLo's inner life is continuous and is not suspended merely because
   a capability is being invoked." Today the inner process runs only on a
   message; between them there is nothing.
   [SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08]

The card's seven named tests are all here, plus the ones that keep this from
becoming a second version of something that already exists.
"""
from __future__ import annotations

import time

import pytest

from faculties.inner_thought import life
from faculties.inner_thought.working_memory import (
    AUTHORITY_DEFINITIVE, AUTHORITY_INFERENCE, AUTHORITY_RECORDED,
    MAX_EVENTS, WorkingMemory,
)


@pytest.fixture
def wm():
    return WorkingMemory()


def _ev(t="APP_OPENED", content="opened Blender", **kw):
    e = {"type": t, "content": content, "source": "macOS"}
    e.update(kw)
    return e


# ── A. the card's named tests ───────────────────────────────────────────────

def test_working_memory_add_and_query(wm):
    wm.add_event(_ev("APP_OPENED", "opened Blender"))
    wm.add_event(_ev("APP_OPENED", "opened Photoshop"))
    wm.add_event(_ev("FILE_OPENED", "imported eLo model"))
    wm.add_event(_ev("USER_MESSAGE", "how is the robot"))
    wm.add_event(_ev("APP_CLOSED", "closed Blender"))

    assert len(wm.query("blender")) == 2
    assert len(wm.query("APP_OPENED")) == 2
    assert wm.query("nothing here") == []


def test_working_memory_ring_buffer(wm):
    for i in range(35):
        wm.add_event(_ev(content=f"event {i}"))
    kept = wm.all_events()
    assert len(kept) == MAX_EVENTS
    assert kept[0]["content"] == "event 5", "oldest five should have fallen off"
    assert kept[-1]["content"] == "event 34"


def test_working_memory_current_project(wm):
    wm.add_event(_ev("TASK_CHANGED", "seams addon"))
    wm.add_event(_ev("APP_OPENED", "opened Blender"))
    wm.add_event(_ev("TASK_CHANGED", "eLo robot shell"))
    assert wm.current_project()["content"] == "eLo robot shell"


def test_working_memory_as_context_returns_string(wm):
    wm.add_event(_ev("APP_OPENED", "opened Blender"))
    out = wm.as_context()
    assert isinstance(out, str) and out.strip()
    assert "opened Blender" in out


def test_life_tick_resting_runs_without_error():
    out = life.life_tick("RESTING")
    assert out["ok"] is True
    assert out["state"] == "RESTING"


def test_life_tick_sleep_consolidates(monkeypatch):
    """
    Card says "SLEEP tick produces at least one vault_write (mock vault)".
    Consolidation here goes through correction_capture, which is the path that
    writes the vault — mocked, so nothing touches the real store.
    """
    calls = []
    import faculties.metacognition.correction_capture as cc
    monkeypatch.setattr(cc, "capture_new",
                        lambda **k: calls.append(1) or {"kept": 2, "seen": 2})

    out = life.life_tick("SLEEP")
    assert calls, "sleep did not run consolidation"
    assert "consolidated_corrections" in out["actions"]
    assert out["corrections_kept"] == 2


def test_life_tick_does_not_block():
    """A daemon beat that stalls is worse than one that does nothing."""
    t0 = time.time()
    life.life_tick("RESTING")
    life.life_tick("SLEEP")
    assert time.time() - t0 < 2.0


# ── A. authority is the point ───────────────────────────────────────────────

def test_an_event_never_claims_more_authority_than_it_was_given(wm):
    """
    Defaulting to `definitive` would let an inference read as a fact from the
    OS. The whole reason this tier avoids a model is that the reader does not
    have to guess.
    """
    assert wm.add_event(_ev())["authority"] == AUTHORITY_RECORDED
    assert wm.add_event(_ev(authority="nonsense"))["authority"] == AUTHORITY_RECORDED
    assert wm.add_event(_ev(authority=AUTHORITY_DEFINITIVE))["authority"] == AUTHORITY_DEFINITIVE


def test_context_marks_anything_not_definitive(wm):
    wm.add_event(_ev("APP_OPENED", "opened Blender", authority=AUTHORITY_DEFINITIVE))
    wm.add_event(_ev("TASK_CHANGED", "probably the shell", authority=AUTHORITY_INFERENCE))
    out = wm.as_context()
    assert "opened Blender\n" in out or out.rstrip().endswith("opened Blender")
    assert "(inference)" in out


def test_nothing_happened_is_an_empty_string_not_a_sentence(wm):
    assert wm.as_context() == ""


def test_a_typeless_event_is_refused(wm):
    assert wm.add_event({"content": "x"}) is None
    assert wm.add_event(None) is None


def test_an_unknown_type_is_kept_not_dropped(wm):
    """A timeline that silently discards what it does not recognise is worse."""
    assert wm.add_event(_ev("SOMETHING_NEW", "whatever")) is not None


def test_freshness_is_seconds_since_it_happened(wm):
    e = wm.add_event(_ev(timestamp=time.time() - 120))
    assert 115 < wm.freshness_s(e) < 125


# ── B. the loop is not here ─────────────────────────────────────────────────

def test_awake_does_not_tick():
    """
    The turn path already thinks on every message. A tick underneath it would
    be a second thinker competing with the first.
    """
    out = life.life_tick("AWAKE")
    assert out["ok"] is True
    assert out["actions"] == []


def test_sleep_does_not_start_a_dream():
    """
    Dreaming already has a trigger in ambient_engine, on a spent mind battery
    in calm. A second trigger here would be two things deciding when eLo
    dreams — the mistake already made with sits and deferral stores.
    """
    out = life.life_tick("SLEEP")
    assert "dream" not in " ".join(out.get("actions", []))
    assert "dream_due" in out, "it should REPORT whether one is due"


def test_this_module_schedules_nothing():
    """
    The card: "The LIFE loop itself lives in Builder 1's daemon (card 0106).
    Builder 2 provides the tick function."
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "faculties" / "inner_thought" / "life.py").read_text()
    body = src.split('"""', 2)[-1]
    for forbidden in ("threading.Thread", "while True", "sched.", "Timer("):
        assert forbidden not in body, f"life.py is running its own loop: {forbidden}"


def test_an_unknown_state_is_refused_not_guessed():
    out = life.life_tick("WIBBLE")
    assert out["ok"] is False and "unknown state" in out["error"]


def test_a_broken_faculty_does_not_break_the_beat(monkeypatch):
    import faculties.metacognition.deferred_threads as dt
    monkeypatch.setattr(dt, "sync_to_self_state",
                        lambda: (_ for _ in ()).throw(RuntimeError("down")))
    assert life.life_tick("RESTING")["ok"] is True


# ── A. not a second version of the existing one ────────────────────────────

def test_it_does_not_shadow_runtime_working_memory():
    """
    runtime/working_memory.py holds cognitive FRAMES, goals and attention —
    what eLo is holding in mind during a turn. This is an event TIMELINE.
    Different things; merging them loses the authority field, which is what
    lets this be answered without a model.
    """
    import runtime.working_memory as rwm
    assert hasattr(rwm, "WorkingMemory")
    assert not hasattr(rwm.WorkingMemory, "add_event"), (
        "the two WorkingMemory classes have converged — one of them should go"
    )


# ── the feeder ──────────────────────────────────────────────────────────────
#
# Card 0010 shipped the timeline with nothing writing to it and said so. The
# card expected app events from "Designer's event bus if wired" — that bus
# does not exist. Unity already writes the app name every tick:
#
#     blender/perch_state.json   {"app": "Claude", "edge": "bottom"}
#     blender/motion_state.json  {"window": "Claude", "win_id": 473}
#
# The signal was there under a different name the whole time. This is what
# makes "what was I doing?" answerable from state rather than from a model.

def test_a_focus_change_is_recorded(tmp_path, monkeypatch):
    import faculties.inner_thought.working_memory as wmm
    monkeypatch.setattr(wmm, "_INSTANCE", wmm.WorkingMemory())
    monkeypatch.setattr(wmm, "_current_app", lambda: "Blender")

    ev = wmm.observe_focus()
    assert ev is not None
    assert ev["content"] == "Blender"
    assert ev["type"] == "APP_FOCUSED"


def test_unity_observing_it_is_definitive_not_inference(tmp_path, monkeypatch):
    """
    The OS reported the window. This is not eLo concluding what David is
    doing, and the authority field is the thing that keeps those apart.
    """
    import faculties.inner_thought.working_memory as wmm
    monkeypatch.setattr(wmm, "_INSTANCE", wmm.WorkingMemory())
    monkeypatch.setattr(wmm, "_current_app", lambda: "Blender")
    assert wmm.observe_focus()["authority"] == wmm.AUTHORITY_DEFINITIVE


def test_the_same_app_is_not_logged_twice(monkeypatch):
    """
    The tick runs every 0.5s. Logging the app each time would fill a
    thirty-row buffer with one app and lose the session.
    """
    import faculties.inner_thought.working_memory as wmm
    monkeypatch.setattr(wmm, "_INSTANCE", wmm.WorkingMemory())
    monkeypatch.setattr(wmm, "_current_app", lambda: "Blender")

    assert wmm.observe_focus() is not None
    assert wmm.observe_focus() is None
    assert wmm.observe_focus() is None


def test_switching_back_and_forth_is_recorded(monkeypatch):
    import faculties.inner_thought.working_memory as wmm
    monkeypatch.setattr(wmm, "_INSTANCE", wmm.WorkingMemory())

    apps = iter(["Blender", "Blender", "Photoshop", "Blender"])
    monkeypatch.setattr(wmm, "_current_app", lambda: next(apps))

    got = [wmm.observe_focus() for _ in range(4)]
    recorded = [g["content"] for g in got if g]
    assert recorded == ["Blender", "Photoshop", "Blender"]


def test_elos_own_window_is_not_a_record(monkeypatch):
    """eLo perching on himself says only that eLo exists."""
    import faculties.inner_thought.working_memory as wmm
    monkeypatch.setattr(wmm, "_INSTANCE", wmm.WorkingMemory())
    for app in ("", "Presence", "eLo", "unknown"):
        monkeypatch.setattr(wmm, "_current_app", lambda a=app: a)
        assert wmm.observe_focus() is None


def test_the_ambient_tick_observes_focus():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "ambient" / "ambient_engine.py").read_text()
    assert "working_memory import observe_focus" in src
