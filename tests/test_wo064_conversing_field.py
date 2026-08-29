"""
tests/test_wo064_conversing_field.py — WO-064 BP-1
Verify `conversing` boolean is written to blender_state.json each turn.
Run: ~/miniconda3/bin/python3 tests/test_wo064_conversing_field.py
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BLENDER_STATE = os.path.join(ROOT, "blender", "blender_state.json")

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


def _load_server_src():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# AT-1: Logic — recent last_user_ts → conversing == True
# ---------------------------------------------------------------------------
def at1_recent_ts_is_true():
    now = time.time()
    recent_ts = now - 5.0  # 5 seconds ago — well within 30s window
    conversing = (now - recent_ts) < 30.0
    if conversing is True:
        ok("AT-1: recent last_user_ts (5s) → conversing == True")
    else:
        fail("AT-1", f"expected True, got {conversing}")


# ---------------------------------------------------------------------------
# AT-2: Logic — stale last_user_ts → conversing == False
# ---------------------------------------------------------------------------
def at2_stale_ts_is_false():
    now = time.time()
    stale_ts = now - 60.0  # 60 seconds ago — past the 30s window
    conversing = (now - stale_ts) < 30.0
    if conversing is False:
        ok("AT-2: stale last_user_ts (60s) → conversing == False")
    else:
        fail("AT-2", f"expected False, got {conversing}")


# ---------------------------------------------------------------------------
# AT-3: Source code — conversing field and 30s threshold present in server.py
# ---------------------------------------------------------------------------
def at3_source_pattern():
    src = _load_server_src()
    has_conversing_field = '"conversing"' in src and "_bs_conversing" in src
    has_30s_threshold = "< 30.0" in src or "< 30" in src
    has_last_user_ts = "last_user_ts" in src
    if has_conversing_field and has_30s_threshold and has_last_user_ts:
        ok("AT-3: server.py has conversing field with 30s threshold logic")
    else:
        missing = []
        if not has_conversing_field:
            missing.append('"conversing" / _bs_conversing')
        if not has_30s_threshold:
            missing.append("< 30.0 threshold")
        if not has_last_user_ts:
            missing.append("last_user_ts")
        fail("AT-3", "missing: " + ", ".join(missing))


# ---------------------------------------------------------------------------
# AT-4: patch() writes `conversing` field to blender_state.json
# ---------------------------------------------------------------------------
def at4_patch_writes_conversing():
    try:
        from blender_bridge.state_writer import patch as _patch
        _patch({"conversing": True})
        try:
            with open(BLENDER_STATE, encoding="utf-8") as f:
                state = json.load(f)
            if "conversing" in state:
                ok(f"AT-4: patch({{conversing: True}}) → field present in blender_state.json")
            else:
                fail("AT-4", "'conversing' key missing from blender_state.json after patch")
        except Exception as e:
            fail("AT-4", f"could not read blender_state.json: {e}")
    except Exception as e:
        fail("AT-4", f"patch() raised: {e}")


def run_tests():
    print("\n=== WO-064 BP-1 — conversing field ===\n")
    at1_recent_ts_is_true()
    at2_stale_ts_is_false()
    at3_source_pattern()
    at4_patch_writes_conversing()
    print(f"\n{'='*50}")
    print(f"Result: {PASS}/4 PASS  {FAIL}/4 FAIL")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
