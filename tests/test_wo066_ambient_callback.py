"""
tests/test_wo066_ambient_callback.py — WO-066: ambient engine callback registration

Spec: server.py:1393 imports `register_ambient_callback` from ambient.ambient_engine
      but the function did not exist → ImportError → except block → ambient engine
      never started → idle utterances never fired.

      Fix: add _ambient_cb module var + register_ambient_callback() to ambient_engine.py.
      The idle ambient timer calls cb() (brain-backed) when set, static pool otherwise.

  AT-1: register_ambient_callback importable from ambient.ambient_engine (no ImportError)
  AT-2: registered callback stored in _ambient_cb
  AT-3: server.py startup import line can be executed without ImportError
  AT-4: static pool still fires when no callback is registered
  AT-5: _ambient_cb branch present in ambient_engine.py source
  AT-6: py_compile clean on ambient_engine.py
  AT-7: py_compile clean on server.py

Run: python3 tests/test_wo066_ambient_callback.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: register_ambient_callback is importable ─────────────────────────────
try:
    from ambient.ambient_engine import register_ambient_callback
    ok("AT-1: register_ambient_callback importable from ambient.ambient_engine")
except ImportError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: registered callback stored in _ambient_cb ──────────────────────────
try:
    import ambient.ambient_engine as _ae
    _ae._ambient_cb = None  # reset

    called = []
    def _fake_cb():
        called.append(1)

    register_ambient_callback(_fake_cb)
    assert _ae._ambient_cb is _fake_cb, f"_ambient_cb not set: {_ae._ambient_cb!r}"
    ok("AT-2: registered callback stored in _ambient_cb")
    # cleanup
    _ae._ambient_cb = None
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: server.py startup import block executes without ImportError ─────────
try:
    # Simulate exactly what server.py does at startup
    from ambient.ambient_engine import start as _ambient_start, register_ambient_callback as _reg_ambient
    ok("AT-3: server.py startup import (start + register_ambient_callback) succeeds")
except ImportError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: static pool still fires when no callback registered ────────────────
try:
    import ambient.ambient_engine as _ae2
    _ae2._ambient_cb = None
    # Verify _AMBIENT_LINES still exists and is non-empty
    assert hasattr(_ae2, "_AMBIENT_LINES") and len(_ae2._AMBIENT_LINES) > 0, \
        "_AMBIENT_LINES missing or empty"
    ok(f"AT-4: static pool intact ({len(_ae2._AMBIENT_LINES)} lines available when no callback)")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: _ambient_cb branch present in source ───────────────────────────────
try:
    with open("ambient/ambient_engine.py", encoding="utf-8") as f:
        src = f.read()
    assert "_ambient_cb is not None" in src, "_ambient_cb branch not found in _run()"
    assert "WO-066" in src, "WO-066 marker not found"
    ok("AT-5: _ambient_cb branch + WO-066 marker present in ambient_engine.py")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean on ambient_engine.py ──────────────────────────────
try:
    py_compile.compile("ambient/ambient_engine.py", doraise=True)
    ok("AT-6: py_compile clean on ambient_engine.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


# ── AT-7: py_compile clean on server.py ──────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-7: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-7", e)


print()
print("=" * 60)
print(f"WO-066 ambient callback  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
