"""
S2 Phase 0 Bug 2 — every string eLo speaks must be recorded. Zero invisible
output.

Six of the 42 _voice_speak sites had no route to chat at all. The worst was
the file-agent result: eLo said out loud what he had done to a file, and it
appeared nowhere — David had no record of an action taken on his filesystem.

Logged inside speak() for the same reason the address rule is applied there:
it is the one place every spoken string passes through. A per-call-site fix
covers 1 of 42, and the next site added starts invisible again.

This is an AUDIT log, not chat bubbles. The main response is already
displayed; logging is not display. What it guarantees is that nothing eLo
says goes unrecorded.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest

import voice.voice_engine as ve

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def log(tmp_path, monkeypatch):
    """Never write the real spoken log from a test."""
    p = tmp_path / "spoken_log.jsonl"
    monkeypatch.setattr(ve, "_SPOKEN_LOG", str(p))
    return p


def _rows(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")] if p.exists() else []


def test_a_spoken_string_is_recorded(log):
    ve._log_spoken("The arm stops at the same angle.")
    rows = _rows(log)
    assert len(rows) == 1
    assert rows[0]["text"] == "The arm stops at the same angle."
    assert rows[0]["ts"] > 0


def test_consecutive_lines_are_both_kept(log):
    """
    ambient_speech.json holds one slot. Two things spoken in quick succession
    and the first is gone — which is the invisible output this ends.
    """
    ve._log_spoken("first")
    ve._log_spoken("second")
    assert [r["text"] for r in _rows(log)] == ["first", "second"]


def test_source_is_recorded(log):
    ve._log_spoken("x", source="ambient")
    assert _rows(log)[0]["source"] == "ambient"


def test_logging_never_raises(log, monkeypatch):
    """A logging failure must not stop eLo speaking."""
    monkeypatch.setattr(ve, "_SPOKEN_LOG", "/nonexistent/\x00/bad/path.jsonl")
    ve._log_spoken("still fine")          # must not raise


def test_log_is_trimmed_and_keeps_the_most_recent(log, monkeypatch):
    monkeypatch.setattr(ve, "_SPOKEN_LOG_MAX", 5)
    for i in range(12):
        ve._log_spoken(f"line {i}")
    rows = _rows(log)
    assert len(rows) == 5
    assert rows[-1]["text"] == "line 11", "trim kept the wrong end"


# ── the chokepoint, not the call sites ───────────────────────────────────────

def test_speak_logs_every_spoken_string():
    """
    The claim is structural: logging sits inside speak(), so all 42 call sites
    are covered and a 43rd cannot start invisible.
    """
    src = open(os.path.join(_ROOT, "voice", "voice_engine.py"), encoding="utf-8").read()
    i = src.index("def speak(")
    body = src[i:]
    assert "_log_spoken(text)" in body, "speak() does not record what it says"
    # before the audio thread starts, so a TTS failure still leaves a record
    assert body.index("_log_spoken(text)") < body.index("_active_thread = threading.Thread")


def test_logging_happens_after_conditioning():
    """
    The log must hold what was actually SAID — the conditioned string — not
    the pre-guard text, or the audit disagrees with the audio.
    """
    src = open(os.path.join(_ROOT, "voice", "voice_engine.py"), encoding="utf-8").read()
    i = src.index("def speak(")
    body = src[i:]
    assert body.index("text = _arg(text)") < body.index("_log_spoken(text)")


def test_json_is_imported():
    """
    _log_spoken uses json.dumps inside a bare except. Without the import it
    compiles, swallows the NameError and logs nothing — the exact silent
    failure this whole item is about. Caught by running it, not by compiling.
    """
    src = open(os.path.join(_ROOT, "voice", "voice_engine.py"), encoding="utf-8").read()
    assert "\nimport json" in src
