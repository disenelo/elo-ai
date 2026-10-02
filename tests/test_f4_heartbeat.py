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
    """
    T2 used sw._STATE_PATH directly — blender/blender_state.json, the LIVE
    file a running server rewrites every 0.3s and DesktopBuddy renders from
    every frame. It wrote a sentinel key into it, patched, then wrote again to
    clean up. Three writes into eLo's running state, and it raced the server:
    the test passed alone and went SystemExit in a full suite run.

    Same class as 274a980 (live blender_state), 2701c39 (the real symbol
    lexicon) and the dream gallery. Fourth instance.

    Redirected to a temp file. The logic under test is unchanged — patch({})
    must advance _ts and leave other fields alone — it just no longer does it
    to the live state.
    """
    import json as _json
    import tempfile as _tempfile
    from blender_bridge import state_writer as sw

    _tmpdir = _tempfile.mkdtemp()
    STATE = os.path.join(_tmpdir, "blender_state.json")
    with open(STATE, "w", encoding="utf-8") as _f:
        _json.dump({"_ts": time.time() - 1.0, "state": {}, "motion": {}}, _f)
    # patch() only advances _ts when _heartbeat_started is True -- deliberately
    # gated so tests cannot fake presence. T2 was relying on T1 having set that
    # flag earlier in the file, and something else in the suite clears it, so
    # T2 passed alone and failed in a full run with before == after. A test
    # that depends on global state another test happens to leave behind is not
    # testing anything reliably. It sets its own precondition now.
    _real_path = sw._STATE_PATH
    _real_hb = sw._heartbeat_started
    sw._STATE_PATH = STATE
    sw._heartbeat_started = True
    try:
        _t2_body(sw, STATE)
    finally:
        sw._STATE_PATH = _real_path
        sw._heartbeat_started = _real_hb


def _t2_body(sw, STATE):

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


# ── T4: bare import does NOT start the heartbeat thread (0054 guard) ─────────
def test_t4_import_without_call_does_not_start_heartbeat():
    import subprocess
    script = (
        "import sys, threading, time; sys.path.insert(0, '.'); "
        "import os; os.environ.pop('ELO_STATE_HEARTBEAT', None); "
        "import blender_bridge.state_writer; "
        "time.sleep(0.05); "
        "names = {t.name for t in threading.enumerate()}; "
        "assert 'state_writer_heartbeat' not in names, f'heartbeat thread started on bare import: {names}'; "
        "print('T4_PASS')"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=10,
        cwd=ROOT,
    )
    if "T4_PASS" not in result.stdout or result.returncode != 0:
        err(f"T4: bare import started heartbeat thread — stdout={result.stdout!r} stderr={result.stderr!r}")
    ok("T4: bare import does NOT start the state_writer_heartbeat thread — guard confirmed")


# ── runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("F4 HEARTBEAT TEST")
    print()
    test_t1_heartbeat_thread_starts()
    test_t2_patch_empty_advances_ts()
    test_t3_heartbeat_interval()
    test_t4_import_without_call_does_not_start_heartbeat()
    print()
    print("F4 DONE: _ts advances on heartbeat independently of state changes.")
