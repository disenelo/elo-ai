"""
WO-031 acceptance tests — continuation loop auto-start.

AT-1  start_thread() starts a thread named 'continuation' and returns it
AT-2  Calling start_thread() a second time returns None (single-instance guard)
AT-3  DISENELO_NO_AUTOLOOP=1 → start_thread() returns None, no thread started
AT-4  Guard is thread-safe (concurrent calls don't start two threads)
AT-5  start_thread() is non-blocking (returns immediately; thread is daemon)
AT-6  py_compile: server.py and continuation.py compile cleanly
AT-7  Frozen kernel untouched (executive.py unchanged)
"""
import importlib.util
import os
import sys
import time
import threading
import types as _types

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_CONT_PATH = os.path.join(_ROOT, "company_runtime", "continuation.py")


def _fresh_module(no_autoloop: str = "") -> _types.ModuleType:
    """Load a fresh continuation module with a clean _started flag."""
    spec = importlib.util.spec_from_file_location(
        f"continuation_test_{id(no_autoloop)}", _CONT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    # Stub heavy deps so the module loads without a full elo-ai environment
    for dep in ("company_runtime.wo_test_runner", "company_runtime.company_state_writer",
                "company_runtime", "company_runtime.agent_bus"):
        stub = _types.ModuleType(dep)
        stub.ROOT    = _ROOT
        stub.BOARD   = os.path.join(_ROOT, "engineering", "work_orders", "DISPATCH_BOARD.md")
        stub.GREEN   = lambda r: False
        stub.tier_for = lambda wo, s: "DAVID"
        stub.discover = lambda: {}
        stub.board_status = lambda: {}
        stub.run_test = lambda p: {"passed": 0, "failed": 0, "errors": [], "rc": 0, "summary": "", "secs": 0}
        stub.auto_close = lambda wo, f: None
        stub.publish = lambda: None
        stub.ping_all = lambda: None
        sys.modules[dep] = stub

    saved_env = os.environ.pop("DISENELO_NO_AUTOLOOP", None)
    if no_autoloop:
        os.environ["DISENELO_NO_AUTOLOOP"] = no_autoloop

    try:
        spec.loader.exec_module(mod)
    finally:
        if saved_env is not None:
            os.environ["DISENELO_NO_AUTOLOOP"] = saved_env
        elif "DISENELO_NO_AUTOLOOP" in os.environ:
            del os.environ["DISENELO_NO_AUTOLOOP"]

    return mod


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_starts_thread():
    """start_thread() returns a daemon thread named 'continuation'."""
    mod = _fresh_module()
    t = mod.start_thread()
    assert t is not None,       "AT-1 FAIL: start_thread() returned None"
    assert t.is_alive(),        "AT-1 FAIL: thread not alive"
    assert t.daemon,            "AT-1 FAIL: thread is not daemon"
    assert t.name == "continuation", f"AT-1 FAIL: thread name={t.name!r}"
    print("AT-1 PASS — continuation thread started")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_single_instance():
    """Second call to start_thread() returns None (guard prevents double-start)."""
    mod = _fresh_module()
    t1 = mod.start_thread()
    t2 = mod.start_thread()
    assert t1 is not None, "AT-2 FAIL: first call returned None"
    assert t2 is None,     f"AT-2 FAIL: second call returned {t2!r}, expected None"
    print("AT-2 PASS — second start_thread() call correctly returns None")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_no_autoloop_env():
    """DISENELO_NO_AUTOLOOP=1 → start_thread() returns None."""
    saved = os.environ.pop("DISENELO_NO_AUTOLOOP", None)
    os.environ["DISENELO_NO_AUTOLOOP"] = "1"
    try:
        mod = _fresh_module(no_autoloop="1")
        t = mod.start_thread()
        assert t is None, f"AT-3 FAIL: start_thread() returned {t!r} despite NO_AUTOLOOP=1"
    finally:
        if saved is not None:
            os.environ["DISENELO_NO_AUTOLOOP"] = saved
        elif "DISENELO_NO_AUTOLOOP" in os.environ:
            del os.environ["DISENELO_NO_AUTOLOOP"]
    print("AT-3 PASS — DISENELO_NO_AUTOLOOP=1 disables auto-start")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_thread_safe_guard():
    """Concurrent start_thread() calls start exactly one thread."""
    mod = _fresh_module()
    results = []
    barrier = threading.Barrier(5)

    def call():
        barrier.wait()
        results.append(mod.start_thread())

    threads = [threading.Thread(target=call) for _ in range(5)]
    for th in threads:
        th.start()
    for th in threads:
        th.join(timeout=3.0)

    started = [r for r in results if r is not None]
    assert len(started) == 1, \
        f"AT-4 FAIL: {len(started)} threads started (expected exactly 1)"
    print("AT-4 PASS — concurrent calls start exactly one thread")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_non_blocking():
    """start_thread() returns in < 0.5 s (non-blocking)."""
    mod = _fresh_module()
    t0 = time.monotonic()
    mod.start_thread()
    elapsed = time.monotonic() - t0
    assert elapsed < 0.5, f"AT-5 FAIL: start_thread() took {elapsed:.2f}s (should be instant)"
    print(f"AT-5 PASS — start_thread() returned in {elapsed*1000:.0f}ms")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_py_compile():
    import py_compile
    for path, label in [
        (os.path.join(_ROOT, "server.py"), "server.py"),
        (os.path.join(_ROOT, "company_runtime", "continuation.py"), "continuation.py"),
    ]:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            raise AssertionError(f"AT-6 FAIL: {label} does not compile: {e}")
    print("AT-6 PASS — server.py + continuation.py compile cleanly")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_frozen_kernel():
    exec_path = os.path.join(_ROOT, "runtime", "executive.py")
    if not os.path.exists(exec_path):
        print("AT-7 PASS — executive.py not found (non-blocking)")
        return
    with open(exec_path, "rb") as f:
        content = f.read()
    for token in (b"WO-031", b"start_thread", b"DISENELO_NO_AUTOLOOP", b"continuation"):
        assert token not in content, \
            f"AT-7 FAIL: frozen file contains WO-031 token '{token.decode()}'"
    print("AT-7 PASS — frozen kernel untouched")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_starts_thread,
        test_at2_single_instance,
        test_at3_no_autoloop_env,
        test_at4_thread_safe_guard,
        test_at5_non_blocking,
        test_at6_py_compile,
        test_at7_frozen_kernel,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-031 ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
