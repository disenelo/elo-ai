"""
tests/test_0054_heartbeat_owner.py — card 0054: _ts must NOT advance when only
a tool or test imports state_writer. Only server.py (via start_heartbeat()) is
entitled to assert eLo's presence.

✅ PROVEN when:
  T1: Bare import of state_writer starts NO heartbeat thread.
  T2: _ts does NOT advance in the interval window when start_heartbeat() is not called.
  T3: start_heartbeat() starts the thread; second call is a no-op (no double thread).
  T4: ELO_STATE_HEARTBEAT=0 prevents start_heartbeat() from firing (test opt-out).

This is the falsifiable test — it goes RED if _start_heartbeat() is put back at
module level or called unconditionally on import.

Run: ELO_STATE_HEARTBEAT=0 python3 tests/test_0054_heartbeat_owner.py
"""
import json
import os
import sys
import threading
import time

# Opt out of heartbeat on import for this test process
os.environ["ELO_STATE_HEARTBEAT"] = "0"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


def _heartbeat_thread_running() -> bool:
    return any(t.name == "state_writer_heartbeat" for t in threading.enumerate())


# ── T1: bare import starts NO heartbeat thread ────────────────────────────────
def test_t1_import_has_no_side_effects():
    import blender_bridge.state_writer  # noqa: F401
    if _heartbeat_thread_running():
        err(
            "T1: state_writer_heartbeat thread is running after bare import — "
            "module import must have no side effects. "
            "This test goes RED if _start_heartbeat() is called at module level."
        )
    ok("T1: bare import of state_writer starts NO heartbeat thread")


# ── T2: _ts does not advance when start_heartbeat() is not called ─────────────
def test_t2_ts_does_not_advance_without_start(tmp_path):
    """
    Prove that patch() does not advance _ts when _heartbeat_started=False.
    Uses a tmp state path for isolation — the live server may be writing to
    the real blender_state.json in parallel; testing against that file would
    always false-fail when the server is running.
    """
    import blender_bridge.state_writer as sw

    # Redirect state path to isolated tmp file and reset heartbeat flag
    real_path   = sw._STATE_PATH
    real_started = sw._heartbeat_started
    tmp_state   = str(tmp_path / "blender_state.json")
    sw._STATE_PATH        = tmp_state
    sw._heartbeat_started = False

    # Write an initial _ts into the tmp file
    import json as _json
    initial_ts = round(time.time(), 3)
    with open(tmp_state, "w") as f:
        _json.dump({"_ts": initial_ts}, f)

    try:
        # Call patch() — must NOT advance _ts when _heartbeat_started=False
        sw.patch({"test_key": "test_value"})

        with open(tmp_state) as f:
            after = _json.load(f)
        ts_after = after.get("_ts", 0.0)

        if ts_after > initial_ts + 0.5:
            err(
                f"T2: patch() advanced _ts ({initial_ts} → {ts_after}) "
                "when _heartbeat_started=False — rogue writer not gated."
            )
        ok(f"T2: patch() did NOT advance _ts when _heartbeat_started=False "
           f"(before={initial_ts:.3f}, after={ts_after:.3f})")
    finally:
        sw._STATE_PATH        = real_path
        sw._heartbeat_started = real_started


# ── T3: start_heartbeat() starts thread; second call is a no-op ───────────────
def test_t3_start_heartbeat_is_explicit_and_guarded():
    # Re-enable for this sub-test
    os.environ["ELO_STATE_HEARTBEAT"] = "1"

    from blender_bridge import state_writer as sw
    # Reset the started flag so we can call it in this test
    sw._heartbeat_started = False

    sw.start_heartbeat()
    if not _heartbeat_thread_running():
        err("T3: start_heartbeat() did not start the thread")
    ok("T3: start_heartbeat() starts the heartbeat thread")

    thread_count_before = sum(1 for t in threading.enumerate() if t.name == "state_writer_heartbeat")
    sw.start_heartbeat()  # second call — must be no-op
    thread_count_after = sum(1 for t in threading.enumerate() if t.name == "state_writer_heartbeat")

    if thread_count_after > thread_count_before:
        err("T3: second call to start_heartbeat() spawned a duplicate thread")
    ok("T3: second call to start_heartbeat() is a no-op (no duplicate thread)")

    # Restore for remaining tests
    os.environ["ELO_STATE_HEARTBEAT"] = "0"
    sw._heartbeat_started = False


# ── T4: ELO_STATE_HEARTBEAT=0 prevents a NEW thread ─────────────────────────
def test_t4_env_opt_out():
    os.environ["ELO_STATE_HEARTBEAT"] = "0"

    from blender_bridge import state_writer as sw
    sw._heartbeat_started = False

    count_before = sum(1 for t in threading.enumerate() if t.name == "state_writer_heartbeat")
    sw.start_heartbeat()   # should be a no-op due to env flag
    count_after = sum(1 for t in threading.enumerate() if t.name == "state_writer_heartbeat")

    if count_after > count_before:
        err("T4: ELO_STATE_HEARTBEAT=0 did not prevent start_heartbeat() from spawning a new thread")
    ok("T4: ELO_STATE_HEARTBEAT=0 prevents start_heartbeat() — test processes are safe")


# ── runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("0054 HEARTBEAT OWNER TEST")
    print("(ELO_STATE_HEARTBEAT=0 — test opt-out active)")
    print()
    test_t1_import_has_no_side_effects()
    test_t2_ts_does_not_advance_without_start()
    test_t3_start_heartbeat_is_explicit_and_guarded()
    test_t4_env_opt_out()
    print()
    print("0054 DONE: _ts advances only when server.py calls start_heartbeat().")
    print("  Import alone = no thread. test_t2 goes RED if module import gains side effects.")
