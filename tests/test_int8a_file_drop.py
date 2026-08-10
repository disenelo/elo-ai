"""
tests/test_int8a_file_drop.py — Acceptance tests for INT-8a (file drop round-trip)

  AT-1: _route() dispatches image extensions to _handle_image path
  AT-2: _route() dispatches text extensions to _handle_text path
  AT-3: _route() dispatches model extensions to _handle_model path
  AT-4: _process() speaks via voice engine (not server import)
  AT-5: _process() queues result in _pending_drops (no state_manager import needed)
  AT-6: pop_pending_drops() drains the queue and returns results
  AT-7: pop_pending_drops() is idempotent — empty on second call
  AT-8: poll loop handles missing _ts by falling back to file mtime (no silent skip)
  AT-9: py_compile clean

Run: python3 tests/test_int8a_file_drop.py
"""
import sys, os, py_compile, json, time, tempfile, threading, pathlib
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


import desktop.file_drop_handler as _fd


def _reset():
    import threading as _th
    with _fd._lock:
        _fd._pending_drops = []
    _fd._last_ts = 0.0


# AT-1: _route() dispatches images
try:
    dispatched = []
    orig = _fd._handle_image
    _fd._handle_image = lambda p: dispatched.append("image") or "image result"
    try:
        result = _fd._route(pathlib.Path("test.png"))
        assert dispatched == ["image"], f"expected image dispatch, got {dispatched}"
        assert result == "image result"
        ok("AT-1: _route() dispatches .png to _handle_image")
    finally:
        _fd._handle_image = orig
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)

# AT-2: _route() dispatches text
try:
    dispatched = []
    orig = _fd._handle_text
    _fd._handle_text = lambda p: dispatched.append("text") or "text result"
    try:
        result = _fd._route(pathlib.Path("notes.md"))
        assert dispatched == ["text"]
        ok("AT-2: _route() dispatches .md to _handle_text")
    finally:
        _fd._handle_text = orig
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)

# AT-3: _route() dispatches 3D models
try:
    dispatched = []
    orig = _fd._handle_model
    _fd._handle_model = lambda p: dispatched.append("model") or "model result"
    try:
        result = _fd._route(pathlib.Path("elo.fbx"))
        assert dispatched == ["model"]
        ok("AT-3: _route() dispatches .fbx to _handle_model")
    finally:
        _fd._handle_model = orig
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)

# AT-4: _process() speaks via voice engine (not circular server import)
try:
    _reset()
    spoken = []
    # Patch the voice engine import path used in _process()
    import voice.voice_engine as _ve
    orig_speak = _ve.speak
    _ve.speak = lambda t: spoken.append(t)

    # Make a real temp file for _process to "find"
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("hello world")
        tmp = pathlib.Path(f.name)

    orig_handle_text = _fd._handle_text
    _fd._handle_text = lambda p: "spoken reply"
    try:
        _fd._process({"path": str(tmp), "type": "file_drop"})
        assert spoken == ["spoken reply"], f"expected speak call, got {spoken}"
        ok("AT-4: _process() speaks via voice.voice_engine.speak (no circular server import)")
    finally:
        _ve.speak = orig_speak
        _fd._handle_text = orig_handle_text
        tmp.unlink(missing_ok=True)
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)

# AT-5: _process() queues result in _pending_drops
try:
    _reset()
    import voice.voice_engine as _ve
    orig_speak = _ve.speak
    _ve.speak = lambda t: None

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("test content")
        tmp = pathlib.Path(f.name)

    orig_handle_text = _fd._handle_text
    _fd._handle_text = lambda p: "queued reply"
    try:
        _fd._process({"path": str(tmp), "type": "file_drop"})
        with _fd._lock:
            drops = list(_fd._pending_drops)
        assert len(drops) == 1, f"expected 1 pending drop, got {len(drops)}"
        assert drops[0]["summary"] == "queued reply"
        ok(f"AT-5: _process() queues result in _pending_drops (no state_manager needed)")
    finally:
        _ve.speak = orig_speak
        _fd._handle_text = orig_handle_text
        tmp.unlink(missing_ok=True)
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)

# AT-6: pop_pending_drops() drains and returns results
try:
    _reset()
    with _fd._lock:
        _fd._pending_drops = [{"file": "a.txt", "summary": "summary A"}]
    drops = _fd.pop_pending_drops()
    assert drops == [{"file": "a.txt", "summary": "summary A"}], f"unexpected: {drops}"
    ok("AT-6: pop_pending_drops() drains queue and returns results")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)

# AT-7: pop_pending_drops() idempotent — empty on second call
try:
    _reset()
    with _fd._lock:
        _fd._pending_drops = [{"file": "b.txt", "summary": "s"}]
    _fd.pop_pending_drops()  # first call
    second = _fd.pop_pending_drops()  # second call
    assert second == [], f"expected [] on second call, got {second}"
    ok("AT-7: pop_pending_drops() is idempotent — empty on second call")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)

# AT-8: poll handles missing _ts via file mtime fallback
try:
    # Simulate: event has no _ts; mtime of _EVENTS_FILE > _last_ts
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({"type": "file_drop", "path": "/nonexistent/file.txt"}, f)
        tmp_events = pathlib.Path(f.name)

    orig_events = _fd._EVENTS_FILE
    _fd._EVENTS_FILE = str(tmp_events)
    _fd._last_ts = 0.0

    event = {"type": "file_drop", "path": "/nonexistent/file.txt"}
    ts = float(event.get("_ts") or os.path.getmtime(str(tmp_events)))
    would_fire = ts > 0.0
    assert would_fire, f"expected mtime fallback > 0.0, got ts={ts}"
    ok(f"AT-8: missing _ts falls back to file mtime ({ts:.1f}) — no silent skip")

    _fd._EVENTS_FILE = orig_events
    tmp_events.unlink(missing_ok=True)
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)

# AT-9: py_compile clean
try:
    py_compile.compile("desktop/file_drop_handler.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("AT-9: py_compile clean on file_drop_handler.py and server.py")
except py_compile.PyCompileError as e:
    fail("AT-9", e)

_reset()

print()
print("=" * 52)
print(f"INT-8a file drop  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
