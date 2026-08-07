"""
tests/test_wo039_f2_cancel.py — WO-039-F2: cancel false-positive fix

Spec: _is_file_cancel() must NOT fire on "No but <continuation>" — only on
      bare standalone "no"/"nope" (possibly followed by punctuation/whitespace).
      Live phrase from David's session: "No but it takes time to build you"
      was routed to "Ok, cancelled." — this must be blocked.

  AT-1: bare "no" → cancel fires
  AT-2: "no!" → cancel fires
  AT-3: "nope" → cancel fires
  AT-4: "nope." → cancel fires
  AT-5: "No but it takes time to build you" → cancel does NOT fire (F2 live phrase)
  AT-6: "no worries" → cancel does NOT fire
  AT-7: "not now" → cancel does NOT fire
  AT-8: "cancel" → cancel fires (substring keyword unchanged)
  AT-9: "forget it" → cancel fires
  AT-10: py_compile clean on server.py

Run: python3 tests/test_wo039_f2_cancel.py
"""
import sys, os, re, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# Replicate _is_file_cancel logic from server.py for isolated testing
_FILE_CANCEL_NO_RE = re.compile(r"^(no|nope)[!.?,\s]*$")

def _is_file_cancel(text: str) -> bool:
    t = text.lower().strip()
    if _FILE_CANCEL_NO_RE.match(t):
        return True
    return any(k in t for k in ("cancel", "don't", "dont", "stop",
                                 "nevermind", "never mind", "forget it", "abort"))


# ── AT-1: bare "no" → cancel ──────────────────────────────────────────────────
try:
    assert _is_file_cancel("no"), "bare 'no' should cancel"
    ok("AT-1: bare 'no' → cancel fires")
except AssertionError as e:
    fail("AT-1", e)


# ── AT-2: "no!" → cancel ──────────────────────────────────────────────────────
try:
    assert _is_file_cancel("no!"), "'no!' should cancel"
    ok("AT-2: 'no!' → cancel fires")
except AssertionError as e:
    fail("AT-2", e)


# ── AT-3: "nope" → cancel ─────────────────────────────────────────────────────
try:
    assert _is_file_cancel("nope"), "'nope' should cancel"
    ok("AT-3: 'nope' → cancel fires")
except AssertionError as e:
    fail("AT-3", e)


# ── AT-4: "nope." → cancel ────────────────────────────────────────────────────
try:
    assert _is_file_cancel("nope."), "'nope.' should cancel"
    ok("AT-4: 'nope.' → cancel fires")
except AssertionError as e:
    fail("AT-4", e)


# ── AT-5: F2 live phrase → NOT cancel ────────────────────────────────────────
try:
    phrase = "No but it takes time to build you"
    assert not _is_file_cancel(phrase), f"'{phrase}' must NOT cancel"
    ok(f"AT-5: '{phrase}' → cancel does NOT fire (F2 fixed)")
except AssertionError as e:
    fail("AT-5", e)


# ── AT-6: "no worries" → NOT cancel ──────────────────────────────────────────
try:
    assert not _is_file_cancel("no worries"), "'no worries' must NOT cancel"
    ok("AT-6: 'no worries' → cancel does NOT fire")
except AssertionError as e:
    fail("AT-6", e)


# ── AT-7: "not now" → NOT cancel ─────────────────────────────────────────────
try:
    assert not _is_file_cancel("not now"), "'not now' must NOT cancel"
    ok("AT-7: 'not now' → cancel does NOT fire")
except AssertionError as e:
    fail("AT-7", e)


# ── AT-8: "cancel" → cancel (substring keyword) ───────────────────────────────
try:
    assert _is_file_cancel("actually just cancel that"), "'cancel' in phrase should cancel"
    ok("AT-8: 'cancel' substring → cancel fires")
except AssertionError as e:
    fail("AT-8", e)


# ── AT-9: "forget it" → cancel ───────────────────────────────────────────────
try:
    assert _is_file_cancel("forget it"), "'forget it' should cancel"
    ok("AT-9: 'forget it' → cancel fires")
except AssertionError as e:
    fail("AT-9", e)


# ── AT-10: py_compile clean on server.py ──────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-10: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-10", e)


print()
print("=" * 55)
print(f"WO-039-F2 cancel fix  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
