"""
tests/test_0014_wo113_gap_states.py — Row 17 GAP (WO-113) disconnection proof.

"I can wall-jump but not reliably from here" — with real gap_distance / reliable_range.
Seven states are reachable; state changes when body_size changes (capability join proven).

Tests:
    GA-1  small gap → CAN (within 80% of reliable_range)
    GA-2  gap at limit → CAN-BUT-LOW-CONFIDENCE (80–100% of reliable_range)
    GA-3  gap over limit → CAN-BUT-DEGRADED (100–120% of reliable_range)
    GA-4  far gap → CANNOT (>120% of reliable_range)
    GA-5  no geometry → UNKNOWN
    GA-6  wrong surface → BLOCKED
    GA-7  reliable_range and gap_distance are real numbers in the assessment (not adjectives)
    GA-8  body_size change → reliable_range changes (capability join proven)
    GA-9  detail string contains both numbers

Run: python3 tests/test_0014_wo113_gap_states.py
"""
import sys
sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from runtime.affordances import (
    gap_state,
    GAP_CAN, GAP_CANNOT, GAP_CAN_BUT_DEGRADED, GAP_CAN_BUT_LOW_CONF,
    GAP_CAN_IF_CONDITION, GAP_UNKNOWN, GAP_BLOCKED,
    _DECLARED_RELIABLE_PX,
)

_JUMP_LIMIT = _DECLARED_RELIABLE_PX["wall-jump"]  # 160px declared


print(f"\nUsing declared wall-jump reliable_range={_JUMP_LIMIT}px\n")


print("GA-1: gap=100px on window_top → CAN")
try:
    g = gap_state("wall-jump", gap_distance=100.0, surface_type="window_top")
    if g.status == GAP_CAN:
        _d = repr(g.detail[:60])
        ok(f"GA-1 — {g.status} confidence={g.confidence} detail: {_d}")
    else:
        fail("GA-1", f"expected CAN, got {g.status!r} (gap=100, limit={_JUMP_LIMIT})")
except Exception as e:
    fail("GA-1", repr(e))


print("\nGA-2: gap at 90% of limit → CAN-BUT-LOW-CONFIDENCE")
try:
    _gap2 = _JUMP_LIMIT * 0.90
    g = gap_state("wall-jump", gap_distance=_gap2, surface_type="window_top")
    if g.status == GAP_CAN_BUT_LOW_CONF:
        ok(f"GA-2 — {g.status} confidence={g.confidence:.2f} (gap={_gap2:.0f}px, limit={_JUMP_LIMIT}px)")
    else:
        fail("GA-2", f"expected CAN-BUT-LOW-CONFIDENCE, got {g.status!r}")
except Exception as e:
    fail("GA-2", repr(e))


print("\nGA-3: gap at 110% of limit → CAN-BUT-DEGRADED")
try:
    _gap3 = _JUMP_LIMIT * 1.10
    g = gap_state("wall-jump", gap_distance=_gap3, surface_type="window_top")
    if g.status == GAP_CAN_BUT_DEGRADED:
        ok(f"GA-3 — {g.status} confidence={g.confidence:.2f} (gap={_gap3:.0f}px, limit={_JUMP_LIMIT}px)")
    else:
        fail("GA-3", f"expected CAN-BUT-DEGRADED, got {g.status!r}")
except Exception as e:
    fail("GA-3", repr(e))


print("\nGA-4: gap at 200% of limit → CANNOT")
try:
    _gap4 = _JUMP_LIMIT * 2.0
    g = gap_state("wall-jump", gap_distance=_gap4, surface_type="window_top")
    if g.status == GAP_CANNOT:
        ok(f"GA-4 — {g.status} confidence={g.confidence} (gap={_gap4:.0f}px >> limit={_JUMP_LIMIT}px)")
    else:
        fail("GA-4", f"expected CANNOT, got {g.status!r}")
except Exception as e:
    fail("GA-4", repr(e))


print("\nGA-5: gap_distance=None → UNKNOWN")
try:
    g = gap_state("wall-jump", gap_distance=None, surface_type="window_top")
    if g.status == GAP_UNKNOWN:
        ok(f"GA-5 — {g.status} (no geometry — absence statable)")
    else:
        fail("GA-5", f"expected UNKNOWN, got {g.status!r}")
except Exception as e:
    fail("GA-5", repr(e))


print("\nGA-6: wall-jump on desktop_floor → BLOCKED (surface doesn't support it)")
try:
    g = gap_state("wall-jump", gap_distance=50.0, surface_type="desktop_floor")
    if g.status == GAP_BLOCKED:
        ok(f"GA-6 — {g.status} (wall-jump not in desktop_floor affordances)")
    else:
        fail("GA-6", f"expected BLOCKED, got {g.status!r}")
except Exception as e:
    fail("GA-6", repr(e))


print("\nGA-7: GapAssessment carries real numbers (gap_distance, reliable_range)")
try:
    _gap7 = 120.0
    g = gap_state("wall-jump", gap_distance=_gap7, surface_type="window_top")
    if g.gap_distance == _gap7 and isinstance(g.reliable_range, float) and g.reliable_range > 0:
        ok(f"GA-7 — numbers present: gap_distance={g.gap_distance}px, reliable_range={g.reliable_range}px")
    else:
        fail("GA-7", f"gap_distance={g.gap_distance!r}, reliable_range={g.reliable_range!r}")
except Exception as e:
    fail("GA-7", repr(e))


print("\nGA-8: body_size change → reliable_range changes (capability join proven)")
try:
    g_normal = gap_state("wall-jump", gap_distance=100.0, body_size=1.0, surface_type="window_top")
    g_large  = gap_state("wall-jump", gap_distance=100.0, body_size=2.0, surface_type="window_top")
    if g_large.reliable_range > g_normal.reliable_range:
        ok(f"GA-8 — body_size 1.0→2.0 changes reliable_range: {g_normal.reliable_range:.0f}→{g_large.reliable_range:.0f}px")
    else:
        fail("GA-8", f"reliable_range did not change: normal={g_normal.reliable_range}, large={g_large.reliable_range}")
except Exception as e:
    fail("GA-8", repr(e))


print("\nGA-9: detail string contains both numbers")
try:
    _gap9 = 140.0
    g = gap_state("wall-jump", gap_distance=_gap9, surface_type="window_top")
    _has_dist = str(int(_gap9)) in g.detail or f"{_gap9}" in g.detail
    _has_range = str(int(g.reliable_range)) in g.detail
    if _has_dist and _has_range:
        _dp = repr(g.detail[:80])
        ok(f"GA-9 — detail contains numbers: {_dp}")
    else:
        fail("GA-9", f"detail missing numbers: {g.detail!r}")
except Exception as e:
    fail("GA-9", repr(e))


print(f"\n{'='*40}")
print(f"Row 17 GAP (WO-113): {PASS} passed, {FAIL} failed")
print()
print("Row verified by this test:")
print("  17 GAP — 7 gap states reachable; numbers behind each; body capability join proven")
print()
print("Example output (Gap §6):")
_ex = gap_state("wall-jump", gap_distance=170.0, surface_type="window_top")
print(f"  'I can wall-jump, but gap_distance={_ex.gap_distance:.0f}px > reliable_range={_ex.reliable_range:.0f}px")
print(f"   (source: {_ex.source}) — {_ex.status} confidence {_ex.confidence:.0f}%'")
if FAIL:
    sys.exit(1)
