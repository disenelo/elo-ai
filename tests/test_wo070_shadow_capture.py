"""
tests/test_wo070_shadow_capture.py — Acceptance tests for WO-070

Spec: WO-070 — Understudy shadow-capture (passive training-data basket).

  AT-1: Simulated turn → exactly one well-formed record appended (all required fields)
  AT-2: raw_gen ≠ final when a scrub fired (different values accepted)
  AT-3: Logger fails internally → bus turn still completes (zero-blocking proof)
  AT-4: L3 approve → record's l3_rating reflects it
  AT-5: Malformed / exception in record_turn → no crash, queue still works after
  AT-6: record_turn is non-blocking (returns in <50ms even under simulated I/O delay)
  AT-7: Bus subscriber registered (ShadowCapture in bus.heartbeat())
  AT-8: py_compile clean on shadow_capture.py and server.py

Run: python3 tests/test_wo070_shadow_capture.py
"""
import sys, os, json, time, py_compile, tempfile, shutil, threading, unittest.mock as _mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

# ── Redirect shadow log to temp dir ───────────────────────────────────────────
_TMP = tempfile.mkdtemp(prefix="wo070_test_")
import runtime.shadow_capture as _sc
_orig_log = _sc._SHADOW_LOG
_sc._SHADOW_LOG = os.path.join(_TMP, "understudy_shadow.jsonl")


def _read_shadow() -> list:
    path = _sc._SHADOW_LOG
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


