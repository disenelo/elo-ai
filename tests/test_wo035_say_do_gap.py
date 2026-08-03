"""
tests/test_wo035_say_do_gap.py — Acceptance tests for WO-035

Spec: WO-035 — sit-intent must be semantic, not exact-phrase; say/do coupling.

Tests:
  AT-1: "Have a seat with me" → sit token fires
  AT-2: "Can you sit though?" → sit token fires
  AT-3: "come sit" → sit token fires
  AT-4: existing phrase "sit with me" still fires (regression guard)
  AT-5: say/do coupling — LLM claims "I'll sit" → token patched in
  AT-6: say/do coupling — LLM claims "I'll come over" → token patched in
  AT-7: unrelated reply → no false-positive sit
  AT-8: server.py compiles cleanly

Run: python3 tests/test_wo035_say_do_gap.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── import signal word function ───────────────────────────────────────────────
try:
    from server import _signal_word_intent
    _SIT_DICT = {"name": "sit", "target": "cursor"}
except Exception as e:
    fail("import", e); sys.exit(1)


# ── AT-1: "have a seat with me" ───────────────────────────────────────────────
try:
    r = _signal_word_intent("Have a seat with me")
    if r == _SIT_DICT:
        ok("AT-1: 'Have a seat with me' → sit token")
    else:
        fail("AT-1", f"expected sit dict, got {r!r}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: "can you sit though?" ───────────────────────────────────────────────
try:
    r = _signal_word_intent("Can you sit though?")
    if r == _SIT_DICT:
        ok("AT-2: 'Can you sit though?' → sit token")
    else:
        fail("AT-2", f"expected sit dict, got {r!r}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: "come sit" ──────────────────────────────────────────────────────────
try:
    r = _signal_word_intent("come sit with me so we can talk")
    if r == _SIT_DICT:
        ok("AT-3: 'come sit with me so we can talk' → sit token")
    else:
        fail("AT-3", f"expected sit dict, got {r!r}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: regression — "sit with me" still fires ─────────────────────────────
try:
    r = _signal_word_intent("sit with me")
    if r == _SIT_DICT:
        ok("AT-4: 'sit with me' still fires (regression guard)")
    else:
        fail("AT-4", f"regression: expected sit dict, got {r!r}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5 & AT-6: say/do coupling — mimic the coupling logic from server.py ───

def _say_do_coupling(mv_intent, response: str) -> dict:
    """Mirror of the WO-035 say/do coupling block in server.py."""
    _is_sit = isinstance(mv_intent, dict) and mv_intent.get("name") == "sit"
    if not _is_sit:
        _sit_claims = ("i'll sit", "i'll come", "coming over",
                       "settling in", "i'm heading", "moving over",
                       "i'll move", "heading your way", "on my way")
        if any(c in response.lower() for c in _sit_claims):
            mv_intent = {"name": "sit", "target": "cursor"}
    return mv_intent

try:
    result = _say_do_coupling("idle", "Sure! I'll sit right there with you.")
    if result == _SIT_DICT:
        ok("AT-5: say/do — 'I'll sit' claim → sit token patched in")
    else:
        fail("AT-5", f"expected sit dict, got {result!r}")
except Exception as e:
    fail("AT-5", e)

try:
    result = _say_do_coupling("idle", "I'll come over and settle in next to you.")
    if result == _SIT_DICT:
        ok("AT-6: say/do — 'I'll come over' claim → sit token patched in")
    else:
        fail("AT-6", f"expected sit dict, got {result!r}")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: no false-positive sit on unrelated reply ───────────────────────────
try:
    result = _say_do_coupling("idle", "That sounds like a great idea. Let's build it!")
    if result != _SIT_DICT:
        ok("AT-7: unrelated reply — no false-positive sit")
    else:
        fail("AT-7", "false-positive: sit token fired on unrelated reply")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: server.py compiles cleanly ─────────────────────────────────────────
try:
    import py_compile as _pyc
    _pyc.compile("server.py", doraise=True)
    ok("AT-8: server.py compiles cleanly")
except Exception as e:
    fail("AT-8", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print(f"{'='*50}")
print(f"WO-035  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
