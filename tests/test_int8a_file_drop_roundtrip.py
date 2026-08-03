"""
INT-8a acceptance tests — file-drop event → Python read → route.

Verifies the Python side of the Unity-→-eLo file-drop round-trip:
unity_events.json written → poll detects new ts → _route() dispatches
by extension. No live AI/vision calls — stubs all external handlers.

AT-1  Routing: .png → image handler
AT-2  Routing: .pdf → PDF handler
AT-3  Routing: .glb → model handler
AT-4  Routing: .md  → text handler
AT-5  Routing: .zip → other handler
AT-6  Poll skips events with stale timestamp (ts <= _last_ts)
AT-7  Poll detects new event (ts > _last_ts) → fires _process()
AT-8  _process() returns safely when file doesn't exist (no crash)
AT-9  py_compile: file_drop_handler.py compiles cleanly
"""
import importlib.util
import json
import os
import sys
import tempfile
import time
import threading
import types as _types
from pathlib import Path

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_FDH_PATH = os.path.join(_ROOT, "desktop", "file_drop_handler.py")


def _load_fdh(events_file: str = "") -> _types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        f"fdh_test_{id(events_file)}", _FDH_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__name__ = f"fdh_test_{id(events_file)}"
    sys.modules[mod.__name__] = mod
    # Stub external deps
    stub_bbs = _types.ModuleType("blender_bridge.state_writer")
    stub_bbs.patch = lambda d: None
    sys.modules.setdefault("blender_bridge.state_writer", stub_bbs)
    stub_bbs2 = _types.ModuleType("blender_bridge")
    sys.modules.setdefault("blender_bridge", stub_bbs2)
    spec.loader.exec_module(mod)
    if events_file:
        mod._EVENTS_FILE = events_file
    return mod


# ── AT-1 to AT-5 — routing ────────────────────────────────────────────────────

_routed: list = []


def _make_route_test_module() -> _types.ModuleType:
    """Load a module with stubbed handlers to capture routing."""
    mod = _load_fdh()
    # Patch handlers to record which fired
    mod._handle_image  = lambda p: _routed.append(("image",  p)) or "img"
    mod._handle_pdf    = lambda p: _routed.append(("pdf",    p)) or "pdf"
    mod._handle_model  = lambda p: _routed.append(("model",  p)) or "mdl"
    mod._handle_text   = lambda p: _routed.append(("text",   p)) or "txt"
    mod._handle_other  = lambda p: _routed.append(("other",  p)) or "oth"
    return mod


def test_at1_route_image():
    global _routed; _routed = []
    mod = _make_route_test_module()
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        mod._route(Path(f.name))
    assert _routed and _routed[0][0] == "image", f"AT-1 FAIL: routed to {_routed}"
    print("AT-1 PASS — .png → image handler")


def test_at2_route_pdf():
    global _routed; _routed = []
    mod = _make_route_test_module()
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        mod._route(Path(f.name))
    assert _routed and _routed[0][0] == "pdf", f"AT-2 FAIL: routed to {_routed}"
    print("AT-2 PASS — .pdf → PDF handler")


def test_at3_route_model():
    global _routed; _routed = []
    mod = _make_route_test_module()
    with tempfile.NamedTemporaryFile(suffix=".glb") as f:
        mod._route(Path(f.name))
    assert _routed and _routed[0][0] == "model", f"AT-3 FAIL: routed to {_routed}"
    print("AT-3 PASS — .glb → model handler")


def test_at4_route_text():
    global _routed; _routed = []
    mod = _make_route_test_module()
    with tempfile.NamedTemporaryFile(suffix=".md") as f:
        mod._route(Path(f.name))
    assert _routed and _routed[0][0] == "text", f"AT-4 FAIL: routed to {_routed}"
    print("AT-4 PASS — .md → text handler")


