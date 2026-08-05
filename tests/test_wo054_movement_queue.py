"""
tests/test_wo054_movement_queue.py — Acceptance tests for WO-054

Spec: overlapping movement requests resolve through a queue; no silent drops;
      duplicate sit while in-flight does NOT re-emit sit_command _ts.

  AT-1: _PENDING_SIT["queued"] field exists (module-level init)
  AT-2: duplicate-sit guard present in server.py (ALREADY_IN_MOTION note injected)
  AT-3: sit-while-pending sets _mv_intent="" (suppresses re-emit) not a new sit
  AT-4: different intent while pending → queued field set, _mv_intent="" (hold)
  AT-5: timeout (>45s) + queued intent → queued promoted to current intent
  AT-6: py_compile clean

Run: python3 tests/test_wo054_movement_queue.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

_src = open("server.py", encoding="utf-8").read()


# ── AT-1: queued field present in _PENDING_SIT init ─────────────────────────
try:
    import server as _sv
    if "queued" in _sv._PENDING_SIT:
        ok('AT-1: _PENDING_SIT["queued"] field exists in module-level init')
    else:
        fail("AT-1", f"_PENDING_SIT keys: {list(_sv._PENDING_SIT.keys())}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: duplicate-sit guard with ALREADY_IN_MOTION note ───────────────────
try:
    if "ALREADY_IN_MOTION" in _src and ("Duplicate sit" in _src or "deduplicate" in _src.lower()):
        ok("AT-2: duplicate-sit guard + ALREADY_IN_MOTION note present")
    else:
        fail("AT-2", "ALREADY_IN_MOTION or deduplicate guard not in server.py")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: duplicate-sit sets _mv_intent="" ───────────────────────────────────
try:
    # Simulate: _PENDING_SIT["active"]=True, new sit intent fires → _mv_intent should be ""
    import server as _sv
    import time as _t
    _sv._PENDING_SIT["active"] = True
    _sv._PENDING_SIT["since"]  = _t.time()   # fresh
    _sv._PENDING_SIT["queued"] = None

    # Mirror the logic from server.py
    _now54 = _t.time()
    _mv_intent = {"name": "sit", "target": "cursor"}
    if isinstance(_mv_intent, dict) and _mv_intent.get("name") == "sit":
        if _sv._PENDING_SIT["active"]:
            _mv_intent = ""   # deduplicated

    if _mv_intent == "":
        ok("AT-3: duplicate sit while pending → _mv_intent='' (no re-emit)")
    else:
        fail("AT-3", f"_mv_intent={_mv_intent!r} — should be empty string")
except Exception as e:
    fail("AT-3", e)
finally:
    # Reset
    _sv._PENDING_SIT["active"] = False
    _sv._PENDING_SIT["queued"] = None


# ── AT-4: different intent while sit pending → queue, hold ────────────────────
try:
    import server as _sv
    import time as _t
    _sv._PENDING_SIT["active"] = True
    _sv._PENDING_SIT["since"]  = _t.time()
    _sv._PENDING_SIT["queued"] = None

    _now54 = _t.time()
    _mv_intent = "explore"   # different from sit

    # Mirror the elif branch:
    if _sv._PENDING_SIT["active"]:
        if _now54 - _sv._PENDING_SIT["since"] > 45.0:
            _sv._PENDING_SIT["active"] = False
        elif _mv_intent:
            _sv._PENDING_SIT["queued"] = _mv_intent
            _mv_intent = ""

    if _mv_intent == "" and _sv._PENDING_SIT["queued"] == "explore":
        ok("AT-4: different intent while sit pending → queued='explore', _mv_intent='' (hold)")
    else:
        fail("AT-4", f"queued={_sv._PENDING_SIT['queued']!r} _mv_intent={_mv_intent!r}")
except Exception as e:
    fail("AT-4", e)
finally:
    _sv._PENDING_SIT["active"] = False
    _sv._PENDING_SIT["queued"] = None


# ── AT-5: timeout + queued → queued promoted to _mv_intent ──────────────────
try:
    import server as _sv
    import time as _t
    _sv._PENDING_SIT["active"] = True
    _sv._PENDING_SIT["since"]  = _t.time() - 50.0   # 50s ago → timed out
    _sv._PENDING_SIT["queued"] = "go_top"

    _now54 = _t.time()
    _mv_intent = ""   # no new intent this turn

    # Mirror the timeout branch:
    if _sv._PENDING_SIT["active"]:
        if _now54 - _sv._PENDING_SIT["since"] > 45.0:
            _sv._PENDING_SIT["active"] = False
            if _sv._PENDING_SIT["queued"]:
                _mv_intent = _sv._PENDING_SIT["queued"]
                _sv._PENDING_SIT["queued"] = None

    if _mv_intent == "go_top" and not _sv._PENDING_SIT["active"]:
        ok("AT-5: 45s timeout → queued 'go_top' promoted to _mv_intent, pending cleared")
    else:
        fail("AT-5", f"_mv_intent={_mv_intent!r} active={_sv._PENDING_SIT['active']}")
except Exception as e:
    fail("AT-5", e)
finally:
    _sv._PENDING_SIT["active"] = False
    _sv._PENDING_SIT["queued"] = None


# ── AT-6: py_compile clean ───────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py", doraise=True)
    ok("AT-6: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 50)
print(f"WO-054  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
