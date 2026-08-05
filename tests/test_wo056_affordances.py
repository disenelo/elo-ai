"""
tests/test_wo056_affordances.py — Acceptance tests for WO-056

Spec: affordances field on CognitiveSnapshot — Executive searches
POSSIBILITIES not animations (ADR-Exec-003 LAW).

  AT-1: SURFACE_AFFORDANCES populated for expected surface types
  AT-2: window_top includes expected verbs (stand, run, jump, peek, enter, exit)
  AT-3: window_body includes wall-run, climb, hide, peek
  AT-4: desktop_floor includes stand, run, jump (no peek)
  AT-5: unknown surface falls back to stand, run
  AT-6: CognitiveSnapshot has surface_type and surface_affordances fields
  AT-7: build_snapshot() returns surface_affordances as a non-empty tuple
  AT-8: py_compile clean on affordances.py + cognitive_snapshot.py

Run: python3 tests/test_wo056_affordances.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: SURFACE_AFFORDANCES populated ──────────────────────────────────────
try:
    from runtime.affordances import SURFACE_AFFORDANCES
    expected_keys = {"window_top", "window_body", "desktop_floor", "unknown"}
    missing = expected_keys - set(SURFACE_AFFORDANCES.keys())
    if not missing:
        ok(f"AT-1: SURFACE_AFFORDANCES has {len(SURFACE_AFFORDANCES)} surface types")
    else:
        fail("AT-1", f"missing keys: {missing}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: window_top verbs ────────────────────────────────────────────────────
try:
    from runtime.affordances import SURFACE_AFFORDANCES
    verbs = SURFACE_AFFORDANCES["window_top"]
    expected = {"stand", "run", "jump", "peek", "enter", "exit"}
    missing = expected - verbs
    if not missing:
        ok(f"AT-2: window_top has expected verbs: {sorted(verbs)}")
    else:
        fail("AT-2", f"window_top missing: {missing}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: window_body verbs ───────────────────────────────────────────────────
try:
    from runtime.affordances import SURFACE_AFFORDANCES
    verbs = SURFACE_AFFORDANCES["window_body"]
    expected = {"wall-run", "climb", "hide", "peek"}
    missing = expected - verbs
    if not missing:
        ok(f"AT-3: window_body has expected verbs: {sorted(verbs)}")
    else:
        fail("AT-3", f"window_body missing: {missing}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: desktop_floor verbs ────────────────────────────────────────────────
try:
    from runtime.affordances import SURFACE_AFFORDANCES
    verbs = SURFACE_AFFORDANCES["desktop_floor"]
    required = {"stand", "run", "jump"}
    excluded = {"peek", "wall-run", "climb"}
    has_required = required.issubset(verbs)
    has_excluded = bool(excluded & verbs)
    if has_required and not has_excluded:
        ok(f"AT-4: desktop_floor has stand/run/jump, excludes peek/wall-run/climb")
    else:
        fail("AT-4", f"verbs={sorted(verbs)} req_ok={has_required} excl={excluded & verbs}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: unknown surface fallback ────────────────────────────────────────────
try:
    from runtime.affordances import affordances_for
    verbs = affordances_for("totally_unknown_surface")
    if "stand" in verbs and "run" in verbs:
        ok(f"AT-5: unknown surface falls back to stand+run: {verbs}")
    else:
        fail("AT-5", f"fallback affordances: {verbs}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: CognitiveSnapshot has surface_type + surface_affordances fields ─────
try:
    from runtime.cognitive_snapshot import CognitiveSnapshot
    snap = CognitiveSnapshot()
    if hasattr(snap, "surface_type") and hasattr(snap, "surface_affordances"):
        if isinstance(snap.surface_type, str) and isinstance(snap.surface_affordances, tuple):
            ok(f"AT-6: CognitiveSnapshot has surface_type (str) + surface_affordances (tuple)")
        else:
            fail("AT-6", f"wrong types: surface_type={type(snap.surface_type).__name__} surface_affordances={type(snap.surface_affordances).__name__}")
    else:
        missing = [f for f in ["surface_type", "surface_affordances"] if not hasattr(snap, f)]
        fail("AT-6", f"missing fields: {missing}")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: build_snapshot() returns surface_affordances tuple ─────────────────
try:
    from runtime.cognitive_snapshot import build_snapshot
    snap = build_snapshot()
    if isinstance(snap.surface_affordances, tuple):
        ok(f"AT-7: build_snapshot() surface_affordances={snap.surface_affordances} (surface={snap.surface_type!r})")
    else:
        fail("AT-7", f"surface_affordances type: {type(snap.surface_affordances).__name__}")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/affordances.py",        doraise=True)
    py_compile.compile("runtime/cognitive_snapshot.py", doraise=True)
    ok("AT-8: py_compile clean on affordances.py + cognitive_snapshot.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-056  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
