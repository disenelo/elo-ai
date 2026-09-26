"""
tests/test_s3_dream_wiring.py — QUEUE/S3-DREAM-WIRING-DEFECT.

Defect: Brain wrote state.mode = "dreaming" at server.py:~974, but Unity's
lay-down pose triggers on `intent` (EloOSAvatarReceiver.cs:482-485). The two
sides spoke different fields, so the real Brain dream path never reached the
animation — only the dream_debug.json test toggle did.

These are source-level guards. They assert the field is emitted on both the
enter and exit paths and fail if either is removed. They do NOT prove Unity
received it — that needs a live server and a real dream trigger.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

SERVER = Path(__file__).resolve().parent.parent / "server.py"


def _dream_block() -> str:
    """The ambient-tick dream section, enter through exit."""
    src = SERVER.read_text(encoding="utf-8")
    start = src.index('"mode": "dreaming"')
    end = src.index('"lifecycle_state": "restored"', start)
    return src[start - 400:end + 400]


def test_server_py_parses():
    ast.parse(SERVER.read_text(encoding="utf-8"))


def test_enter_dream_writes_intent_dream():
    block = _dream_block()
    enter = block[: block.index('"lifecycle_state": "restored"')]
    assert '"intent":' in enter, "dream enter does not write intent at all"
    assert re.search(r'"intent":\s*"dream"', enter), (
        'dream enter writes state.mode but not intent="dream" — '
        "Unity lay-down pose will not fire"
    )


def test_enter_dream_still_writes_the_original_fields():
    """The fix adds a field. It must not have replaced the existing writes."""
    enter = _dream_block()
    enter = enter[: enter.index('"lifecycle_state": "restored"')]
    assert re.search(r'"mode":\s*"dreaming"', enter)
    assert re.search(r'"animation":\s*"sleep"', enter)
    assert re.search(r'"lifecycle_state":\s*"dreaming"', enter)


def test_exit_dream_clears_the_intent():
    """Without this eLo stays in dream intent after waking and never stands up."""
    block = _dream_block()
    exit_block = block[block.index('"lifecycle_state": "restored"') - 300:]
    assert re.search(r'"intent":\s*"idle"', exit_block), (
        "dream exit does not clear intent — eLo stays laid down after waking"
    )


def test_exit_dream_clears_the_dream_cycle_fields():
    """WO-DREAM-ENGINE-001 PHASE 9: on wake, dream_phase goes null."""
    block = _dream_block()
    exit_block = block[block.index('"lifecycle_state": "restored"') - 300:]
    assert re.search(r'"dream_phase":\s*None', exit_block)
    assert re.search(r'"dream_intensity":\s*0\.0', exit_block)


def test_intent_values_match_what_unity_accepts():
    """
    EloOSAvatarReceiver.cs:482-485 accepts "dream" / "dreaming" / "daydream".
    Guard against a rename to something Unity does not recognise.
    """
    block = _dream_block()
    enter = block[: block.index('"lifecycle_state": "restored"')]
    match = re.search(r'"intent":\s*"([a-z]+)"', enter)
    assert match is not None
    assert match.group(1) in ("dream", "dreaming", "daydream"), match.group(1)
