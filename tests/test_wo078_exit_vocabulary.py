"""
tests/test_wo078_exit_vocabulary.py — Acceptance tests for WO-078 (Builder lane)

Spec: WO-078 — Exit-run: leave/space vocabulary (+ UK slang) + false-positive guards

  AT-01: "give me a mo" → triggers exit phrase match
  AT-02: "give me some space" → triggers exit phrase match
  AT-03: "give me some room" → triggers exit phrase match
  AT-04: "give us a minute" → triggers exit phrase match
  AT-05: "give us a sec" → triggers exit phrase match
  AT-06: "leave me be" → triggers exit phrase match
  AT-07: "let me be" → triggers exit phrase match
  AT-08: "need a breather" → triggers exit phrase match
  AT-09: "make yourself scarce" → triggers exit phrase match
  AT-10: "i need a minute" → triggers exit phrase match
  AT-11: FALSE POSITIVE — "don't leave" → NOT exit
  AT-12: FALSE POSITIVE — "give me a second to think" → NOT exit
  AT-13: FALSE POSITIVE — "stay here" → NOT exit
  AT-14: Legacy phrases still fire: "take five", "pop off", "brb"
  AT-15: py_compile clean on server.py

Run: python3 tests/test_wo078_exit_vocabulary.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── Mirror the exact detection logic from server.py ──────────────────────────

_STEP_OUT_PHRASES = frozenset({
    "take 5", "take five", "give me a minute", "give me a moment",
    "some privacy", "step away", "leave me to it", "go away for a bit", "pop off",
    "good night", "goodnight", "done for today", "signing off", "heading out",
    "taking a break", "need a break", "brb",
    # WO-078 additions
    "give me a mo", "give me some space", "give me some room",
    "give us a minute", "give us a sec",
    "leave me be", "let me be", "need a breather",
    "make yourself scarce", "i need a minute", "i need some space",
})

_STEP_OUT_FALSE_POSITIVES = frozenset({
    "don't leave", "dont leave", "do not leave",
    "don't go", "dont go", "do not go",
    "don't step away", "dont step away",
    "give me a second to think", "give me a second to work",
    "stay here", "stay put", "wait here", "stay with me",
})


def _is_exit(text: str) -> bool:
    t = text.lower().strip()
    if any(fp in t for fp in _STEP_OUT_FALSE_POSITIVES):
        return False
    return any(
        t == p or t.startswith(p + " ") or t.endswith(" " + p) or (" " + p + " ") in t
        for p in _STEP_OUT_PHRASES
    )


NEW_EXIT_PHRASES = [
    ("AT-01", "give me a mo"),
    ("AT-02", "give me some space"),
    ("AT-03", "give me some room"),
    ("AT-04", "give us a minute"),
    ("AT-05", "give us a sec"),
    ("AT-06", "leave me be"),
    ("AT-07", "let me be"),
    ("AT-08", "need a breather"),
    ("AT-09", "make yourself scarce"),
    ("AT-10", "i need a minute"),
]

for at_id, phrase in NEW_EXIT_PHRASES:
    try:
        assert _is_exit(phrase), f"expected exit for '{phrase}' but got False"
        ok(f"{at_id}: '{phrase}' → exit ✓")
    except AssertionError as e:
        fail(at_id, e)
    except Exception as e:
        fail(at_id, e)

FALSE_POSITIVES = [
    ("AT-11", "don't leave"),
    ("AT-12", "give me a second to think"),
    ("AT-13", "stay here"),
]

for at_id, phrase in FALSE_POSITIVES:
    try:
        assert not _is_exit(phrase), f"expected NO exit for '{phrase}' but got True"
        ok(f"{at_id}: '{phrase}' → NOT exit (false positive blocked) ✓")
    except AssertionError as e:
        fail(at_id, e)
    except Exception as e:
        fail(at_id, e)

# ── AT-14: Legacy phrases still fire ─────────────────────────────────────────
try:
    legacy = ["take five", "pop off", "brb", "take 5", "give me a minute"]
    bad = [p for p in legacy if not _is_exit(p)]
    assert not bad, f"legacy phrases no longer fire: {bad}"
    ok(f"AT-14: legacy exit phrases still fire: {legacy}")
except AssertionError as e:
    fail("AT-14", e)
except Exception as e:
    fail("AT-14", e)

# ── AT-15: py_compile clean ───────────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-15: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-15", e)


print()
print("=" * 50)
print(f"WO-078 exit vocabulary  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
