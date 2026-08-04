"""
tests/test_wo039_garbled_routing.py — Acceptance tests for WO-039

Spec: WO-039 — intent-parse corruption: "built" fuzzy-matched to "quit",
      system intent misfires, grammar/command content leaks into replies.

Tests:
  AT-1: "built" is in _PROTECTED — never fuzzy-repaired to "quit"
  AT-2: _COMMAND_WORDS guard: "built"→"quit" (dist 2) rejected by fuzzy matcher
  AT-3: intent_engine system pattern requires sentence-start (no mid-sentence match)
  AT-4: "Yeah so everything I built is related" does NOT classify as system intent
  AT-5: A real quit command ("quit Finder") still classifies as system intent
  AT-6: py_compile clean

Run: python3 tests/test_wo039_garbled_routing.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: "built" is protected ────────────────────────────────────────────────
try:
    from runtime.router.typo_engine import _PROTECTED
    if "built" in _PROTECTED:
        ok("AT-1: 'built' is in _PROTECTED — cannot be fuzzy-repaired")
    else:
        fail("AT-1", "'built' not found in _PROTECTED")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: fuzzy matcher rejects "built"→"quit" via _COMMAND_WORDS guard ──────
try:
    from runtime.router.typo_engine import _fuzzy_match
    result = _fuzzy_match("built")
    if result is None:
        ok("AT-2: _fuzzy_match('built') returns None (command-word guard)")
    else:
        fail("AT-2", f"expected None, got {result}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: intent system pattern requires sentence start ───────────────────────
try:
    import re
    _src = open("runtime/router/intent_engine.py", encoding="utf-8").read()
    # The old pattern was r"\b(?:quit|close|kill)\s+\w+\b" — no anchor
    # The new pattern must start with ^ (or equivalent sentence-start anchor)
    if "^(?:please" in _src and "quit|exit|close|kill" in _src:
        ok("AT-3: system pattern anchored at sentence start (^ found)")
    else:
        fail("AT-3", "sentence-start anchor not found in system intent pattern")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: "built" sentence → NOT system intent ───────────────────────────────
try:
    from runtime.router.intent_engine import detect
    r = detect("yeah so everything i built is related")
    if r["intent"] != "system":
        ok(f"AT-4: 'everything i built is related' → intent={r['intent']!r} (not system)")
    else:
        fail("AT-4", f"classified as 'system' — garble still fires")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: real quit command still classifies as system ────────────────────────
try:
    from runtime.router.intent_engine import detect
    r = detect("quit finder")
    if r["intent"] == "system":
        ok("AT-5: 'quit Finder' → intent=system (real command still works)")
    else:
        fail("AT-5", f"expected system, got {r['intent']!r}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/router/typo_engine.py", doraise=True)
    py_compile.compile("runtime/router/intent_engine.py", doraise=True)
    ok("AT-6: py_compile clean on typo_engine and intent_engine")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print(f"{'='*50}")
print(f"WO-039  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
