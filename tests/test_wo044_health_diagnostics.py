"""
tests/test_wo044_health_diagnostics.py — Acceptance tests for WO-044

Spec: Runtime /health diagnostics API
  1. GET /health returns 200 with per-faculty status dict
  2. All four faculties present in the response
  3. mark_degraded → /health reflects DEGRADED
  4. mark_recovered → /health reflects CONNECTED again
  5. server.py [FACULTY HEALTH] block wired into capability injection
  6. py_compile clean

Run: python3 tests/test_wo044_health_diagnostics.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: faculty_health module imports cleanly ───────────────────────────────
try:
    from runtime.faculty_health import (
        mark_degraded, mark_recovered, mark_offline,
        get_status, all_statuses, health_summary,
        CONNECTED, DEGRADED, OFFLINE,
    )
    ok("AT-1: runtime.faculty_health imports cleanly")
except Exception as e:
    fail("AT-1", e)
    sys.exit(1)


# ── AT-2: all four faculties present in all_statuses() ───────────────────────
try:
    statuses = all_statuses()
    required = {"reasoning", "memory", "tools", "embodiment"}
    missing  = required - set(statuses.keys())
    if missing:
        fail("AT-2", f"missing faculties: {missing}")
    else:
        ok(f"AT-2: all 4 faculties present — {list(statuses.keys())}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: mark_degraded → all_statuses reflects DEGRADED ─────────────────────
try:
    mark_recovered("tools")          # reset first
    mark_degraded("tools", "test-degraded")
    st = all_statuses()
    if st.get("tools") == DEGRADED:
        ok("AT-3: mark_degraded('tools') → all_statuses shows DEGRADED")
    else:
        fail("AT-3", f"expected DEGRADED, got {st.get('tools')}")
    mark_recovered("tools")          # clean up
except Exception as e:
    fail("AT-3", e)


# ── AT-4: mark_recovered → CONNECTED ─────────────────────────────────────────
try:
    mark_degraded("memory", "test")
    mark_recovered("memory")
    st = all_statuses()
    if st.get("memory") == CONNECTED:
        ok("AT-4: mark_recovered('memory') → all_statuses shows CONNECTED")
    else:
        fail("AT-4", f"expected CONNECTED, got {st.get('memory')}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: health_summary() includes all faculties ────────────────────────────
try:
    summary = health_summary()
    required_keys = ["reasoning", "memory", "tools", "embodiment"]
    missing = [k for k in required_keys if k not in summary]
    if missing:
        fail("AT-5", f"health_summary missing faculties: {missing}")
    else:
        ok(f"AT-5: health_summary() covers all faculties: {summary[:80]!r}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: /health route present in server.py ─────────────────────────────────
try:
    src = open("server.py", encoding="utf-8").read()
    if '"/health"' in src and "all_statuses" in src and "WO-044" in src:
        ok("AT-6: server.py has /health route wired to all_statuses (WO-044)")
    else:
        fail("AT-6", '"/health" route or all_statuses not found in server.py')
except Exception as e:
    fail("AT-6", e)


# ── AT-7: [FACULTY HEALTH] block wired into capability injection ──────────────
try:
    src = open("server.py", encoding="utf-8").read()
    if "FACULTY HEALTH" in src and "health_summary" in src and "are you working right" in src:
        ok("AT-7: [FACULTY HEALTH] block wired into capability injection in server.py")
    else:
        fail("AT-7", "FACULTY HEALTH / health_summary / 'are you working right' not all in server.py")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/faculty_health.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("AT-8: py_compile clean on faculty_health.py + server.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-044  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
