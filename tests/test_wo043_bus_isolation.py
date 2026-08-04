"""
tests/test_wo043_bus_isolation.py — Acceptance tests for WO-043

Spec: WO-043 — Faculty Bus isolation; stop "weave it in" fact injection;
      tool outputs must not be asserted as personal truths.

Tests:
  AT-1: ambient cultural_facts prompt no longer says "use it naturally if the moment feels right"
  AT-2: ambient injection uses "CURIOUS FACT" framing (not FACT AVAILABLE)
  AT-3: ANTI-FABRICATION block in /chat path covers weather/area facts
  AT-4: ANTI-FABRICATION block bans "it's X in your studio" style assertions
  AT-5: server.py compile clean

Run: python3 tests/test_wo043_bus_isolation.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

_src = open("server.py", encoding="utf-8").read()


# ── AT-1: old "use it naturally if the moment feels right" removed ────────────
if "use it naturally in speak if the moment feels right" not in _src:
    ok("AT-1: old 'use it naturally' ambient injection phrase removed")
else:
    fail("AT-1", "'use it naturally in speak if the moment feels right' still present in server.py")


# ── AT-2: new ambient injection uses CURIOUS FACT framing ────────────────────
if "CURIOUS FACT" in _src:
    ok("AT-2: ambient injection now uses 'CURIOUS FACT' framing")
else:
    fail("AT-2", "'CURIOUS FACT' framing not found in server.py")


# ── AT-3: ANTI-FABRICATION block covers area/weather facts ───────────────────
if "AREA-LEVEL forecast" in _src or "area-level" in _src.lower():
    ok("AT-3: ANTI-FABRICATION block covers area-level weather/forecast facts")
else:
    fail("AT-3", "weather/area-level anti-fabrication not found in server.py")


# ── AT-4: ANTI-FABRICATION block bans studio-level weather assertions ─────────
if "your studio" in _src and "NEVER" in _src:
    # verify they appear together near each other (within 300 chars)
    idx = _src.find("your studio")
    window = _src[max(0, idx-200):idx+100]
    if "NEVER" in window or "never" in window:
        ok("AT-4: ANTI-FABRICATION explicitly bans 'X in your studio' assertions")
    else:
        fail("AT-4", "'your studio' found but no NEVER guard nearby")
else:
    fail("AT-4", "'your studio' anti-fabrication guard not found in server.py")


# ── AT-5: server.py compile clean ────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py", doraise=True)
    ok("AT-5: server.py compile clean")
except py_compile.PyCompileError as e:
    fail("AT-5", e)


print()
print(f"{'='*50}")
print(f"WO-043  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
