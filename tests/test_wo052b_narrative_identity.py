"""
tests/test_wo052b_narrative_identity.py — Acceptance tests for WO-052B
(updated by Card 0019 P0-A — Vol XXI · D-XXI-2, Verified Speech)

WO-052B originally shipped with hard-coded fabricated defaults ("adventuring
in eLo-Planet", "first learned to move on the desktop") — Card 0019 removed
those. The narrative_block() function must:

  1. Produce an honest "no autobiography yet" block when history + milestones
     are empty (defaults).
  2. Still narrate correctly when history + milestones are populated with
     verified events.

  AT-1: narrative_block() returns a non-empty string with an empty state
  AT-2: default state's block explicitly declines to invent a past
  AT-3: default state's block contains NO fabricated embodiment names
  AT-4: populated state narrates active / prototype / future correctly
  AT-5: populated state emits its milestones
  AT-6: update() carries embodiment_history + milestones through (no silent reset)
  AT-7: load() falls back to EMPTY defaults when JSON is missing the new fields
  AT-8: narrative_block() never fabricates when history is empty
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

# AT-1: narrative_block() is non-empty even with empty state
try:
    state = EloSelfState()
    block = narrative_block(state)
    assert block and len(block) > 10, "expected non-empty narrative block"
    ok("AT-1: narrative_block() returns non-empty string")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)

# AT-2: default state's block explicitly declines to invent a past
try:
    state = EloSelfState()
    block = narrative_block(state).lower()
    assert "no verified autobiography yet" in block, \
        "expected honest 'no autobiography yet' phrasing on empty state"
    assert "do not invent" in block or "silence is the correct answer" in block, \
        "expected explicit anti-fabrication instruction on empty state"
    ok("AT-2: empty state block explicitly declines to invent a past")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)

# AT-3: default state's block contains NO fabricated embodiment names
try:
    state = EloSelfState()
    block = narrative_block(state).lower()
    for tainted in ("adventuring in elo-planet", "one day a physical body",
                    "early glimpses", "where i've mostly lived",
                    "first learned to move on the desktop"):
        assert tainted not in block, f"empty-state block leaked tainted default: '{tainted}'"
    # "current: desktop" is a live embodiment fact from state.embodiment — fine.
    # But invented history entries ('lived in: game', 'yet to come: robot') must NOT appear.
    assert "lived in:" not in block, "empty state should not narrate 'lived in'"
    assert "yet to come:" not in block, "empty state should not narrate 'yet to come'"
    assert "glimpsed:" not in block, "empty state should not narrate 'glimpsed'"
    ok("AT-3: empty state block contains no fabricated embodiment history")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)

# AT-4: populated state narrates active / prototype / future correctly
try:
    state = EloSelfState()
    state.embodiment_history = [
        {"name": "desktop",    "status": "active",    "note": ""},
        {"name": "exhibition", "status": "prototype", "note": ""},
        {"name": "robot",      "status": "future",    "note": ""},
    ]
    block = narrative_block(state)
    assert "desktop" in block, "populated state missing 'desktop' under lived in"
    assert "exhibition" in block, "populated state missing 'exhibition' under glimpsed"
    assert "robot" in block, "populated state missing 'robot' under yet to come"
    assert "glimpsed" in block.lower(), "populated state missing 'glimpsed' label"
    ok("AT-4: populated state narrates active / prototype / future correctly")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)

# AT-5: populated state emits its milestones
try:
    state = EloSelfState()
    state.embodiment_milestones = [{"note": "handed something back for the first time"}]
    state.embodiment_history = [{"name": "desktop", "status": "active", "note": ""}]
    block = narrative_block(state)
    assert "handed something back for the first time" in block, \
        "populated milestone missing from block"
    ok("AT-5: populated state emits its milestones")
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

# AT-7: load() falls back to EMPTY defaults when JSON missing new fields
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
        assert loaded.embodiment_history == [], \
            f"expected empty embodiment_history on partial JSON, got {loaded.embodiment_history!r}"
        assert loaded.embodiment_milestones == [], \
            f"expected empty milestones on partial JSON, got {loaded.embodiment_milestones!r}"
        assert _DEFAULT_EMBODIMENT_HISTORY == [], "module-level default must be empty"
        assert _DEFAULT_EMBODIMENT_MILESTONES == [], "module-level milestones default must be empty"
        ok("AT-7: load() falls back to EMPTY defaults on partial JSON")
    finally:
        _esm._STATE_PATH = old_path
        tmp.unlink(missing_ok=True)
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)

# AT-8: narrative_block() never fabricates when history is empty
try:
    # Every possible tainted phrase from the old defaults must be absent
    state = EloSelfState()
    block = narrative_block(state)
    tainted_names = ["game", "exhibition", "phone", "AR", "hologram"]
    for name in tainted_names:
        # 'game' could conceivably appear in other prose — but under a "lived in"
        # or "glimpsed" or "yet to come" line, that's fabrication.
        for label in ("lived in: ", "glimpsed: ", "yet to come: "):
            assert (label + name) not in block, \
                f"empty state leaked '{label}{name}' — fabricated embodiment"
            assert (label + name + ",") not in block, \
                f"empty state leaked '{label}{name},' — fabricated embodiment"
    ok("AT-8: narrative_block() never fabricates on empty history")
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
