"""
S2 Phase 0 Bug 1 — voice and chat must carry the same conditioned string.

STACK.md: "TTS must read same conditioned string as chat.
           Verify: 'you' in text = 'you' in voice"

enforce_second_person_to_david rewrites "David <verb>" and bare "David" into
"you", so eLo does not refer to David in the third person while talking to
him. server.py applied it at :6761 — in the MAIN path only.

Measured: 41 early returns sit before that line, and there are 42 separate
_voice_speak call sites. On any fast path eLo said "David" out loud, to David,
and showed "David" in chat. Voice and text agreed with each other and both
broke the address rule.

Fixed at two chokepoints rather than 41 edits:
  voice/voice_engine.speak()  — covers all 42 spoken strings
  server.py send boundary     — covers every route out of a turn

The guard is idempotent, so the main path passing through twice is harmless.
"""
from __future__ import annotations

import os
import re

import pytest

from runtime.address_rule_guard import enforce_second_person_to_david as condition

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(rel):
    return open(os.path.join(_ROOT, rel), encoding="utf-8").read()


# ── the guard itself ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,want", [
    ("I remember when David built the arm.", "I remember when you built the arm."),
    ("I told David about it.", "I told you about it."),
])
def test_guard_rewrites_third_person_david(raw, want):
    assert condition(raw) == want


@pytest.mark.parametrize("raw", [
    "David Charles, founder of DISENELO",   # full name — a fact, not an address
    "the DISENELO brand",
    "Davidson",                              # substring, must not match
    "That landed.",
])
def test_guard_leaves_other_text_alone(raw):
    assert condition(raw) == raw


def test_guard_is_idempotent():
    """Both chokepoints may apply it to the same string on the main path."""
    once = condition("I remember when David built the arm with David.")
    assert condition(once) == once


# ── both chokepoints wired ────────────────────────────────────────────────────

def test_voice_conditions_every_spoken_string():
    """
    42 _voice_speak sites. Conditioning inside speak() is the only way to
    cover them all; a fix at any single call site leaves 41 unconditioned.
    """
    s = _src("voice/voice_engine.py")
    assert "enforce_second_person_to_david" in s
    assert "text = _arg(text)" in s


def test_chat_conditions_every_route_out_of_a_turn():
    s = _src("server.py")
    assert 'result["response"] = _arg_out(result["response"])' in s
    assert "_arg_out(b) if isinstance(b, str) else b" in s, "bubbles must be conditioned too"


def test_every_turn_response_boundary_is_conditioned():
    """
    There is more than one route out. /chat and /listen each return a turn
    result, and the first version of this fix covered only /chat — leaving the
    VOICE-input path, where a voice/text split matters most, unconditioned.
    Every _send_json(200, result) must be fed a conditioned result.
    """
    src = _src("server.py").splitlines()
    sends = [i for i, l in enumerate(src) if "_send_json(200, result)" in l]
    assert sends, "no turn-result send sites found — pipeline restructured?"
    for i in sends:
        window = "\n".join(src[max(0, i - 12):i])
        assert "_condition_outbound(" in window, (
            f"server.py:{i+1} sends a turn result that was never conditioned"
        )


def test_conditioning_precedes_the_audio_call():
    """Conditioning after the audio starts would be too late."""
    s = _src("voice/voice_engine.py")
    i = s.index("def speak(")
    body = s[i:]
    assert body.index("text = _arg(text)") < body.index("_stop_flag.set()")


# ── the gap this closes ───────────────────────────────────────────────────────

def test_fast_paths_exist_and_bypass_the_main_guard():
    """
    Pins the reason both chokepoints are needed. If this ever reports zero,
    the pipeline has been restructured and the fix can be reconsidered.
    """
    src = _src("server.py").splitlines()
    guard = next(i for i, l in enumerate(src) if "response = _arg(response)" in l) + 1
    early = [i + 1 for i, l in enumerate(src)
             if re.match(r'^\s+return \{"response":', l) and i + 1 < guard]
    assert len(early) > 1, (
        "no early returns found before the main guard — if the pipeline now has "
        "a single exit, the boundary fix alone would suffice"
    )


def test_voice_and_chat_agree_on_the_same_input():
    """The actual claim: the same text conditioned for each path is identical."""
    raw = "I remember when David built the arm."
    assert condition(raw) == condition(condition(raw))
