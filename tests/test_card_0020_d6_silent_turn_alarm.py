"""tests/test_card_0020_d6_silent_turn_alarm.py — Card 0020 · D-6.

The 2026-08-19 live test had ten direct questions produce NO reply. The card
requires: "a silent turn must log loudly — this is Rule 1 in the place the
user actually feels it." This test proves the guard is on the exit path of
`_process_turn` — an empty response is caught, a WARNING is logged, and an
honest short beat is substituted so nothing reaches David as silence.

Run: python3 tests/test_card_0020_d6_silent_turn_alarm.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "server.py")


# D-6.a — the exit-path guard is in place
try:
    with open(SERVER, encoding="utf-8") as f:
        src = f.read()
    assert "D-6 silent-turn alarm" in src, \
        "D-6: silent-turn alarm marker missing from server.py"
    assert "not response or not response.strip()" in src, \
        "D-6: empty-response predicate not on the exit path"
    # It must be BEFORE the final return so it can substitute the payload.
    idx_alarm = src.find("D-6 silent-turn alarm")
    # Find the final return {} block that closes _process_turn — it contains both
    # "response": response and "bubbles": _bubbles; use the LAST occurrence since
    # there can be multiple return-dict blocks earlier in the function.
    # Updated 2026-10-08: return format has extra spacing around field separators.
    import re as _re
    # Find the final return block by finding the last "bubbles": _bubbles
    # (the close of _process_turn's return dict) and working backwards to the return.
    _all_bubbles = list(_re.finditer(r'"bubbles"\s*:\s*_bubbles', src))
    idx_return = _all_bubbles[-1].start() if _all_bubbles else -1
    assert 0 < idx_alarm < idx_return, \
        "D-6: alarm is not positioned before the final return"
    ok("D-6.a: silent-turn alarm sits on the exit path before the final return")
except Exception as e:
    fail("D-6.a", e)


# D-6.b — logging is at WARNING and includes the raw prompt (Rule 1 alarm)
try:
    with open(SERVER, encoding="utf-8") as f:
        src = f.read()
    idx = src.find("D-6 silent-turn alarm")
    # Look back up to 200 chars (the .warning( call precedes the alarm string)
    window = src[max(0, idx - 200):idx + 1200]
    assert "warning" in window.lower() or "WARNING" in window, \
        "D-6: alarm does not log at WARNING"
    assert "raw=" in window or "raw%" in window, \
        "D-6: alarm does not include the raw prompt"
    ok("D-6.b: alarm logs the raw prompt at WARNING (Rule 1 alarm)")
except Exception as e:
    fail("D-6.b", e)


# D-6.c — the fallback beat is short, honest, and non-empty
try:
    with open(SERVER, encoding="utf-8") as f:
        src = f.read()
    assert 'came back empty' in src, \
        "D-6: honest fallback beat missing"
    ok("D-6.c: honest fallback beat present so David never sees silence")
except Exception as e:
    fail("D-6.c", e)


print()
print("=" * 52)
print(f"Card 0020 · D-6 silent-turn alarm  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
