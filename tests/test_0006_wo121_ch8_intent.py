"""
tests/test_0006_wo121_ch8_intent.py — Acceptance tests for WO-121 Ch.8 (card 0006).

Vol V Ch.8 Intent Relationship Engine — FT-1: five-category detection.

Tests:
    FT-1a  Build intent: "let's build" → category=Build
    FT-1b  Explore intent: weather query → category=Explore
    FT-1c  Reflect intent: recall query → category=Reflect
    FT-1d  Decide intent: timer command → category=Decide
    FT-1e  Connect intent: conversation → category=Connect
    FT-1f  category and reason fields present on every detect() call

Run: python3 tests/test_0006_wo121_ch8_intent.py
"""
import sys
sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from runtime.router.intent_engine import detect


_VALID_CATEGORIES = {"Build", "Explore", "Reflect", "Decide", "Connect"}


def _check(test_id, inp, expected_cat):
    r = detect(inp)
    cat  = r.get("category", "")
    reason = r.get("reason", "")
    intent = r.get("intent", "")
    if "category" not in r:
        fail(test_id, f"detect() missing 'category' key: {r}")
    elif "reason" not in r:
        fail(test_id, f"detect() missing 'reason' key: {r}")
    elif cat not in _VALID_CATEGORIES:
        fail(test_id, f"category {cat!r} not one of {_VALID_CATEGORIES}")
    elif cat != expected_cat:
        fail(test_id, f"expected category={expected_cat!r}, got {cat!r} (intent={intent!r})")
    else:
        ok(f"{test_id} — {inp!r} → {cat} (intent={intent!r}, reason={reason!r})")


print("\nFT-1a: Build intent → category=Build")
_check("FT-1a", "let's build a website", "Build")

print("\nFT-1b: Explore intent → category=Explore")
_check("FT-1b", "what's the weather like outside", "Explore")

print("\nFT-1c: Reflect intent → category=Reflect")
_check("FT-1c", "what did we work on last time", "Reflect")

print("\nFT-1d: Decide intent → category=Decide")
_check("FT-1d", "set a timer for 5 minutes", "Decide")

print("\nFT-1e: Connect intent → category=Connect")
_check("FT-1e", "tell me a story", "Connect")

print("\nFT-1f: category and reason present on every call")
try:
    for inp in ["hello", "build this now", "remember when", "should I use Python", "play some music"]:
        r = detect(inp)
        if "category" not in r or "reason" not in r:
            fail("FT-1f", f"missing keys on {inp!r}: {r}")
            break
        if r["category"] not in _VALID_CATEGORIES:
            fail("FT-1f", f"invalid category {r['category']!r} for {inp!r}")
            break
    else:
        ok("FT-1f — category + reason present and valid on all inputs")
except Exception as e:
    fail("FT-1f", repr(e))


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"WO-121 Ch.8 Intent (FT-1): {PASS} passed, {FAIL} failed")
if FAIL:
    sys.exit(1)
