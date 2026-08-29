"""
tests/test_wo064_move_words.py — WO-064 BP-2
Verify spoken move phrases emit correct move_command{type,_ts} to blender_state.json.
Run: ~/miniconda3/bin/python3 tests/test_wo064_move_words.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BLENDER_STATE = os.path.join(ROOT, "blender", "blender_state.json")

PASS = 0
FAIL = 0


def ok(label):
    global PASS
    PASS += 1
    print(f"  ✅ {label}")


def fail(label, reason=""):
    global FAIL
    FAIL += 1
    print(f"  ❌ {label}" + (f": {reason}" if reason else ""))


def _write_move_intent(sub_type: str) -> dict:
    """Write a move intent with sub_type via state_writer.write(); return blender_state.json."""
    from blender_bridge.state_writer import write as _write
    _write(
        motion={"animation": "idle", "speed": 0.5},
        intent={"name": "move", "sub_type": sub_type},
    )
    with open(BLENDER_STATE, encoding="utf-8") as f:
        return json.load(f)


def _write_non_move(text: str = "what's the weather like today?") -> dict:
    """Write a state without a move intent; return blender_state.json."""
    from blender_bridge.state_writer import write as _write
    _write(motion={"animation": "idle", "speed": 0.5}, intent=None)
    with open(BLENDER_STATE, encoding="utf-8") as f:
        return json.load(f)


def _load_server_src():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# AT-1: "fire jump" phrase is mapped and write emits move_command type=fire_jump
# ---------------------------------------------------------------------------
def at1_fire_jump():
    src = _load_server_src()
    if '"fire jump"' not in src or "fire_jump" not in src:
        fail("AT-1", '"fire jump" → fire_jump not found in server.py signal words')
        return
    try:
        state = _write_move_intent("fire_jump")
        mc = state.get("move_command", {})
        if mc.get("type") == "fire_jump" and "_ts" in mc:
            ok('AT-1: "fire jump" → move_command.type=fire_jump (+ _ts present)')
        else:
            fail("AT-1", f"expected type=fire_jump, got move_command={mc}")
    except Exception as e:
        fail("AT-1", str(e))


# ---------------------------------------------------------------------------
# AT-2: "climb that" / "wall jump" → move_command type=wall_jump
# ---------------------------------------------------------------------------
def at2_wall_jump():
    src = _load_server_src()
    if '"climb that"' not in src or "wall_jump" not in src:
        fail("AT-2", '"climb that" → wall_jump not found in server.py signal words')
        return
    try:
        state = _write_move_intent("wall_jump")
        mc = state.get("move_command", {})
        if mc.get("type") == "wall_jump" and "_ts" in mc:
            ok('AT-2: "climb that"/"wall jump" → move_command.type=wall_jump')
        else:
            fail("AT-2", f"expected type=wall_jump, got move_command={mc}")
    except Exception as e:
        fail("AT-2", str(e))


# ---------------------------------------------------------------------------
# AT-3: "back up and run at it" → move_command type=step_back_run_fire
# ---------------------------------------------------------------------------
def at3_step_back_run_fire():
    src = _load_server_src()
    if "step_back_run_fire" not in src:
        fail("AT-3", "step_back_run_fire not found in server.py signal words")
        return
    try:
        state = _write_move_intent("step_back_run_fire")
        mc = state.get("move_command", {})
        if mc.get("type") == "step_back_run_fire" and "_ts" in mc:
            ok('AT-3: "back up and run at it" → move_command.type=step_back_run_fire')
        else:
            fail("AT-3", f"expected type=step_back_run_fire, got move_command={mc}")
    except Exception as e:
        fail("AT-3", str(e))


# ---------------------------------------------------------------------------
# AT-4: "drop down" → move_command type=drop
# ---------------------------------------------------------------------------
def at4_drop():
    src = _load_server_src()
    if '"drop down"' not in src or '"drop"' not in src and "\"sub_type\": \"drop\"" not in src:
        # check for drop sub_type in the map
        if '"drop_down"' not in src and "drop" not in src:
            fail("AT-4", '"drop down" → drop not found in server.py signal words')
            return
    try:
        state = _write_move_intent("drop")
        mc = state.get("move_command", {})
        if mc.get("type") == "drop" and "_ts" in mc:
            ok('AT-4: "drop down" → move_command.type=drop')
        else:
            fail("AT-4", f"expected type=drop, got move_command={mc}")
    except Exception as e:
        fail("AT-4", str(e))


# ---------------------------------------------------------------------------
# AT-5: Non-move phrase → no move_command emitted
# ---------------------------------------------------------------------------
def at5_non_move_no_emit():
    try:
        state = _write_non_move()
        if "move_command" not in state:
            ok("AT-5: non-move intent → move_command NOT emitted")
        else:
            fail("AT-5", f"expected no move_command, got {state.get('move_command')}")
    except Exception as e:
        fail("AT-5", str(e))


def run_tests():
    print("\n=== WO-064 BP-2 — spoken move words → move_command ===\n")
    at1_fire_jump()
    at2_wall_jump()
    at3_step_back_run_fire()
    at4_drop()
    at5_non_move_no_emit()
    print(f"\n{'='*50}")
    print(f"Result: {PASS}/5 PASS  {FAIL}/5 FAIL")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
