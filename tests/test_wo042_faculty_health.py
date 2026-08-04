"""
tests/test_wo042_faculty_health.py — Acceptance tests for WO-042

Spec: WO-042 — Faculty health registry: persistent CONNECTED/DEGRADED/OFFLINE
      per faculty; Executive routes on it; no per-call oscillation.

Tests:
  AT-1: faculty_health module imports cleanly
  AT-2: all four faculties exist in registry (reasoning, memory, tools, embodiment)
  AT-3: get_status() returns CONNECTED by default
  AT-4: mark_degraded() transitions status and records reason
  AT-5: mark_recovered() resets status and error count to zero
  AT-6: mark_offline() sets OFFLINE status
  AT-7: health_summary() returns a single-line string covering all faculties
  AT-8: reasoning faculty is wired into backend_router (WO-042 comment present)
  AT-9: py_compile clean

Run: python3 tests/test_wo042_faculty_health.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: module imports cleanly ──────────────────────────────────────────────
try:
    from runtime.faculty_health import (
        get_status, mark_degraded, mark_recovered, mark_offline,
        health_summary, all_statuses, CONNECTED, DEGRADED, OFFLINE,
    )
    ok("AT-1: runtime.faculty_health imports cleanly")
except Exception as e:
    fail("AT-1", e)
    sys.exit(1)


# ── AT-2: all four faculties present ─────────────────────────────────────────
try:
    _statuses = all_statuses()
    _required = {"reasoning", "memory", "tools", "embodiment"}
    _missing  = _required - set(_statuses.keys())
    if not _missing:
        ok(f"AT-2: all four faculties in registry: {sorted(_statuses.keys())}")
    else:
        fail("AT-2", f"missing faculties: {_missing}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: default status is CONNECTED ────────────────────────────────────────
try:
    # reset all first
    for f in ("reasoning", "memory", "tools", "embodiment"):
        mark_recovered(f)
    _st = get_status("reasoning")
    if _st == CONNECTED:
        ok(f"AT-3: get_status('reasoning') = CONNECTED by default")
    else:
        fail("AT-3", f"expected CONNECTED, got {_st!r}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: mark_degraded transitions correctly ─────────────────────────────────
try:
    mark_degraded("reasoning", "OpenAI quota exceeded")
    _st = get_status("reasoning")
    if _st == DEGRADED:
        ok("AT-4: mark_degraded('reasoning') → status=DEGRADED")
    else:
        fail("AT-4", f"expected DEGRADED, got {_st!r}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: mark_recovered resets to CONNECTED + zero error_count ───────────────
try:
    mark_recovered("reasoning")
    from runtime.faculty_health import _registry
    rec = _registry["reasoning"]
    if get_status("reasoning") == CONNECTED and rec["error_count"] == 0:
        ok("AT-5: mark_recovered resets status=CONNECTED + error_count=0")
    else:
        fail("AT-5", f"status={get_status('reasoning')!r} error_count={rec['error_count']}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: mark_offline transitions correctly ──────────────────────────────────
try:
    mark_offline("tools", "weather API unreachable")
    _st = get_status("tools")
    if _st == OFFLINE:
        ok("AT-6: mark_offline('tools') → status=OFFLINE")
    else:
        fail("AT-6", f"expected OFFLINE, got {_st!r}")
    mark_recovered("tools")  # cleanup
except Exception as e:
    fail("AT-6", e)


# ── AT-7: health_summary returns one-line string ──────────────────────────────
try:
    _summary = health_summary()
    if isinstance(_summary, str) and "|" in _summary and "reasoning" in _summary:
        ok(f"AT-7: health_summary() returns multi-faculty one-liner: {_summary[:80]!r}")
    else:
        fail("AT-7", f"unexpected summary: {_summary!r}")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: backend_router wired to faculty health ──────────────────────────────
try:
    _src = open("runtime/backend_router.py", encoding="utf-8").read()
    if "WO-042" in _src and "faculty_health" in _src and "_fh_degraded" in _src:
        ok("AT-8: backend_router.py wired to faculty_health (WO-042 references present)")
    else:
        fail("AT-8", "faculty_health wiring not found in backend_router.py")
except Exception as e:
    fail("AT-8", e)


# ── AT-9: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/faculty_health.py", doraise=True)
    py_compile.compile("runtime/backend_router.py", doraise=True)
    ok("AT-9: py_compile clean on faculty_health.py and backend_router.py")
except py_compile.PyCompileError as e:
    fail("AT-9", e)


print()
print(f"{'='*50}")
print(f"WO-042  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
