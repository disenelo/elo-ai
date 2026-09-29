"""
tests/test_elo_intentions_001.py — Intentions store
eLo as a holder of intentions: hold, defer, resume, complete, abandon.
Wired into turn path via intentions_prompt_block().

AT-1  hold() creates an ACTIVE intention with correct fields
AT-2  defer() moves ACTIVE → DEFERRED with reason
AT-3  resume() moves DEFERRED → RESUMED, increments resumed_count
AT-4  complete() moves ACTIVE/RESUMED → COMPLETED
AT-5  abandon() moves to ABANDONED
AT-6  open_intentions() returns only open statuses (ACTIVE/DEFERRED/RESUMED)
AT-7  relevant_to_turn() matches deferred intentions by keyword
AT-8  relevant_to_turn() returns nothing when no keyword matches
AT-9  intentions_prompt_block() returns non-empty when intentions open
AT-10 intentions_prompt_block() marks relevant intentions in block
AT-11 intentions_prompt_block() returns "" when no open intentions
AT-12 Server.py wiring: intentions block injection present in source
AT-13 py_compile clean on intentions.py and server.py
"""
from __future__ import annotations

import os
import sys
import json
import py_compile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import memory.intentions as intmod
from memory.intentions import (
    Intention,
    hold, defer, resume, complete, abandon,
    open_intentions, deferred_intentions, relevant_to_turn,
    intentions_prompt_block,
    STATUS_ACTIVE, STATUS_DEFERRED, STATUS_RESUMED,
    STATUS_COMPLETED, STATUS_ABANDONED,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path):
    """Redirect _STORE to a temp file for every test — no pollution of real data."""
    tmp_store = tmp_path / "test_intentions.json"
    with patch.object(intmod, "_STORE", tmp_store):
        yield tmp_store


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_hold_creates_active_intention():
    intention = hold("Figure out the SPG context_tags enrichment path", context="SPG discussion")
    assert isinstance(intention, Intention)
    assert intention.status == STATUS_ACTIVE
    assert intention.content == "Figure out the SPG context_tags enrichment path"
    assert intention.context == "SPG discussion"
    assert intention.intention_id
    # Must persist to disk
    loaded = open_intentions()
    assert any(i.intention_id == intention.intention_id for i in loaded)


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_defer_moves_to_deferred():
    intention = hold("Finish the intentions module", context="build session")
    result = defer(intention.intention_id, reason="Blocked on test setup")
    assert result is True
    loaded = open_intentions()
    match = next((i for i in loaded if i.intention_id == intention.intention_id), None)
    assert match is not None
    assert match.status == STATUS_DEFERRED
    assert match.deferred_reason == "Blocked on test setup"


def test_at2_defer_nonexistent_returns_false():
    assert defer("does-not-exist") is False


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_resume_moves_to_resumed():
    intention = hold("Research NeoPixel timing for robot", context="robot build")
    defer(intention.intention_id, reason="Hardware not arrived")
    result = resume(intention.intention_id)
    assert result is True
    loaded = open_intentions()
    match = next(i for i in loaded if i.intention_id == intention.intention_id)
    assert match.status == STATUS_RESUMED
    assert match.resumed_count == 1

    # Resume again — count should increment
    defer(intention.intention_id, reason="Second deferral")
    resume(intention.intention_id)
    loaded = open_intentions()
    match = next(i for i in loaded if i.intention_id == intention.intention_id)
    assert match.resumed_count == 2


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_complete_removes_from_open():
    intention = hold("Write the habit tracker test", context="test session")
    result = complete(intention.intention_id)
    assert result is True
    loaded = open_intentions()
    assert not any(i.intention_id == intention.intention_id for i in loaded)


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_abandon():
    intention = hold("Explore Groq integration", context="backend session")
    result = abandon(intention.intention_id, reason="Groq quota hit — David's lane")
    assert result is True
    loaded = open_intentions()
    assert not any(i.intention_id == intention.intention_id for i in loaded)


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_open_intentions_only_open_statuses():
    i_active   = hold("Active thread A")
    i_deferred = hold("Deferred thread B")
    i_complete = hold("Completed thread C")
    defer(i_deferred.intention_id, reason="waiting")
    complete(i_complete.intention_id)

    loaded = open_intentions()
    statuses = {i.intention_id: i.status for i in loaded}
    assert statuses.get(i_active.intention_id)   == STATUS_ACTIVE
    assert statuses.get(i_deferred.intention_id) == STATUS_DEFERRED
    assert i_complete.intention_id not in statuses


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_relevant_to_turn_matches_by_keyword():
    intention = hold("Look into SPG graph enrichment next session",
                     keywords=["spg", "graph", "enrichment"])
    defer(intention.intention_id, reason="Not now")

    matches = relevant_to_turn("What about the spg graph — are we enriching it?")
    assert any(m.intention_id == intention.intention_id for m in matches), (
        "AT-7 FAIL: deferred intention with matching keywords not returned by relevant_to_turn()"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_relevant_to_turn_no_match():
    intention = hold("Finish the robot servo mapping", keywords=["servo", "robot", "mapping"])
    defer(intention.intention_id, reason="Hardware")

    matches = relevant_to_turn("What time is it?")
    assert not any(m.intention_id == intention.intention_id for m in matches), (
        "AT-8 FAIL: unrelated turn matched a deferred intention — keyword gate too loose"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_prompt_block_non_empty_when_intentions_open():
    hold("Finish writing the calm animation NLA strip")
    block = intentions_prompt_block()
    assert block, "AT-9 FAIL: intentions_prompt_block() empty despite open intention"
    assert "[OPEN INTENTIONS" in block


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_prompt_block_marks_relevant():
    intention = hold("Write the SPG pattern test suite", keywords=["spg", "pattern", "test"])
    defer(intention.intention_id, reason="After habits WO")
    block = intentions_prompt_block(turn_text="Let's continue with the spg pattern work")
    assert "RELEVANT TO THIS TURN" in block, (
        "AT-10 FAIL: relevant intention not highlighted in prompt block"
    )


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_prompt_block_empty_when_no_intentions():
    block = intentions_prompt_block()
    assert block == "", (
        "AT-11 FAIL: intentions_prompt_block() returned non-empty with no intentions"
    )


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_server_wiring():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "intentions_prompt_block" in source, (
        "AT-12 FAIL: 'intentions_prompt_block' not found in server.py"
    )
    assert "memory.intentions" in source, (
        "AT-12 FAIL: 'memory.intentions' import not found in server.py"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_py_compile_clean():
    files = [
        os.path.join(ROOT, "memory", "intentions.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-13 FAIL: {os.path.basename(path)} compile error: {exc}")
