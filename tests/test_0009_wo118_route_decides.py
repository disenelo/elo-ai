"""
tests/test_0009_wo118_route_decides.py — Row 14 ROUTE disconnection proof.

A capability is not VERIFIED until the seam is open end-to-end — state present
must produce a different decision than state absent.

Tests:
    RD-1  route_history absent (empty list) → action stays in build/connect/celebrate
    RD-2  route_history last move fell (arrived=False, fell=True) → action shifts to "witness"
    RD-3  route_history last move succeeded (arrived=True) → action stays in build/connect/celebrate
    RD-4  route_history with multiple entries — only the last one drives the shift

Run: python3 tests/test_0009_wo118_route_decides.py
"""
import sys
sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from runtime.executive import decide


_BASE = {"intent": "creation", "valence": "positive", "momentum": "building",
         "world_state": {"available": True}}
_INPUT = "let me build this idea"

_FELL_MOVE   = {"arrived": False, "fell": True,  "goal": "WindowTop"}
_ARRIVED_MOVE = {"arrived": True,  "fell": False, "goal": "WindowTop"}


print("\nRD-1: route_history absent → action stays in build/connect/celebrate")
try:
    r = decide({**_BASE, "world_state": {"available": True, "route_history": []}},
               loop_detected=False, user_input=_INPUT)
    action = r.get("action")
    if action in ("build", "connect", "celebrate"):
        ok(f"RD-1 — no route history → {action!r} (not overridden)")
    else:
        fail("RD-1", f"unexpected action {action!r} with empty route_history")
except Exception as e:
    fail("RD-1", repr(e))


print("\nRD-2: last move fell → action shifts to 'witness'")
try:
    r = decide({**_BASE, "world_state": {"available": True, "route_history": [_FELL_MOVE]}},
               loop_detected=False, user_input=_INPUT)
    action = r.get("action")
    if action == "witness":
        ok(f"RD-2 — fell last move → 'witness' (presence before enthusiasm)")
    elif action in ("build", "connect", "celebrate"):
        fail("RD-2", f"seam not open — fell move did not shift action; got {action!r}")
    else:
        fail("RD-2", f"unexpected action {action!r}")
except Exception as e:
    fail("RD-2", repr(e))


print("\nRD-3: last move arrived (success) → action stays in build/connect/celebrate")
try:
    r = decide({**_BASE, "world_state": {"available": True, "route_history": [_ARRIVED_MOVE]}},
               loop_detected=False, user_input=_INPUT)
    action = r.get("action")
    if action in ("build", "connect", "celebrate"):
        ok(f"RD-3 — successful last move → {action!r} (no override)")
    else:
        fail("RD-3", f"unexpected action {action!r} after successful move")
except Exception as e:
    fail("RD-3", repr(e))


print("\nRD-4: last entry drives shift — success then fall → 'witness'")
try:
    hist = [_ARRIVED_MOVE, _ARRIVED_MOVE, _FELL_MOVE]
    r = decide({**_BASE, "world_state": {"available": True, "route_history": hist}},
               loop_detected=False, user_input=_INPUT)
    action = r.get("action")
    if action == "witness":
        ok("RD-4 — last entry (fell) drives shift even with prior successes")
    elif action in ("build", "connect", "celebrate"):
        fail("RD-4", f"seam not open — last fell entry did not shift; got {action!r}")
    else:
        fail("RD-4", f"unexpected action {action!r}")
except Exception as e:
    fail("RD-4", repr(e))


print(f"\n{'='*40}")
print(f"Row 14 ROUTE Disconnection: {PASS} passed, {FAIL} failed")
print()
print("Row verified by this test:")
print("  14 ROUTE — route_history readable by decide(); fell move → 'witness'")
if FAIL:
    sys.exit(1)
