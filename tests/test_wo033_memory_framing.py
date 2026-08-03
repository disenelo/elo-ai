"""
tests/test_wo033_memory_framing.py — Acceptance tests for WO-033

Spec: WO-033 — eLo memory framing: real time/days, never "sessions"

Tests:
  AT-1: _SELF_REF_POOL contains no "session" strings
  AT-2: _memory_recall_response() does not say "session" in user-facing output
  AT-3: living_presence_spec.txt contains no user-facing "session" framing
  AT-4: prompts file uses time/day language instead of session language

CI guard: any "session" in user-facing memory language is a test failure.

Run: python3 tests/test_wo033_memory_framing.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: _SELF_REF_POOL contains no "session" strings ───────────────────────

try:
    from server import _SELF_REF_POOL
    _bad = [s for s in _SELF_REF_POOL if "session" in s.lower()]
    if _bad:
        fail("AT-1", f"found 'session' in _SELF_REF_POOL: {_bad}")
    else:
        ok("AT-1: _SELF_REF_POOL — no 'session' framing")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: _memory_recall_response() output is session-free ───────────────────

try:
    from server import _memory_recall_response
    _output = _memory_recall_response()
    if "session" in _output.lower():
        fail("AT-2", f"'session' found in memory recall output: {_output!r}")
    else:
        ok(f"AT-2: _memory_recall_response() — no 'session' framing (got: {_output!r})")
except Exception as e:
    fail("AT-2", e)


# ── AT-3/AT-4: living_presence_spec.txt — user-facing session language removed ──

try:
    _spec_path = os.path.join("prompts", "living_presence_spec.txt")
    with open(_spec_path, encoding="utf-8") as _f:
        _lines = _f.readlines()

    _bad_lines = []
    for _i, _ln in enumerate(_lines, 1):
        # Allow "session" only in non-user-facing technical comments (none exist in this file)
        if "session" in _ln.lower():
            _bad_lines.append((_i, _ln.rstrip()))

    if _bad_lines:
        fail("AT-3", f"'session' still present in living_presence_spec.txt: {_bad_lines}")
    else:
        ok("AT-3: living_presence_spec.txt — no 'session' framing")

    # AT-4: check the time/day alternatives are present
    _content = "".join(_lines)
    _time_phrases = ("days and weeks", "day to day", "over time", "here today, here tomorrow")
    _found = [p for p in _time_phrases if p in _content]
    if _found:
        ok(f"AT-4: prompts use time/day language — found: {_found}")
    else:
        fail("AT-4", "expected time/day phrases not found in living_presence_spec.txt")
except Exception as e:
    fail("AT-3/AT-4", e)


# ── Summary ───────────────────────────────────────────────────────────────────

print()
print(f"{'='*50}")
print(f"WO-033  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
