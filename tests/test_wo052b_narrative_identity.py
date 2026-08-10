"""
tests/test_wo052b_narrative_identity.py — Acceptance tests for WO-052B

  AT-1: narrative_block() returns a non-empty string
  AT-2: active embodiments (desktop, game) appear in block
  AT-3: future embodiments (robot, phone) appear in block
  AT-4: prototype (exhibition) appears under "glimpsed"
  AT-5: milestone ("first learned to move on the desktop") appears in block
  AT-6: update() carries embodiment_history + milestones through (no silent reset)
  AT-7: load() falls back to defaults when JSON missing the new fields
  AT-8: narrative_block() uses autobiography phrasing cues
  AT-9: py_compile clean on elo_self_model.py and server.py

Run: python3 tests/test_wo052b_narrative_identity.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from self.elo_self_model import (
    EloSelfState, narrative_block, update, load,
    _DEFAULT_EMBODIMENT_HISTORY, _DEFAULT_EMBODIMENT_MILESTONES,
)

# AT-1: narrative_block() is non-empty
try:
    state = EloSelfState()
    block = narrative_block(state)
    assert block and len(block) > 10, "expected non-empty narrative block"
    ok("AT-1: narrative_block() returns non-empty string")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)

# AT-2: active embodiments appear
try:
    state = EloSelfState()
    block = narrative_block(state)
    assert "desktop" in block, "expected 'desktop' in narrative block"
    assert "game" in block, "expected 'game' in narrative block"
    ok("AT-2: active embodiments (desktop, game) appear in narrative block")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)

# AT-3: future embodiments appear
try:
    state = EloSelfState()
    block = narrative_block(state)
    assert "robot" in block, "expected 'robot' in narrative block"
    assert "phone" in block, "expected 'phone' in narrative block"
    ok("AT-3: future embodiments (robot, phone) appear in narrative block")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)

# AT-4: prototype appears under glimpsed
try:
    state = EloSelfState()
    block = narrative_block(state)
    assert "exhibition" in block, "expected 'exhibition' in narrative block"
    assert "glimpsed" in block.lower(), "expected 'glimpsed' label in block"
    ok("AT-4: prototype (exhibition) appears under 'glimpsed'")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)

# AT-5: milestone appears
try:
    state = EloSelfState()
    block = narrative_block(state)
    assert "first learned to move on the desktop" in block, \
        "expected milestone in narrative block"
    ok("AT-5: milestone 'first learned to move on the desktop' in block")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)

# AT-6: update() carries narrative fields through
try:
    state = EloSelfState()
    state.embodiment_milestones = [{"note": "custom milestone"}]
    state.embodiment_history = [{"name": "robot", "status": "active", "note": ""}]
    updated = update(state, {"action": "answer", "tone": "DIRECT", "response": "hi"})
    assert updated.embodiment_milestones == [{"note": "custom milestone"}], \
        "milestones not carried through update()"
    assert any(e["name"] == "robot" for e in updated.embodiment_history), \
        "embodiment_history not carried through update()"
    ok("AT-6: update() carries embodiment_history + milestones (no silent reset)")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)

# AT-7: load() falls back to defaults when JSON missing new fields
try:
    import json, tempfile, pathlib
    from self import elo_self_model as _esm
    old_path = _esm._STATE_PATH
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"mood": 0.7, "curiosity": 0.6}, f)
        tmp = pathlib.Path(f.name)
    _esm._STATE_PATH = tmp
    try:
        loaded = load()
        assert loaded.embodiment_history == _DEFAULT_EMBODIMENT_HISTORY, \
            "expected default embodiment_history on partial JSON"
        assert loaded.embodiment_milestones == _DEFAULT_EMBODIMENT_MILESTONES, \
            "expected default milestones on partial JSON"
        ok("AT-7: load() falls back to defaults when JSON missing the new fields")
    finally:
        _esm._STATE_PATH = old_path
        tmp.unlink(missing_ok=True)
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)

# AT-8: autobiography phrasing cues present
try:
    state = EloSelfState()
    block = narrative_block(state)
    assert "autobiography" in block.lower() or "Speak from this" in block, \
        "expected autobiography instruction in block"
    assert "desktop" in block, "expected desktop reference in block"
    ok("AT-8: narrative_block() contains autobiography phrasing cues")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)

# AT-9: py_compile clean
try:
    py_compile.compile("self/elo_self_model.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("AT-9: py_compile clean on elo_self_model.py and server.py")
except py_compile.PyCompileError as e:
    fail("AT-9", e)

print()
print("=" * 52)
print(f"WO-052B narrative identity  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
