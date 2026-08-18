"""
tests/test_f4_heartbeat.py — card 0053 F4: _ts must advance on a periodic
heartbeat even when no other field changes.

Updated by 0054: heartbeat no longer starts on import — only server.py calls
start_heartbeat(). T1 updated to call it explicitly before checking.

Run: python3 tests/test_f4_heartbeat.py
"""
import json
import os
import sys
import threading
import time

os.environ.setdefault("ELO_STATE_HEARTBEAT", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── T1: start_heartbeat() starts the thread (called explicitly, not on import) ─
def test_t1_heartbeat_thread_starts():
    from blender_bridge import state_writer as sw
    sw._heartbeat_started = False   # reset so we can test fresh
    sw.start_heartbeat()
    names = {t.name for t in threading.enumerate()}
    if "state_writer_heartbeat" not in names:
        err("T1: 'state_writer_heartbeat' daemon thread not found after start_heartbeat()")
    ok("T1: start_heartbeat() starts the state_writer_heartbeat daemon thread")


# ── T2: patch({}) advances _ts, leaves other fields untouched ────────────────
def test_t2_patch_empty_advances_ts():
    from blender_bridge import state_writer as sw
    STATE = sw._STATE_PATH

    # Read current _ts (or create a baseline)
    try:
        with open(STATE, encoding="utf-8") as f:
            before = json.load(f)
        ts_before = before.get("_ts", 0.0)
        sentinel_key = "_f4_test_sentinel"
        sentinel_val = "preserved"
        before[sentinel_key] = sentinel_val
        # Write sentinel back
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(before, f)
        os.replace(tmp, STATE)
    except Exception as e:
        err(f"T2: could not set up test state: {e}")

    time.sleep(0.05)  # ensure time advances
    sw.patch({})      # empty heartbeat tick

    try:
        with open(STATE, encoding="utf-8") as f:
            after = json.load(f)
        ts_after = after.get("_ts", 0.0)
    except Exception as e:
        err(f"T2: could not read state after patch: {e}")

    if ts_after <= ts_before:
        err(f"T2: _ts did not advance: before={ts_before}, after={ts_after}")
    ok(f"T2: _ts advanced from {ts_before} → {ts_after} on patch({{}})")

    if after.get(sentinel_key) != sentinel_val:
        err(f"T2: patch({{}}) modified other fields — sentinel_key lost")
    ok(f"T2: other fields untouched (sentinel preserved)")

    # Clean up sentinel
    del after[sentinel_key]
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(after, f)
    os.replace(tmp, STATE)


# ── T3: heartbeat interval is sane (≤ 60s) ───────────────────────────────────
def test_t3_heartbeat_interval():
    from blender_bridge import state_writer as sw
    interval = sw._HEARTBEAT_INTERVAL
    if interval > 60:
        err(f"T3: _HEARTBEAT_INTERVAL={interval}s — too long, Blender will see stale state")
    ok(f"T3: _HEARTBEAT_INTERVAL={interval}s (≤ 60s)")


# ── runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("F4 HEARTBEAT TEST")
    print()
    test_t1_heartbeat_thread_starts()
    test_t2_patch_empty_advances_ts()
    test_t3_heartbeat_interval()
    print()
    print("F4 DONE: _ts advances on heartbeat independently of state changes.")
