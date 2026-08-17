"""
tests/test_fa_preserve_keys.py — F-A: expression survives a patch() that omits it

Card 0047 F-A: expression was absent from _PRESERVE_KEYS. Any patch() that
did not carry the expression block (e.g. a verbal-response write) nuked
shape_keys → visemes → lip-sync unreachable.

Tests:
    FA-1  expression in _PRESERVE_KEYS — the one-liner fix
    FA-2  motion, state, gaze, presence_plan also in _PRESERVE_KEYS
    FA-3  patch() that omits expression leaves existing expression block intact
    FA-4  animation_router._to_blender() routes through state_writer.patch(),
          not direct open(_BLENDER_PATH, "w")
    FA-5  _to_blender() + patch() leaves expression intact (integration)

Run: python3 tests/test_fa_preserve_keys.py
"""
import inspect
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── FA-1: expression in _PRESERVE_KEYS ───────────────────────────────────────
def test_fa1_expression_in_preserve_keys():
    from blender_bridge.state_writer import _PRESERVE_KEYS
    if "expression" not in _PRESERVE_KEYS:
        err("FA-1: 'expression' not in _PRESERVE_KEYS — lip-sync is droppable on any patch()")
    ok("FA-1: 'expression' in _PRESERVE_KEYS")


# ── FA-2: other core render fields in _PRESERVE_KEYS ─────────────────────────
def test_fa2_core_render_fields():
    from blender_bridge.state_writer import _PRESERVE_KEYS
    required = {"motion", "state", "gaze", "presence_plan"}
    missing = required - _PRESERVE_KEYS
    if missing:
        err(f"FA-2: core render fields absent from _PRESERVE_KEYS: {sorted(missing)}")
    ok(f"FA-2: motion·state·gaze·presence_plan all in _PRESERVE_KEYS")


# ── FA-3: patch() preserves existing expression when omitted ──────────────────
def test_fa3_patch_preserves_expression(tmp_path):
    state_file = tmp_path / "blender_state.json"
    existing = {
        "expression": {"shape_keys": {"A": 0.8, "viseme_PP": 0.6}},
        "motion": {"animation": "idle"},
        "mode": "idle",
    }
    state_file.write_text(json.dumps(existing))

    import blender_bridge.state_writer as sw
    orig_path = sw._STATE_PATH
    sw._STATE_PATH = str(state_file)
    try:
        # Patch with only 'mode' — expression must survive
        sw.patch({"mode": "speaking"})
        result = json.loads(state_file.read_text())
        if "expression" not in result:
            err("FA-3: patch() dropped 'expression' key entirely")
        if result["expression"].get("shape_keys") != {"A": 0.8, "viseme_PP": 0.6}:
            err(f"FA-3: expression.shape_keys corrupted: {result.get('expression')}")
    finally:
        sw._STATE_PATH = orig_path
    ok("FA-3: patch() that omits expression leaves existing block intact")


# ── FA-4: animation_router._to_blender() calls state_writer.patch() ──────────
def test_fa4_to_blender_uses_patch():
    from avatar import animation_router as ar
    src = inspect.getsource(ar._to_blender)
    if 'open(_BLENDER_PATH, "w")' in src or "open(_BLENDER_PATH, 'w')" in src:
        err("FA-4: _to_blender() still uses open(_BLENDER_PATH, 'w') — bypasses coordinator")
    if "state_writer" not in src and "_sw_patch" not in src:
        err("FA-4: _to_blender() does not call state_writer.patch() — bypass not fixed")
    ok("FA-4: _to_blender() routes through state_writer.patch() — coordinator honoured")


# ── FA-5: _to_blender() integration — expression survives animation call ──────
def test_fa5_to_blender_preserves_expression(tmp_path):
    state_file = tmp_path / "blender_state.json"
    existing = {
        "expression": {"shape_keys": {"A": 0.9}},
        "mode": "idle",
    }
    state_file.write_text(json.dumps(existing))

    import blender_bridge.state_writer as sw
    orig_path = sw._STATE_PATH
    sw._STATE_PATH = str(state_file)
    try:
        from avatar.animation_router import _to_blender
        _to_blender({"animation": "walk", "duration": 1.0, "intensity": 0.5})
        result = json.loads(state_file.read_text())
        if result.get("expression", {}).get("shape_keys", {}).get("A") != 0.9:
            err(f"FA-5: expression lost after _to_blender() call: {result.get('expression')}")
        if result.get("motion", {}).get("animation") != "walk":
            err(f"FA-5: motion not written: {result.get('motion')}")
    finally:
        sw._STATE_PATH = orig_path
    ok("FA-5: _to_blender() writes motion AND leaves existing expression intact")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("F-A — PRESERVE_KEYS core render fields (card 0047)")
    print()
    test_fa1_expression_in_preserve_keys()
    test_fa2_core_render_fields()

    with tempfile.TemporaryDirectory() as tmp:
        import pathlib
        test_fa3_patch_preserves_expression(pathlib.Path(tmp))
        test_fa5_to_blender_preserves_expression(pathlib.Path(tmp))

    test_fa4_to_blender_uses_patch()
    print()
    print("5/5 PASS — F-A: expression and core render fields survive all patch() and animation calls")
    print()
    print("PROVEN when: a patch() omitting expression leaves shape_keys intact in blender_state.json.")
    print("MT can now receive lip-sync visemes without them being dropped between writes.")