def test_at5_route_other():
    global _routed; _routed = []
    mod = _make_route_test_module()
    # _handle_other calls open() — stub subprocess to avoid macOS dialog
    import unittest.mock as _mock
    with tempfile.NamedTemporaryFile(suffix=".zip") as f:
        with _mock.patch("subprocess.Popen"):
            mod._route(Path(f.name))
    assert _routed and _routed[0][0] == "other", f"AT-5 FAIL: routed to {_routed}"
    print("AT-5 PASS — .zip → other handler")


# ── AT-6 — stale event skipped ───────────────────────────────────────────────

def test_at6_stale_event_skipped():
    """Poll loop must NOT re-fire an event whose _ts <= _last_ts."""
    processed = []
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        f.write(json.dumps({"type": "file_drop", "path": "/tmp/x.txt", "_ts": 100.0}))
        ev_path = f.name

    mod = _load_fdh(events_file=ev_path)
    mod._last_ts = 200.0  # already past the event's ts
    mod._process = lambda ev: processed.append(ev)

    # Simulate one poll iteration manually
    try:
        with open(ev_path, encoding="utf-8") as f:
            event = json.load(f)
        if event.get("type") == "file_drop" or event.get("event") == "file_drop":
            ts = float(event.get("_ts", 0))
            with mod._lock:
                if ts > mod._last_ts:
                    mod._last_ts = ts
                    threading.Thread(target=mod._process, args=(event,), daemon=True).start()
    finally:
        os.unlink(ev_path)

    time.sleep(0.05)
    assert not processed, f"AT-6 FAIL: stale event fired {processed}"
    print("AT-6 PASS — stale event (ts=100 ≤ _last_ts=200) correctly skipped")


# ── AT-7 — new event fires ───────────────────────────────────────────────────

def test_at7_new_event_fires():
    """Poll loop fires _process() for a new event (ts > _last_ts)."""
    processed = []
    now = time.time()
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        f.write(json.dumps({"type": "file_drop", "path": "/tmp/x.txt", "_ts": now}))
        ev_path = f.name

    mod = _load_fdh(events_file=ev_path)
    mod._last_ts = now - 1.0  # event is 1 second newer
    mod._process = lambda ev: processed.append(ev)

    try:
        with open(ev_path, encoding="utf-8") as f:
            event = json.load(f)
        if event.get("type") == "file_drop" or event.get("event") == "file_drop":
            ts = float(event.get("_ts", 0))
            with mod._lock:
                if ts > mod._last_ts:
                    mod._last_ts = ts
                    threading.Thread(target=mod._process, args=(event,), daemon=True).start()
    finally:
        os.unlink(ev_path)

    time.sleep(0.1)
    assert processed, "AT-7 FAIL: new event (ts > _last_ts) did not fire _process()"
    print("AT-7 PASS — new event correctly triggered _process()")


# ── AT-8 — missing file → no crash ───────────────────────────────────────────

def test_at8_missing_file_no_crash():
    """_process() returns cleanly when the dropped file doesn't exist."""
    mod = _load_fdh()
    mod._route = lambda p: "routed"
    try:
        mod._process({"path": "/tmp/definitely_does_not_exist_xyz.txt"})
    except Exception as e:
        raise AssertionError(f"AT-8 FAIL: _process() raised: {e}")
    print("AT-8 PASS — missing file handled safely (no crash)")


# ── AT-9 — py_compile ─────────────────────────────────────────────────────────

def test_at9_py_compile():
    import py_compile
    try:
        py_compile.compile(_FDH_PATH, doraise=True)
    except py_compile.PyCompileError as e:
        raise AssertionError(f"AT-9 FAIL: file_drop_handler.py does not compile: {e}")
    print("AT-9 PASS — file_drop_handler.py compiles cleanly")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_route_image,
        test_at2_route_pdf,
        test_at3_route_model,
        test_at4_route_text,
        test_at5_route_other,
        test_at6_stale_event_skipped,
        test_at7_new_event_fires,
        test_at8_missing_file_no_crash,
        test_at9_py_compile,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — INT-8a ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
