"""
tests/test_wo016_voice_plugin.py — Acceptance tests for WO-016

Spec: DISPATCH_BOARD §WO-016
Wire Whisper/STT into the voice plugin stub.

5 tests:
    FT-1  capture_input() delegates to voice.stt.capture()
    FT-2  deliver_output() delegates to tts_output.speak() with emotion snapshot
    FT-3  emotion snapshot correctly extracted from context dict
    ST-1  deliver_output() falls back to print on TTS error (no crash)
    ST-2  is_available() delegates to voice.stt.is_available()

Run: python3 tests/test_wo016_voice_plugin.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── FT-1: capture_input() delegates to voice.stt.capture() ───────────────────

_stt_called = []

import voice.stt as _stt_mod
_real_capture = _stt_mod.capture

def _fake_capture():
    _stt_called.append(True)
    return "hello from whisper"

_stt_mod.capture = _fake_capture

from plugins.voice.plugin import VoicePlugin
plugin = VoicePlugin()

result = plugin.capture_input()
try:
    assert len(_stt_called) == 1, "voice.stt.capture() not called"
    assert result == "hello from whisper", f"unexpected result: {result!r}"
    ok(f"FT-1: capture_input() → voice.stt.capture() → {result!r}")
except AssertionError as e: fail("FT-1", e)
finally:
    _stt_mod.capture = _real_capture


# ── FT-2: deliver_output() delegates to tts_output.speak() ───────────────────

import plugins.voice.tts_output as _tts_mod

_tts_calls = []
_real_speak = _tts_mod.speak

def _fake_speak(text, emotion_snapshot=None, backend=None):
    _tts_calls.append({"text": text, "emotion_snapshot": emotion_snapshot})

_tts_mod.speak = _fake_speak

ctx = {"emotional_state": "calm", "tone": "CALM", "voice_pacing": "slow", "voice_warmth": 0.85}
plugin.deliver_output("Wagwan", ctx)

try:
    assert len(_tts_calls) == 1, "tts_output.speak() not called"
    assert _tts_calls[0]["text"] == "Wagwan", f"text wrong: {_tts_calls[0]['text']!r}"
    snap = _tts_calls[0]["emotion_snapshot"]
    assert snap is not None, "emotion_snapshot not passed"
    ok(f"FT-2: deliver_output() → tts_output.speak(); snapshot={snap}")
except AssertionError as e: fail("FT-2", e)


# ── FT-3: emotion snapshot extracted correctly from context ───────────────────

_tts_calls.clear()
ctx2 = {
    "emotional_state": "curious",
    "tone":            "WARM",
    "voice_pacing":    "measured",
    "voice_warmth":    0.75,
}
plugin.deliver_output("Interesting.", ctx2)

try:
    snap2 = _tts_calls[0]["emotion_snapshot"]
    assert snap2["emotion"] == "curious",   f"emotion: {snap2['emotion']!r}"
    assert snap2["tone"]    == "WARM",      f"tone: {snap2['tone']!r}"
    assert snap2["pacing"]  == "measured",  f"pacing: {snap2['pacing']!r}"
    assert abs(snap2["warmth"] - 0.75) < 0.01, f"warmth: {snap2['warmth']}"
    ok(f"FT-3: emotion snapshot correct — emotion={snap2['emotion']!r}, pacing={snap2['pacing']!r}, warmth={snap2['warmth']}")
except AssertionError as e: fail("FT-3", e)
finally:
    _tts_mod.speak = _real_speak


# ── ST-1: deliver_output() falls back to print on TTS error, no crash ─────────

import io, builtins

_printed = []
_real_print = builtins.print

def _fake_print(*args, **kwargs):
    _printed.append(" ".join(str(a) for a in args))

def _broken_speak(*args, **kwargs):
    raise RuntimeError("TTS engine exploded")

_tts_mod.speak = _broken_speak
builtins.print = _fake_print
_st1_crashed = False
try:
    plugin.deliver_output("fallback test", {})
except Exception:
    _st1_crashed = True
finally:
    _tts_mod.speak = _real_speak
    builtins.print = _real_print   # restored before ok()/fail()

try:
    assert not _st1_crashed,   "deliver_output raised — should not crash"
    assert any("fallback test" in p for p in _printed), (
        f"fallback print not called; printed: {_printed}"
    )
    ok("ST-1: TTS error → fallback print, no crash")
except AssertionError as e: fail("ST-1", e)


# ── ST-2: is_available() delegates to voice.stt.is_available() ───────────────

_avail_calls = []
_real_avail = _stt_mod.is_available

def _fake_avail():
    _avail_calls.append(True)
    return True

_stt_mod.is_available = _fake_avail

try:
    result2 = plugin.is_available()
    assert len(_avail_calls) == 1, "voice.stt.is_available() not called"
    assert result2 is True, f"expected True, got {result2!r}"
    ok(f"ST-2: is_available() → voice.stt.is_available() → {result2}")
except AssertionError as e: fail("ST-2", e)
finally:
    _stt_mod.is_available = _real_avail


print(f"\nResult: {PASS}/5 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
