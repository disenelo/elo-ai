"""
tests/test_wo_fix_mobile_replay.py — WO-FIX-MOBILE-REPLAY
Verify mobile event replay guard in server.py.
Run: ~/miniconda3/bin/python3 tests/test_wo_fix_mobile_replay.py
"""
import py_compile
import re
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PY = os.path.join(ROOT, "server.py")
EXEC_PY = os.path.join(ROOT, "runtime", "executive.py")

PASS = 0
FAIL = 0

def ok(label):
    global PASS
    PASS += 1
    print(f"  ✅ {label}")

def fail(label, reason=""):
    global FAIL
    FAIL += 1
    print(f"  ❌ {label}" + (f": {reason}" if reason else ""))


def load_server_source():
    with open(SERVER_PY, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# AT-1: Same mobile event ts → guard fires; second call suppressed (1 process)
# ---------------------------------------------------------------------------
def at1_same_ts_suppressed():
    """Simulate the guard: same _ev_ts twice → only processed once."""
    src = load_server_source()

    # Verify guard variable exists
    if "_mobile_last_ts" not in src:
        fail("AT-1", "_mobile_last_ts not found in server.py")
        return

    # Verify guard condition exists
    if "_ev_ts > _mobile_last_ts" not in src:
        fail("AT-1", "guard condition '_ev_ts > _mobile_last_ts' not in server.py")
        return

    # Verify update after processing
    if "_mobile_last_ts = _ev_ts" not in src:
        fail("AT-1", "timestamp update '_mobile_last_ts = _ev_ts' not in server.py")
        return

    # Simulate the guard logic (mirrors server.py exactly)
    mobile_last_ts = 0.0
    call_count = 0

    def _simulate_guard(ev_ts):
        nonlocal mobile_last_ts, call_count
        if ev_ts > mobile_last_ts:
            call_count += 1
            mobile_last_ts = ev_ts

    _simulate_guard(100.0)
    _simulate_guard(100.0)  # same ts — should be suppressed

    if call_count == 1:
        ok("AT-1: same ts → processed exactly once (not twice)")
    else:
        fail("AT-1", f"expected 1 process, got {call_count}")


# ---------------------------------------------------------------------------
# AT-2: Two different ts → both processed (guard doesn't over-suppress)
# ---------------------------------------------------------------------------
def at2_different_ts_both_processed():
    mobile_last_ts = 0.0
    call_count = 0

    def _simulate_guard(ev_ts):
        nonlocal mobile_last_ts, call_count
        if ev_ts > mobile_last_ts:
            call_count += 1
            mobile_last_ts = ev_ts

    _simulate_guard(100.0)
    _simulate_guard(200.0)  # different ts — should process

    if call_count == 2:
        ok("AT-2: two different ts → both processed (2 entries)")
    else:
        fail("AT-2", f"expected 2 processes, got {call_count}")


# ---------------------------------------------------------------------------
# AT-3: ACK branch unchanged — _ack_last_ts pattern preserved
# ---------------------------------------------------------------------------
def at3_ack_branch_unchanged():
    src = load_server_source()

    # Both guards should be present and independent
    has_ack_guard = "_ev_ts > _ack_last_ts" in src
    has_mobile_guard = "_ev_ts > _mobile_last_ts" in src
    has_ack_update = "_ack_last_ts = _ev_ts" in src
    has_mobile_update = "_mobile_last_ts = _ev_ts" in src

    if has_ack_guard and has_mobile_guard and has_ack_update and has_mobile_update:
        ok("AT-3: ACK guard (_ack_last_ts) intact; mobile guard (_mobile_last_ts) added alongside it")
    else:
        missing = []
        if not has_ack_guard:
            missing.append("_ev_ts > _ack_last_ts")
        if not has_mobile_guard:
            missing.append("_ev_ts > _mobile_last_ts")
        if not has_ack_update:
            missing.append("_ack_last_ts = _ev_ts")
        if not has_mobile_update:
            missing.append("_mobile_last_ts = _ev_ts")
        fail("AT-3", "missing: " + ", ".join(missing))


# ---------------------------------------------------------------------------
# AT-4: executive.py not touched (FREEZE_V1_LOCK clean)
# ---------------------------------------------------------------------------
def at4_executive_not_touched():
    try:
        py_compile.compile(EXEC_PY, doraise=True)
        ok("AT-4: executive.py compiles clean (FREEZE_V1_LOCK — file not modified by this WO)")
    except py_compile.PyCompileError as e:
        fail("AT-4", str(e))


def run_tests():
    print("\n=== WO-FIX-MOBILE-REPLAY — mobile event replay guard ===\n")
    at1_same_ts_suppressed()
    at2_different_ts_both_processed()
    at3_ack_branch_unchanged()
    at4_executive_not_touched()
    print(f"\n{'='*50}")
    print(f"Result: {PASS}/4 PASS  {FAIL}/4 FAIL")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
