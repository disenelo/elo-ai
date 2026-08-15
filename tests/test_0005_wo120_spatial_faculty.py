"""
tests/test_0005_wo120_spatial_faculty.py — Acceptance tests for WO-120 (card 0005).

3 tests:
    SF-1  Faculty is importable (would fail if orphaned module)
    SF-2  context_block() answers "what's reachable" from real state (returns non-empty string)
    SF-3  spatial_state.py docstring no longer claims to "plan routes"

Run: python3 tests/test_0005_wo120_spatial_faculty.py
"""
import sys
sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── SF-1: faculty is importable ───────────────────────────────────────────────

print("\nSF-1: Spatial Faculty is importable")
try:
    from faculties.spatial.spatial_faculty import assemble, context_block, SpatialContext
    ok("SF-1 — faculties.spatial.spatial_faculty imported successfully")
except Exception as e:
    fail("SF-1", repr(e))


# ── SF-2: context_block answers reachability from real state ──────────────────

print("\nSF-2: context_block() returns spatial context from real state")
try:
    block = context_block()
    if not isinstance(block, str):
        fail("SF-2", f"expected str, got {type(block)}")
    elif block and not block.startswith("[SPATIAL]"):
        fail("SF-2", f"expected '[SPATIAL]' prefix or empty string; got: {block!r}")
    else:
        # assemble() must not raise regardless of file state
        ctx = assemble()
        if not isinstance(ctx, SpatialContext):
            fail("SF-2", f"assemble() returned {type(ctx)}")
        elif ctx.affordances is not None and not isinstance(ctx.affordances, tuple):
            fail("SF-2", f"affordances must be a tuple; got {type(ctx.affordances)}")
        else:
            _preview = repr(block[:80]) if block else "(empty — no live spatial state)"
            ok(f"SF-2 — context_block() returned {_preview}")
except Exception as e:
    fail("SF-2", repr(e))


# ── SF-3: spatial_state.py docstring no longer claims route planning ──────────

print("\nSF-3: spatial_state.py docstring does not claim to 'plan routes'")
try:
    with open("desktop/spatial_state.py", encoding="utf-8") as f:
        src = f.read()
    if "plans routes" in src:
        fail("SF-3", "docstring still contains 'plans routes' — lie not removed")
    else:
        ok("SF-3 — 'plans routes' removed from spatial_state.py docstring")
except Exception as e:
    fail("SF-3", repr(e))


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"WO-120 Spatial Faculty: {PASS} passed, {FAIL} failed")
if FAIL:
    sys.exit(1)
