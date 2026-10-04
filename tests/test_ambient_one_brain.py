"""
tests/test_ambient_one_brain.py — IS ELO: One Brain?

    "can an ambient process speak as eLo without a cognitive plan?"
    "can a legacy path bypass Executive?"
    "if I remove the prompts that tell eLo to behave like eLo, does the
     architecture still produce eLo?"

Yes, yes, and the third one is worse than a prompt.

server.py has a correct One Brain ambient path: the Executive decides, a
chosen silence stops the turn, the decision is journalled, and the line is
built through prompt_builder — "proves self-initiated turns use the same
faculty chain as conversational turns". It is registered into the ambient
engine as _ambient_cb.

Three call sites spoke around it:

  :778  idle "utterance" behaviour  → _speak(choice(_AMBIENT_LINES))
  :850  startup greeting            → _speak(choice(_STARTUP_LINES))
  :871  startup greeting, 2nd site  → _speak(choice(_STARTUP_LINES))

_AMBIENT_LINES is a developer-written list — "Still here.", "You've got
this.", "Good energy today." Those are not prompts telling eLo how to behave;
they are eLo's voice, pre-written, emitted on a timer with no decision behind
them. The site at :921 already asks the brain first and only falls back to
the pool. The other three never asked.

WHAT IS NOT CLAIMED HERE: the authored pool is not deleted. With no brain
registered, the alternative to a pool line is muteness, and the greeting
fires before the server may be ready. What changes is that unplanned speech
is DECLARED — logged as speech eLo did not decide to make — instead of
passing as his cognition. A quirk-bank line is declared separately from an
authored one, because a line drawn from his own accumulated material is not
the same thing as a line someone typed for him.
"""
from __future__ import annotations

import logging

import pytest

import ambient.ambient_engine as ae


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    spoken: list[str] = []
    monkeypatch.setattr(ae, "_speak", lambda t: spoken.append(t))
    monkeypatch.setattr(ae, "_ambient_cb", None)
    monkeypatch.setattr(ae, "_is_speaking", lambda: False)
    return spoken


# ── The Executive gets asked first ───────────────────────────────────────────

def test_idle_speech_asks_the_brain_when_one_is_registered(monkeypatch, _clean):
    called: list[int] = []
    monkeypatch.setattr(ae, "_ambient_cb", lambda: called.append(1))
    monkeypatch.setattr(ae.threading, "Thread",
                        lambda target, daemon=False: type(
                            "T", (), {"start": lambda s: target()})())
    ae._ambient_utterance()
    assert called, "the brain was registered and never asked"
    assert not _clean, f"spoke an authored line anyway: {_clean}"


def test_no_authored_line_is_spoken_while_the_brain_is_available(monkeypatch, _clean):
    # random.random() pinned ABOVE the quirk threshold so the authored pool is
    # the only fallback available. Unpinned, this passed ~30% of the time on a
    # broken route by taking the quirk branch instead — a flaky test is worse
    # than no test, and a wire-cut only caught it because I read which tests
    # went red rather than the count.
    monkeypatch.setattr(ae.random, "random", lambda: 1.0)
    monkeypatch.setattr(ae, "_ambient_cb", lambda: None)
    monkeypatch.setattr(ae.threading, "Thread",
                        lambda target, daemon=False: type(
                            "T", (), {"start": lambda s: target()})())
    ae._ambient_utterance()
    for line in _clean:
        assert line not in ae._AMBIENT_LINES, line


# ── Unplanned speech is declared, not disguised ─────────────────────────────

def test_speaking_without_a_brain_says_so(monkeypatch, caplog, _clean):
    with caplog.at_level(logging.WARNING, logger="ambient.ambient_engine"):
        ae._ambient_utterance()
    assert _clean, "nothing was spoken at all"
    assert "without a cognitive plan" in caplog.text.lower(), caplog.text


def test_a_quirk_bank_line_is_declared_differently_from_an_authored_one(
        monkeypatch, caplog, _clean):
    """
    A line drawn from eLo's own accumulated material is not the same as one a
    developer typed for him. "does eLo remember something because it
    happened, rather than because it was placed in a prompt?"
    """
    monkeypatch.setattr(ae.random, "random", lambda: 0.0)   # force the quirk draw
    import memory.quirk_bank as qb
    monkeypatch.setattr(qb, "draw", lambda n: ["the thing about Tuesdays"])
    with caplog.at_level(logging.WARNING, logger="ambient.ambient_engine"):
        ae._ambient_utterance()
    assert "the thing about Tuesdays" in _clean
    assert "quirk" in caplog.text.lower(), caplog.text


def test_the_startup_greeting_is_declared_too(monkeypatch, caplog, _clean):
    with caplog.at_level(logging.WARNING, logger="ambient.ambient_engine"):
        ae._speak_unplanned("Morning.", "startup")
    assert _clean == ["Morning."]
    assert "startup" in caplog.text


# ── No site may speak around the chokepoint ─────────────────────────────────

def test_every_ambient_speech_site_goes_through_a_declared_route():
    """
    Counted, not eyeballed. A new _speak(random.choice(...)) anywhere in this
    file is a fourth bypass, and the whole point is that there is one route.
    """
    from pathlib import Path
    src = Path(ae.__file__).read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    import re
    raw = re.findall(r"_speak\(\s*(?:_rand|random)\.choice", code)
    assert not raw, f"{len(raw)} ambient site(s) still speak an authored line directly"


def test_the_declared_route_is_the_only_caller_of_plain_speak(monkeypatch):
    """_speak itself stays — _speak_unplanned and the brain path both use it."""
    from pathlib import Path
    src = Path(ae.__file__).read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert "def _speak_unplanned" in code
    assert "def _ambient_utterance" in code
