"""
tests/test_wo016_019_voice_completeness.py — WO-016/019 voice_engine fix

Root cause: _speak_thread split text into sentences and made N separate OpenAI
API calls, so any slow fetch or interruption between sentences dropped the tail.

Fix: send the FULL text as ONE TTS call. Per-sentence loop only for say fallback.

  AT-1: _speak_thread calls TTS ONCE for full multi-sentence text (not per sentence)
  AT-2: _play_openai checks stop BEFORE the API fetch (no wasted network call)
  AT-3: _play_openai checks stop AFTER the API fetch (cancels before playback)
  AT-4: afplay is killed immediately when stop is set (not left running)
  AT-5: text > OPENAI_TTS_MAX_CHARS falls back to sentence-by-sentence say
  AT-6: say fallback is still sentence-by-sentence (say has no length limit)
  AT-7: _split_sentences still handles period/question/exclamation breaks
  AT-8: py_compile clean on voice_engine.py

Run: python3 tests/test_wo016_019_voice_completeness.py
"""
import sys, os, threading, unittest.mock as _mock, tempfile, time
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

import voice.voice_engine as _ve


# ── AT-1: _speak_thread calls TTS once for full multi-sentence text ────────────
try:
    _calls = []
    _stop = threading.Event()

    def _fake_play_openai(text, stop):
        _calls.append(text)
        return True

    with _mock.patch.object(_ve, "_OPENAI_KEY", "sk-fake"), \
         _mock.patch.object(_ve, "_EL_KEY", ""), \
         _mock.patch.object(_ve, "_play_openai", _fake_play_openai), \
         _mock.patch.object(_ve, "clear_lipsync", lambda: None):
        _ve._speak_thread(
            "First sentence here. Second sentence follows. Third one arrives.",
            _stop,
        )

    if len(_calls) == 1 and "Third one arrives" in _calls[0]:
        ok(f"AT-1: _speak_thread passed FULL text to TTS in ONE call ({len(_calls[0])} chars)")
    else:
        fail("AT-1", f"called {len(_calls)} times — expected 1; texts={[c[:40] for c in _calls]}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: _play_openai checks stop BEFORE API fetch ───────────────────────────
try:
    _fetched = []
    def _fake_fetch(text):
        _fetched.append(text)
        return b"fake_audio"

    _pre_stop = threading.Event()
    _pre_stop.set()   # already cancelled

    with _mock.patch.object(_ve, "_fetch_openai_audio", _fake_fetch):
        result = _ve._play_openai("Should not be fetched", _pre_stop)

    if not result and not _fetched:
        ok("AT-2: _play_openai skips API fetch when stop already set")
    else:
        fail("AT-2", f"result={result} fetched={len(_fetched)}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: _play_openai checks stop AFTER API fetch ────────────────────────────
try:
    _played = []
    _stop3 = threading.Event()

    def _fake_fetch3(text):
        _stop3.set()   # simulate cancellation during fetch
        return b"fake_audio"

    with _mock.patch.object(_ve, "_fetch_openai_audio", _fake_fetch3), \
         _mock.patch.object(_ve, "_text_to_phoneme_sequence", lambda t: []):
        result3 = _ve._play_openai("Some text", _stop3)

    # Should return False (not attempt playback) because stop was set during fetch
    if not result3:
        ok("AT-3: _play_openai returns False when stop set after fetch (no playback)")
    else:
        fail("AT-3", f"result={result3} (expected False)")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: afplay killed immediately when stop is set ─────────────────────────
try:
    _killed = []
    _stop4 = threading.Event()

    class _FakeProc:
        def kill(self): _killed.append("killed")
        def wait(self, timeout=None): pass

    def _fake_pulse4(phonemes, stop, text=""):
        stop.set()   # simulate cancellation during lipsync

    # Patch the audio bytes so no real API call happens, and real tempfile is used
    with _mock.patch.object(_ve, "_fetch_openai_audio", lambda t: b"ID3fake_audio"), \
         _mock.patch.object(_ve, "_text_to_phoneme_sequence", lambda t: []), \
         _mock.patch.object(_ve, "_pulse_lipsync", _fake_pulse4), \
         _mock.patch("subprocess.Popen", lambda *a, **kw: _FakeProc()):
        _ve._play_openai("some text", _stop4)

    if _killed:
        ok("AT-4: afplay.kill() called immediately when stop is set during lipsync")
    else:
        fail("AT-4", "afplay was not killed (proc.kill() not called)")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: text > OPENAI_TTS_MAX_CHARS falls back to sentence-by-sentence ──────
try:
    _say_calls = []
    _play_calls = []

    def _fake_say(text, stop):
        _say_calls.append(text)

    def _fake_play_openai5(text, stop):
        _play_calls.append(text)
        return False   # simulate failure

    _big_text = "A" * (_ve._OPENAI_TTS_MAX_CHARS + 100) + ". And a second bit."
    _stop5 = threading.Event()

    with _mock.patch.object(_ve, "_OPENAI_KEY", "sk-fake"), \
         _mock.patch.object(_ve, "_EL_KEY", ""), \
         _mock.patch.object(_ve, "_play_openai", _fake_play_openai5), \
         _mock.patch.object(_ve, "_play_say", _fake_say), \
         _mock.patch.object(_ve, "clear_lipsync", lambda: None):
        _ve._speak_thread(_big_text, _stop5)

    # _play_openai should NOT be called (text too long), say should be used
    if _say_calls and not _play_calls:
        ok(f"AT-5: text>{_ve._OPENAI_TTS_MAX_CHARS} chars falls back to sentence-by-sentence say "
           f"({len(_say_calls)} say call(s))")
    else:
        fail("AT-5", f"play_calls={len(_play_calls)} say_calls={len(_say_calls)}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: say fallback is sentence-by-sentence ────────────────────────────────
try:
    _say6 = []

    def _fake_say6(text, stop):
        _say6.append(text)

    _stop6 = threading.Event()
    _three_sentences = "One sentence here. Two follows now. Three completes it."

    with _mock.patch.object(_ve, "_OPENAI_KEY", ""), \
         _mock.patch.object(_ve, "_EL_KEY", ""), \
         _mock.patch.object(_ve, "_play_say", _fake_say6), \
         _mock.patch.object(_ve, "clear_lipsync", lambda: None):
        _ve._speak_thread(_three_sentences, _stop6)

    if len(_say6) == 3:
        ok(f"AT-6: say fallback is sentence-by-sentence ({len(_say6)} calls for 3-sentence text)")
    else:
        fail("AT-6", f"expected 3 say calls, got {len(_say6)}: {_say6}")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: _split_sentences handles period/question/exclamation ────────────────
try:
    _text7 = "Hello! How are you? I'm doing great. Let's continue."
    _parts = _ve._split_sentences(_text7)
    if len(_parts) == 4 and _parts[0] == "Hello!" and _parts[-1] == "Let's continue.":
        ok(f"AT-7: _split_sentences produced {len(_parts)} parts correctly")
    else:
        fail("AT-7", f"split result: {_parts}")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("voice/voice_engine.py", doraise=True)
    ok("AT-8: py_compile clean on voice_engine.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-016/019  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
