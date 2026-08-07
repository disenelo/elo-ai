"""
tests/test_wo039_f1_press_parse.py — WO-039-F1: "press" conversational false-positive fix

Spec: parse_intent() must NOT interpret "press on with that, that needs my attention"
      as a keyboard shortcut. _KEY_RE matched anything after "press " — conversational
      phrases became key combos joined with '+' (F1 live bug: "press on+with?+that+...").
      Fix: _is_valid_key_combo() rejects keys that aren't real keyboard tokens.

  AT-1: F1 live phrase → parse_intent returns None (not a key command)
  AT-2: "press cmd+c" → parse_intent returns key action (real shortcut still works)
  AT-3: "press ctrl shift t" → parse_intent returns key action
  AT-4: "press escape" → parse_intent returns key action
  AT-5: "press on with what's happening" → None (another conversational pattern)
  AT-6: "hit cmd v" → parse_intent returns key action (hit trigger word)
  AT-7: "hit me with your best shot" → None (conversational "hit")
  AT-8: _is_valid_key_combo([]) → False (empty list)
  AT-9: _is_valid_key_combo(["on", "with"]) → False (non-keys rejected)
  AT-10: _is_valid_key_combo(["cmd", "c"]) → True (valid combo)
  AT-11: describe() for a valid key action uses + notation correctly
  AT-12: py_compile clean on computer_control_agent.py

Run: python3 tests/test_wo039_f1_press_parse.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from tools.computer_control_agent import parse_intent, describe, _is_valid_key_combo


# ── AT-1: F1 live phrase → None ───────────────────────────────────────────────
try:
    r = parse_intent("press on with that, that needs my attention")
    assert r is None, f"expected None, got {r}"
    ok("AT-1: F1 live phrase 'press on with that...' → None (not a key command)")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: "press cmd+c" → key action ─────────────────────────────────────────
try:
    r = parse_intent("press cmd+c")
    assert r is not None and r["type"] == "key", f"expected key action, got {r}"
    assert "cmd" in r["keys"] and "c" in r["keys"], f"wrong keys: {r['keys']}"
    ok(f"AT-2: 'press cmd+c' → key action {r['keys']}")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: "press ctrl shift t" → key action ───────────────────────────────────
try:
    r = parse_intent("press ctrl shift t")
    assert r is not None and r["type"] == "key", f"expected key action, got {r}"
    ok(f"AT-3: 'press ctrl shift t' → key action {r['keys']}")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: "press escape" → key action ────────────────────────────────────────
try:
    r = parse_intent("press escape")
    assert r is not None and r["type"] == "key", f"expected key action, got {r}"
    ok(f"AT-4: 'press escape' → key action {r['keys']}")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: conversational "press on" → None ────────────────────────────────────
try:
    r = parse_intent("press on with what's happening here")
    assert r is None, f"expected None, got {r}"
    ok("AT-5: 'press on with...' → None (conversational)")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: "hit cmd v" → key action ───────────────────────────────────────────
try:
    r = parse_intent("hit cmd v")
    assert r is not None and r["type"] == "key", f"expected key action, got {r}"
    ok(f"AT-6: 'hit cmd v' → key action {r['keys']}")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: "hit me with your best shot" → None ─────────────────────────────────
try:
    r = parse_intent("hit me with your best shot")
    assert r is None, f"expected None, got {r}"
    ok("AT-7: 'hit me with your best shot' → None (conversational 'hit')")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: _is_valid_key_combo([]) → False ────────────────────────────────────
try:
    assert not _is_valid_key_combo([]), "empty list should return False"
    ok("AT-8: _is_valid_key_combo([]) → False")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)


# ── AT-9: non-keyboard words rejected ────────────────────────────────────────
try:
    assert not _is_valid_key_combo(["on", "with"]), "['on','with'] should return False"
    assert not _is_valid_key_combo(["needs", "my", "attention"]), "prose words → False"
    ok("AT-9: _is_valid_key_combo(['on','with']) → False; prose words rejected")
except AssertionError as e:
    fail("AT-9", e)
except Exception as e:
    fail("AT-9", e)


# ── AT-10: valid combo accepted ───────────────────────────────────────────────
try:
    assert _is_valid_key_combo(["cmd", "c"]), "['cmd','c'] should return True"
    assert _is_valid_key_combo(["ctrl", "shift", "t"]), "['ctrl','shift','t'] → True"
    assert _is_valid_key_combo(["esc"]), "['esc'] → True"
    ok("AT-10: _is_valid_key_combo(['cmd','c']) → True; valid combos accepted")
except AssertionError as e:
    fail("AT-10", e)
except Exception as e:
    fail("AT-10", e)


# ── AT-11: describe() formats valid key action with + notation ────────────────
try:
    action = {"type": "key", "keys": ["cmd", "c"]}
    desc = describe(action)
    assert "cmd" in desc and "c" in desc and "+" in desc, f"expected + notation in: {desc!r}"
    ok(f"AT-11: describe(key cmd+c) → {desc!r}")
except AssertionError as e:
    fail("AT-11", e)
except Exception as e:
    fail("AT-11", e)


# ── AT-12: py_compile clean ───────────────────────────────────────────────────
try:
    py_compile.compile("tools/computer_control_agent.py", doraise=True)
    ok("AT-12: py_compile clean on computer_control_agent.py")
except py_compile.PyCompileError as e:
    fail("AT-12", e)


print()
print("=" * 60)
print(f"WO-039-F1 press parse fix  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
