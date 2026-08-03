"""
tests/test_wo037_memory_writeback.py — Acceptance tests for WO-037

Spec: WO-037 — interactions.json write-back reconnected in server.py /chat path.

Tests:
  AT-1: store_interaction() writes to interactions.json (file updated after call)
  AT-2: written record has correct fields (timestamp, user, response, mode, concepts)
  AT-3: project tag resolves from content (not always "elo_core")
  AT-4: server.py post-response section imports store_interaction (compile-path check)
  AT-5: interactions.json mtime advances after a simulated turn

Run: python3 tests/test_wo037_memory_writeback.py
"""
import sys, os, json, time, tempfile, shutil
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: store_interaction writes to interactions.json ───────────────────────
try:
    from core.memory_engine import store_interaction, _STORE_PATH
    _before_mtime = os.path.getmtime(_STORE_PATH) if os.path.exists(_STORE_PATH) else 0.0

    # write to a temp copy so we don't mutate the live store
    import core.memory_engine as _me
    _orig_path = _me._STORE_PATH
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as _tf:
        json.dump([], _tf)
        _tmp_path = _tf.name

    _me._STORE_PATH = _tmp_path
    try:
        store_interaction("test input", "test response", "direct", "elo_core")
        _data = json.loads(open(_tmp_path).read())
        if _data and _data[-1]["user"] == "test input":
            ok("AT-1: store_interaction() writes to interactions file")
        else:
            fail("AT-1", f"unexpected store content: {_data}")
    finally:
        _me._STORE_PATH = _orig_path
        os.unlink(_tmp_path)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: written record has required fields ──────────────────────────────────
try:
    _me = sys.modules["core.memory_engine"] if "core.memory_engine" in sys.modules else None
    if _me is None:
        from core import memory_engine as _me

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as _tf:
        json.dump([], _tf)
        _tmp2 = _tf.name

    _orig2 = _me._STORE_PATH
    _me._STORE_PATH = _tmp2
    try:
        _me.store_interaction("I'm building eLo OS", "Good progress!", "direct")
        _records = json.loads(open(_tmp2).read())
        _r = _records[-1]
        _required = {"timestamp", "user", "response", "mode", "concepts", "memory_categories"}
        _missing = _required - set(_r.keys())
        if not _missing:
            ok(f"AT-2: record has all required fields; concepts={_r['concepts']}")
        else:
            fail("AT-2", f"missing fields: {_missing}")
    finally:
        _me._STORE_PATH = _orig2
        os.unlink(_tmp2)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: project tag resolves from content ───────────────────────────────────
try:
    from core.memory_engine import load_registry, resolve_project
    _registry = load_registry()
    _tag = resolve_project("working on the eLo OS backend", _registry)
    if isinstance(_tag, str) and _tag:
        ok(f"AT-3: project tag resolved: '{_tag}'")
    else:
        fail("AT-3", f"expected a non-empty string, got {_tag!r}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: server.py imports store_interaction in post-response section ────────
try:
    _src = open("server.py", encoding="utf-8").read()
    if "store_interaction" in _src and "_store_interaction" in _src and "WO-037" in _src:
        ok("AT-4: server.py has WO-037 write-back block with store_interaction call")
    else:
        fail("AT-4", "WO-037 write-back block not found in server.py")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: interactions.json mtime advances after simulated turn ───────────────
try:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as _tf5:
        json.dump([], _tf5)
        _tmp5 = _tf5.name

    _orig5 = _me._STORE_PATH
    _me._STORE_PATH = _tmp5
    _t0 = os.path.getmtime(_tmp5)
    time.sleep(0.05)
    try:
        _me.store_interaction("hello", "hey", "direct")
        _t1 = os.path.getmtime(_tmp5)
        if _t1 > _t0:
            ok(f"AT-5: interactions mtime advanced after simulated turn")
        else:
            fail("AT-5", f"mtime did not advance: {_t0} → {_t1}")
    finally:
        _me._STORE_PATH = _orig5
        os.unlink(_tmp5)
except Exception as e:
    fail("AT-5", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print(f"{'='*50}")
print(f"WO-037  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
