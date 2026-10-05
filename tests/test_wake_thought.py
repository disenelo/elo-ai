"""
tests/test_wake_thought.py — S2 Phase 3: the first thought after a dream is the dream's.

STACK.md names the field: "Dream inner_thought from `wake_inner_thought`".
It returned 0 matches repo-wide — never built, so the phase could not run.

wake_from_dream() already folds a dream's insight into mood, curiosity and
satisfaction (pinned in test_dream_changes_state). What it never did was let
the dream be the thing eLo is THINKING when he next speaks. The insight was
written to the journal and never surfaced as a thought.
"""
from __future__ import annotations

import pathlib

import pytest

import runtime.wake_thought as wt


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(wt, "_PATH", str(tmp_path / "wake_inner_thought.json"))


def test_a_held_thought_comes_back():
    wt.hold("the seam was never the problem", dream_id="d1")
    assert wt.take() == "the seam was never the problem"


def test_it_is_consumed_on_read():
    """
    One turn only. A dream that kept re-surfacing would stop being a dream and
    start being a personality.
    """
    wt.hold("something about moons")
    assert wt.take()
    assert wt.take() == ""


def test_peek_does_not_consume():
    wt.hold("still here")
    assert wt.peek() == "still here"
    assert wt.peek() == "still here"
    assert wt.take() == "still here"


def test_nothing_held_is_empty_not_an_error():
    assert wt.take() == ""
    assert wt.peek() == ""


def test_an_empty_insight_holds_nothing():
    """A dream that produced no insight must not blank the next thought."""
    wt.hold("")
    assert wt.take() == ""


def test_whitespace_is_not_a_thought():
    wt.hold("   \n  ")
    assert wt.take() == ""


def test_a_corrupt_store_does_not_raise():
    pathlib.Path(wt._PATH).write_text("{not json", encoding="utf-8")
    assert wt.take() == ""


# ── The wiring ─────────────────────────────────────────────────────────────

def _server() -> str:
    return (pathlib.Path(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")


def test_the_dream_holds_its_insight_on_waking():
    code = "\n".join(l for l in _server().splitlines() if not l.strip().startswith("#"))
    assert "from runtime.wake_thought import hold" in code
    assert "_wt_hold(" in code


def test_the_inner_thought_path_takes_it():
    code = "\n".join(l for l in _server().splitlines() if not l.strip().startswith("#"))
    assert "from runtime.wake_thought import take" in code
    assert "if _wt_thought:" in code


def test_the_override_lands_after_the_generated_fallback():
    """
    Order is the whole thing. Applied before the generation block, the
    generated value would overwrite the dream — which is exactly what my
    first attempt did: an `else:` that only captured one line, so the LLM
    call still ran and clobbered the result.
    """
    code = _server()
    fallback = code.index('_it_result = _it_vmap.get(')
    override = code.index("if _wt_thought:")
    assert fallback < override, (fallback, override)