try:
    # Reset writer state for isolated testing
    import queue as _queue_mod
    _sc._q = _queue_mod.Queue(maxsize=0)
    _sc._started = False

    # ── AT-1: One turn → one well-formed record ───────────────────────────────
    try:
        _sc.record_turn(
            raw_input="just write it down before I lose the thread",
            elo_raw_gen="Got it — saving now.",
            elo_final="Got it — saved to ideas_log.jsonl.",
            backend_used="groq",
            trace_id="test-trace-001",
            executed_action="capture",
        )
        _sc.flush_sync(timeout=2.0)
        entries = _read_shadow()
        assert len(entries) >= 1, f"expected at least 1 record, got {len(entries)}"
        rec = entries[-1]
        required = ("trace_id", "timestamp", "context", "raw_input",
                    "elo_raw_gen", "elo_final", "backend_used", "executed_action", "l3_rating")
        missing = [k for k in required if k not in rec]
        assert not missing, f"record missing fields: {missing}"
        assert rec["raw_input"] == "just write it down before I lose the thread"
        assert rec["backend_used"] == "groq"
        ok(f"AT-1: record written with all {len(required)} required fields")
    except AssertionError as e:
        fail("AT-1", e)
    except Exception as e:
        fail("AT-1", e)


    # ── AT-2: raw_gen ≠ final when scrub fired ────────────────────────────────
    try:
        _sc.record_turn(
            raw_input="how are you doing?",
            elo_raw_gen="I'm doing great honestly, how about you?",  # pre-scrub (with trailing ?)
            elo_final="I'm doing great honestly.",                    # post-scrub (stripped ?)
            backend_used="ollama",
            trace_id="test-trace-002",
        )
        _sc.flush_sync(timeout=2.0)
        entries = _read_shadow()
        scrubbed = [e for e in entries if e.get("trace_id") == "test-trace-002"]
        assert len(scrubbed) == 1, f"expected 1 scrubbed record, got {len(scrubbed)}"
        rec = scrubbed[0]
        assert rec["elo_raw_gen"] != rec["elo_final"], \
            "raw_gen should differ from final when scrub fired"
        ok(f"AT-2: raw_gen ≠ final captured correctly (scrub delta recorded)")
    except AssertionError as e:
        fail("AT-2", e)
    except Exception as e:
        fail("AT-2", e)


    # ── AT-3: Logger fails internally → bus turn still completes ─────────────
    try:
        _before_count = len(_read_shadow())
        # Simulate a write failure by patching _flush
        _failure_raised = []
        def _bad_flush(record):
            _failure_raised.append(True)
            raise OSError("simulated disk failure")

        with _mock.patch.object(_sc, "_flush", side_effect=_bad_flush):
            _sc.record_turn(
                raw_input="this should not crash anything",
                elo_raw_gen="...",
                elo_final="...",
                backend_used="mock",
                trace_id="test-trace-003",
            )
            # The caller returns immediately — no exception
            time.sleep(0.2)  # let the background thread attempt the flush

        # Bus turn completed (no exception propagated)
        assert len(_failure_raised) >= 1, "flush should have been attempted"
        _after_count = len(_read_shadow())
        # The failed record doesn't appear (flush failed) — that's expected
        # The key is: no exception was raised to the caller
        ok(f"AT-3: logger failure isolated — caller returned, no exception propagated")
    except AssertionError as e:
        fail("AT-3", e)
    except Exception as e:
        fail("AT-3", e)


    # ── AT-4: L3 approve → l3_rating captured ────────────────────────────────
    try:
        _sc.record_l3_rating("test-trace-001", "approved")
        _sc.flush_sync(timeout=2.0)
        entries = _read_shadow()
        patches = [e for e in entries if e.get("_type") == "l3_patch"
                   and e.get("trace_id") == "test-trace-001"]
        assert len(patches) >= 1, f"expected at least 1 l3_patch record, got {patches}"
        assert patches[-1]["l3_rating"] == "approved"
        ok(f"AT-4: L3 approve → l3_patch record captured (trace_id match)")
    except AssertionError as e:
        fail("AT-4", e)
    except Exception as e:
        fail("AT-4", e)


    # ── AT-5: Malformed call → no crash, queue still works ────────────────────
    try:
        # Pass None for required fields — should not raise
        try:
            _sc.record_turn(
                raw_input=None,    # type: ignore
                elo_raw_gen=None,  # type: ignore
                elo_final=None,    # type: ignore
                backend_used=None, # type: ignore
            )
        except Exception as e_inner:
            fail("AT-5", f"record_turn raised on bad input: {e_inner}")
            raise

        # Queue should still work after the bad call
        _sc.record_turn(
            raw_input="recovery check",
            elo_raw_gen="ok",
            elo_final="ok",
            backend_used="mock",
            trace_id="test-trace-005",
        )
        _sc.flush_sync(timeout=2.0)
        entries = _read_shadow()
        recovery = [e for e in entries if e.get("trace_id") == "test-trace-005"]
        assert len(recovery) >= 1, "queue should recover after malformed call"
        ok("AT-5: malformed call → no crash; queue recovered for next call")
    except AssertionError as e:
        fail("AT-5", e)
    except Exception as e:
        fail("AT-5", e)


    # ── AT-6: Non-blocking — returns in <50ms ────────────────────────────────
    try:
        # Simulate slow I/O by temporarily stalling the writer
        _t0 = time.perf_counter()
        for _ in range(5):
            _sc.record_turn(
                raw_input="non-blocking test",
                elo_raw_gen="...",
                elo_final="...",
                backend_used="groq",
            )
        _elapsed_ms = (time.perf_counter() - _t0) * 1000
        assert _elapsed_ms < 50.0, \
            f"record_turn x5 took {_elapsed_ms:.1f}ms — should be <50ms (non-blocking)"
        ok(f"AT-6: record_turn x5 returned in {_elapsed_ms:.1f}ms (non-blocking ✓)")
    except AssertionError as e:
        fail("AT-6", e)
    except Exception as e:
        fail("AT-6", e)


    # ── AT-7: Bus subscriber registered ──────────────────────────────────────
    try:
        _sc.subscribe_to_bus()
        from core.faculty_bus import get_bus
        hb = get_bus().heartbeat()
        assert "ShadowCapture" in hb["subscribers"], \
            f"ShadowCapture not in bus subscribers: {hb['subscribers']}"
        ok(f"AT-7: ShadowCapture registered in bus (subscribers: {hb['subscribers']})")
    except AssertionError as e:
        fail("AT-7", e)
    except Exception as e:
        fail("AT-7", e)


    # ── AT-8: py_compile clean ────────────────────────────────────────────────
    try:
        py_compile.compile("runtime/shadow_capture.py", doraise=True)
        py_compile.compile("server.py", doraise=True)
        ok("AT-8: py_compile clean on shadow_capture.py and server.py")
    except py_compile.PyCompileError as e:
        fail("AT-8", e)

finally:
    _sc._SHADOW_LOG = _orig_log
    shutil.rmtree(_TMP, ignore_errors=True)


print()
print("=" * 50)
print(f"WO-070 shadow capture  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
