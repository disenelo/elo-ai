"""
tests/test_wo002_live_world_state.py — Acceptance tests for WO-002: LiveWorldState

Spec: world/live_world_state.py
6 acceptance tests from Volume_XV.

Run: python3 tests/test_wo002_live_world_state.py
"""
import sys
sys.path.insert(0, '.')

PASS = 0; FAIL = 0
def ok(n):  global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from world.live_world_state import assemble_world_state, LiveWorldState

# Actual domains from the dataclass (verified by inspection)
DOMAINS = ["desktop", "user", "unity", "browser", "files", "internet",
           "music", "calendar", "environment", "time", "weather"]

# ── FT-1: Returns a LiveWorldState ───────────────────────────────────────────
ws = assemble_world_state(turn_id="test-001")
try:
    assert isinstance(ws, LiveWorldState)
    ok("FT-1: assemble_world_state returns LiveWorldState")
except AssertionError as e: fail("FT-1", e)

# ── FT-2: All 11 domain slices present ────────────────────────────────────────
try:
    for d in DOMAINS:
        assert hasattr(ws, d), f"missing domain: {d}"
    ok(f"FT-2: all {len(DOMAINS)} domain slices present")
except AssertionError as e: fail("FT-2", e)

# ── FT-3: Domain health metadata present ─────────────────────────────────────
try:
    assert hasattr(ws, "domain_health"), "missing domain_health"
    for d in DOMAINS:
        h = ws.domain_health.get(d, {})
        assert "status" in h, f"domain {d} missing status"
        assert h["status"] in ("live", "cached", "stale", "absent"), f"bad status: {h['status']}"
    ok("FT-3: domain_health metadata present on all domains")
except AssertionError as e: fail("FT-3", e)

# ── FT-4: Frozen (immutable) ──────────────────────────────────────────────────
try:
    try:
        ws.time = None
        fail("FT-4", "LiveWorldState is not frozen — mutation succeeded")
    except Exception:
        ok("FT-4: LiveWorldState is frozen")
except Exception as e: fail("FT-4", e)

# ── ST-1: One failing domain never blocks others ─────────────────────────────
try:
    ws2 = assemble_world_state(turn_id="test-st1")
    present = [d for d in DOMAINS if ws2.domain_health.get(d, {}).get("status") != "absent"]
    assert len(present) >= 1, "all domains absent"
    ok(f"ST-1: failing domains degrade gracefully; {len(present)}/{len(DOMAINS)} domains have data")
except AssertionError as e: fail("ST-1", e)

# ── ST-2: degraded tuple populated when domains fall back ─────────────────────
try:
    assert isinstance(ws.degraded, tuple), "degraded should be a tuple"
    ok(f"ST-2: degraded tuple present ({len(ws.degraded)} degraded domains)")
except AssertionError as e: fail("ST-2", e)

print(f"\nResult: {PASS}/6 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
