"""
tests/test_wo069_multilingual_how_are_you.py — Acceptance tests for WO-069

Spec: WO-069 — Multilingual 'how are you' → answer in-language, no meta-narration.
"Como estas?" / "come stai?" / "ça va?" / "wie geht's?" → eLo answers the question,
in that language when mapped, with zero "I notice you asked in X" narration.

  AT-1: "como estas?" → Spanish reply (contains ¿/tú/bien), NO "I notice"/"you asked"
  AT-2: "come stai?" (it) → Italian reply token
  AT-3: "ça va?" (fr) → French reply token
  AT-4: "wie geht's?" (de) → German reply token
  AT-5: "how are you?" (en) → still routes to HOW_ARE_YOU (regression guard)
  AT-6: "hola" (pure greeting) → not matched by how-are-you detector (regression guard)
  AT-7: WO-069 marker present in server.py
  AT-8: py_compile clean on server.py

Run: python3 tests/test_wo069_multilingual_how_are_you.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

import server as _srv

META_PHRASES = ("i notice", "you asked in", "you wrote in", "a language", "language pivot",
                "language switch", "that was", "interesting choice")


def _no_meta(reply: str) -> bool:
    r = reply.lower()
    return not any(p in r for p in META_PHRASES)


# ── AT-1: "como estas?" → Spanish reply, no meta ─────────────────────────────
try:
    result = _srv._detect_multilingual_how_are_you("como estas?")
    assert result is not None, "_detect_multilingual_how_are_you returned None for 'como estas?'"
    lang, reply = result
    assert lang == "spanish", f"expected lang='spanish', got {lang!r}"
    # Spanish replies contain at least one of these tokens
    _es_tokens = ("bien", "¿y tú?", "¿y tu?", "tú", "tu?", "aquí", "todo")
    assert any(t in reply.lower() for t in _es_tokens), \
        f"AT-1: reply doesn't look Spanish: {reply!r}"
    assert _no_meta(reply), f"AT-1: meta-narration in reply: {reply!r}"
    ok(f"AT-1: 'como estas?' → Spanish reply: {reply!r}")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: "come stai?" → Italian reply ───────────────────────────────────────
try:
    result = _srv._detect_multilingual_how_are_you("come stai?")
    assert result is not None, "_detect_multilingual_how_are_you returned None for 'come stai?'"
    lang, reply = result
    assert lang == "italian", f"expected lang='italian', got {lang!r}"
    _it_tokens = ("bene", "grazie", "e tu", "tutto")
    assert any(t in reply.lower() for t in _it_tokens), \
        f"AT-2: reply doesn't look Italian: {reply!r}"
    assert _no_meta(reply), f"AT-2: meta-narration in reply: {reply!r}"
    ok(f"AT-2: 'come stai?' → Italian reply: {reply!r}")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: "ça va?" → French reply ────────────────────────────────────────────
try:
    result = _srv._detect_multilingual_how_are_you("ça va?")
    assert result is not None, "_detect_multilingual_how_are_you returned None for 'ça va?'"
    lang, reply = result
    assert lang == "french", f"expected lang='french', got {lang!r}"
    _fr_tokens = ("bien", "merci", "et toi", "ça va")
    assert any(t in reply.lower() for t in _fr_tokens), \
        f"AT-3: reply doesn't look French: {reply!r}"
    assert _no_meta(reply), f"AT-3: meta-narration in reply: {reply!r}"
    ok(f"AT-3: 'ça va?' → French reply: {reply!r}")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: "wie geht's?" → German reply ───────────────────────────────────────
try:
    result = _srv._detect_multilingual_how_are_you("wie geht's?")
    assert result is not None, "_detect_multilingual_how_are_you returned None for \"wie geht's?\""
    lang, reply = result
    assert lang == "german", f"expected lang='german', got {lang!r}"
    _de_tokens = ("gut", "danke", "und dir", "und du")
    assert any(t in reply.lower() for t in _de_tokens), \
        f"AT-4: reply doesn't look German: {reply!r}"
    assert _no_meta(reply), f"AT-4: meta-narration in reply: {reply!r}"
    ok(f"AT-4: \"wie geht's?\" → German reply: {reply!r}")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: "how are you?" → NOT matched by multilingual detector ───────────────
try:
    result = _srv._detect_multilingual_how_are_you("how are you?")
    assert result is None, f"English 'how are you?' should NOT match multilingual detector, got {result!r}"
    ok("AT-5: 'how are you?' → not matched by multilingual detector (English path unaffected)")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: "hola" → NOT matched by how-are-you detector ───────────────────────
try:
    result = _srv._detect_multilingual_how_are_you("hola")
    assert result is None, f"'hola' (pure greeting) should NOT match how-are-you detector, got {result!r}"
    ok("AT-6: 'hola' not matched — pure greeting path unaffected")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: WO-069 marker in server.py ─────────────────────────────────────────
try:
    with open("server.py", encoding="utf-8") as f:
        _src = f.read()
    assert "WO-069" in _src, "WO-069 marker not found in server.py"
    assert "_detect_multilingual_how_are_you" in _src, "detector not wired in server.py"
    assert "_MULTILINGUAL_HOW_ARE_YOU_PHRASES" in _src, "phrase map not in server.py"
    ok("AT-7: WO-069 marker + wiring confirmed in server.py")
except AssertionError as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-8: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-069 multilingual how-are-you  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
