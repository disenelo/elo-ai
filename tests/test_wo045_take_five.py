"""
tests/test_wo045_take_five.py — Acceptance tests for WO-045 (Builder lane)

Spec: "take 5" → leave_command in blender_state.json; "come back" → return_command
  1. Privacy phrases in _SIGNAL_WORDS → step_out
  2. Return phrases in _SIGNAL_WORDS → return_elo
  3. state_writer emits leave_command when intent == "step_out"
  4. state_writer emits return_command when intent == "return_elo"
  5. py_compile clean

Run: python3 tests/test_wo045_take_five.py
"""
import sys, os, json, tempfile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: privacy phrases map to step_out in _SIGNAL_WORDS ───────────────────
try:
    _src = open("server.py", encoding="utf-8").read()
    required = ["take 5", "take five", "give me a minute", "some privacy",
                "step away", "leave me to it", "pop off"]
    missing  = [p for p in required if f'"{p}"' not in _src and f"'{p}'" not in _src]
    if missing:
        fail("AT-1", f"missing privacy phrases: {missing}")
    else:
        ok(f"AT-1: all privacy phrases present in _SIGNAL_WORDS ({len(required)} checked)")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: return phrases map to return_elo ───────────────────────────────────
try:
    _src = open("server.py", encoding="utf-8").read()
    if '"return_elo"' in _src and '"come back"' in _src and '"you there"' in _src:
        ok('AT-2: return phrases (come back / you there) → return_elo in _SIGNAL_WORDS')
    else:
        fail("AT-2", "return_elo / come back / you there not all in _SIGNAL_WORDS")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: state_writer emits leave_command on step_out intent ────────────────
try:
    import blender_bridge.state_writer as _sw
    import blender_bridge.state_writer as _sw_mod
    # Patch _STATE_PATH to a temp file
    _orig = _sw_mod._STATE_PATH
    _tmp  = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    _tmp.close()
    _sw_mod._STATE_PATH = _tmp.name

    _sw.write(
        motion={"animation": "idle", "speed": 0.5, "intensity": 0.5, "duration": 4.0, "mood": "neutral", "mode": "idle"},
        intent="step_out",
    )
    with open(_tmp.name, encoding="utf-8") as f:
        result = json.load(f)
    os.unlink(_tmp.name)
    _sw_mod._STATE_PATH = _orig

    if "leave_command" in result and "_ts" in result["leave_command"]:
        ok(f"AT-3: state_writer.write(intent='step_out') emits leave_command._ts")
    else:
        fail("AT-3", f"leave_command not in payload: {list(result.keys())}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: state_writer emits return_command on return_elo intent ─────────────
try:
    _orig = _sw_mod._STATE_PATH
    _tmp  = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    _tmp.close()
    _sw_mod._STATE_PATH = _tmp.name

    _sw.write(
        motion={"animation": "idle", "speed": 0.5, "intensity": 0.5, "duration": 4.0, "mood": "neutral", "mode": "idle"},
        intent="return_elo",
    )
    with open(_tmp.name, encoding="utf-8") as f:
        result = json.load(f)
    os.unlink(_tmp.name)
    _sw_mod._STATE_PATH = _orig

    if "return_command" in result and "_ts" in result["return_command"]:
        ok(f"AT-4: state_writer.write(intent='return_elo') emits return_command._ts")
    else:
        fail("AT-4", f"return_command not in payload: {list(result.keys())}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: write_with_presence also emits leave_command ───────────────────────
try:
    _orig = _sw_mod._STATE_PATH
    _tmp  = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    _tmp.close()
    _sw_mod._STATE_PATH = _tmp.name

    _sw.write_with_presence(
        motion={"animation": "idle", "speed": 0.5, "intensity": 0.5, "duration": 4.0, "mood": "neutral", "mode": "idle"},
        intent="step_out",
    )
    with open(_tmp.name, encoding="utf-8") as f:
        result = json.load(f)
    os.unlink(_tmp.name)
    _sw_mod._STATE_PATH = _orig

    if "leave_command" in result and "_ts" in result["leave_command"]:
        ok("AT-5: write_with_presence(intent='step_out') also emits leave_command")
    else:
        fail("AT-5", f"leave_command not in write_with_presence payload: {list(result.keys())}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("server.py", doraise=True)
    py_compile.compile("blender_bridge/state_writer.py", doraise=True)
    ok("AT-6: py_compile clean on server.py + state_writer.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 50)
print(f"WO-045  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
