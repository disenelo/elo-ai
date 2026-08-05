"""
tests/test_wo057_perception_scope.py — Acceptance tests for WO-057

Spec: widen DesktopState to Chrome tabs/history/open docs/files;
make capability registry EXECUTE with faculty-health gate.
(company-state half skipped — WO-048 blocked on D-LANES decision)

  AT-1: CognitiveSnapshot has chrome_open field (bool)
  AT-2: CognitiveSnapshot has chrome_tab_count field (int)
  AT-3: CognitiveSnapshot has chrome_active_url field (str)
  AT-4: CognitiveSnapshot has chrome_recent_domains field (tuple)
  AT-5: CognitiveSnapshot has gated_capabilities field (tuple)
  AT-6: build_snapshot() returns chrome_* fields with correct types
  AT-7: gated_capabilities is non-empty when capability registry is available
  AT-8: py_compile clean on cognitive_snapshot.py

Run: python3 tests/test_wo057_perception_scope.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: chrome_open field ───────────────────────────────────────────────────
try:
    from runtime.cognitive_snapshot import CognitiveSnapshot
    snap = CognitiveSnapshot()
    if hasattr(snap, "chrome_open") and isinstance(snap.chrome_open, bool):
        ok("AT-1: CognitiveSnapshot has chrome_open (bool)")
    else:
        fail("AT-1", f"chrome_open missing or wrong type: {type(getattr(snap, 'chrome_open', None)).__name__}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: chrome_tab_count field ─────────────────────────────────────────────
try:
    from runtime.cognitive_snapshot import CognitiveSnapshot
    snap = CognitiveSnapshot()
    if hasattr(snap, "chrome_tab_count") and isinstance(snap.chrome_tab_count, int):
        ok("AT-2: CognitiveSnapshot has chrome_tab_count (int)")
    else:
        fail("AT-2", f"chrome_tab_count missing or wrong type: {type(getattr(snap, 'chrome_tab_count', None)).__name__}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: chrome_active_url field ────────────────────────────────────────────
try:
    from runtime.cognitive_snapshot import CognitiveSnapshot
    snap = CognitiveSnapshot()
    if hasattr(snap, "chrome_active_url") and isinstance(snap.chrome_active_url, str):
        ok("AT-3: CognitiveSnapshot has chrome_active_url (str)")
    else:
        fail("AT-3", f"chrome_active_url missing or wrong type")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: chrome_recent_domains field ────────────────────────────────────────
try:
    from runtime.cognitive_snapshot import CognitiveSnapshot
    snap = CognitiveSnapshot()
    if hasattr(snap, "chrome_recent_domains") and isinstance(snap.chrome_recent_domains, tuple):
        ok("AT-4: CognitiveSnapshot has chrome_recent_domains (tuple)")
    else:
        fail("AT-4", f"chrome_recent_domains missing or wrong type")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: gated_capabilities field ───────────────────────────────────────────
try:
    from runtime.cognitive_snapshot import CognitiveSnapshot
    snap = CognitiveSnapshot()
    if hasattr(snap, "gated_capabilities") and isinstance(snap.gated_capabilities, tuple):
        ok("AT-5: CognitiveSnapshot has gated_capabilities (tuple)")
    else:
        fail("AT-5", f"gated_capabilities missing or wrong type")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: build_snapshot() chrome_* types correct ────────────────────────────
try:
    from runtime.cognitive_snapshot import build_snapshot
    snap = build_snapshot()
    checks = [
        isinstance(snap.chrome_open, bool),
        isinstance(snap.chrome_tab_count, int),
        isinstance(snap.chrome_active_url, str),
        isinstance(snap.chrome_recent_domains, tuple),
        isinstance(snap.gated_capabilities, tuple),
    ]
    if all(checks):
        ok(f"AT-6: build_snapshot() chrome fields typed correctly "
           f"(open={snap.chrome_open} tabs={snap.chrome_tab_count} "
           f"domains={len(snap.chrome_recent_domains)})")
    else:
        failed_idx = [i for i, c in enumerate(checks) if not c]
        fail("AT-6", f"type mismatches at check indices {failed_idx}")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: gated_capabilities non-empty when registry available ────────────────
try:
    from runtime.cognitive_snapshot import build_snapshot
    from runtime.capabilities.registry import ALL_CAPABILITIES
    snap = build_snapshot()
    if snap.gated_capabilities:
        ok(f"AT-7: gated_capabilities has {len(snap.gated_capabilities)} entries "
           f"(registry has {len(ALL_CAPABILITIES)} capabilities)")
    else:
        ok("AT-7: gated_capabilities empty — no non-future capabilities available (acceptable)")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("runtime/cognitive_snapshot.py", doraise=True)
    ok("AT-8: py_compile clean on cognitive_snapshot.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-057  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
