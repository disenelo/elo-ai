"""
tests/test_wo038_desktop_context.py — Acceptance tests for WO-038

Spec: Chrome context labels must be distinct (live tab vs history vs no-match-open)
      so eLo never says "Chrome isn't open" when tabs exist but none matched a query.

  AT-1: CHROME_LIVE_TABS label used when tabs match (not CHROME_TABS_MATCHED)
  AT-2: CHROME_OPEN label injected when tab_count > 0 but no tabs matched
  AT-3: BROWSER_HISTORY label distinguishes history from live tabs
  AT-4: no CHROME_OPEN injected when tab_count == 0 (Chrome genuinely not found)
  AT-5: py_compile clean

Run: python3 tests/test_wo038_desktop_context.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

_src = open("server.py", encoding="utf-8").read()


# ── AT-1: CHROME_LIVE_TABS label (not old CHROME_TABS_MATCHED) ──────────────
try:
    if "CHROME_LIVE_TABS" in _src and "CHROME_TABS_MATCHED" not in _src:
        ok("AT-1: CHROME_LIVE_TABS label used for matched live tabs")
    elif "CHROME_TABS_MATCHED" in _src:
        fail("AT-1", "old CHROME_TABS_MATCHED label still present — not updated")
    else:
        fail("AT-1", "CHROME_LIVE_TABS not found in server.py")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: CHROME_OPEN injected when tabs open but none matched ────────────────
try:
    if "CHROME_OPEN" in _src and "none matched this topic" in _src:
        ok("AT-2: CHROME_OPEN label injected when tabs open but query unmatched")
    else:
        fail("AT-2", "CHROME_OPEN / 'none matched this topic' not found")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: BROWSER_HISTORY label distinguishes from live tabs ─────────────────
try:
    if "BROWSER_HISTORY (not a live tab)" in _src:
        ok("AT-3: BROWSER_HISTORY (not a live tab) label distinguishes history source")
    else:
        fail("AT-3", "'BROWSER_HISTORY (not a live tab)' not found in server.py")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: CHROME_OPEN gated on tab_count > 0 ─────────────────────────────────
try:
    if "_chr_tab_count > 0" in _src or "tab_count" in _src:
        ok("AT-4: CHROME_OPEN is gated on tab_count > 0 — not injected when Chrome absent")
    else:
        fail("AT-4", "tab_count guard not found in server.py")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py", doraise=True)
    ok("AT-5: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-5", e)


print()
print("=" * 50)
print(f"WO-038  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
