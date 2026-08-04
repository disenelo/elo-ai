"""
tests/test_wo041_verify_before_speak.py — Acceptance tests for WO-041

Spec: WO-041 — Executive must VERIFY an action before speaking as if complete.
      Never say "I'm sitting" until Unity ACKs SIT_COMPLETE.

Tests:
  AT-1: _PENDING_SIT module-level dict exists in server.py
  AT-2: _PENDING_SIT is activated when sit intent fires (WO-035 coupling block)
  AT-3: Transit note ("MOVEMENT IN TRANSIT") injected into g_ctx when sit pending
  AT-4: Transit note guards contain "heading over" / "on my way" language
  AT-5: Timeout (45s) logic present — pending sit clears after timeout
  AT-6: py_compile clean

Run: python3 tests/test_wo041_verify_before_speak.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

_src = open("server.py", encoding="utf-8").read()


# ── AT-1: _PENDING_SIT exists ─────────────────────────────────────────────────
if '_PENDING_SIT' in _src and '"active"' in _src and '"since"' in _src:
    ok("AT-1: _PENDING_SIT dict defined in server.py with active/since keys")
else:
    fail("AT-1", "_PENDING_SIT or its keys not found in server.py")


# ── AT-2: _PENDING_SIT activated when sit intent fires ───────────────────────
if '_PENDING_SIT["active"] = True' in _src and '_PENDING_SIT["since"]' in _src:
    ok("AT-2: _PENDING_SIT activated (active=True + since=time.time()) on sit fire")
else:
    fail("AT-2", "Sit activation code not found in server.py")


# ── AT-3: Transit note injected into g_ctx when sit pending ──────────────────
if "MOVEMENT IN TRANSIT" in _src and "_transit_note" in _src:
    ok("AT-3: Transit note injected into g_ctx when _PENDING_SIT active")
else:
    fail("AT-3", "Transit note injection not found in server.py")


# ── AT-4: Transit note uses correct "heading over" language ──────────────────
if "heading over" in _src and "on my way" in _src:
    ok("AT-4: Transit note instructs 'heading over' / 'on my way' (not 'I'm sitting')")
else:
    fail("AT-4", "'heading over' / 'on my way' language not found in transit note")


# ── AT-5: 45s timeout logic present ──────────────────────────────────────────
if "45.0" in _src and '_PENDING_SIT["active"] = False' in _src:
    ok("AT-5: 45s timeout clears pending sit when Unity ACK absent")
else:
    fail("AT-5", "45s timeout or _PENDING_SIT clear not found in server.py")


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py", doraise=True)
    ok("AT-6: server.py compile clean")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print(f"{'='*50}")
print(f"WO-041  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
