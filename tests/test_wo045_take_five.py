"""
tests/test_wo045_take_five.py — WO-045 "take five" privacy pop-off (Builder lane)

Spec: "take 5" → leave_command in blender_state.json; "come back" → return_command.
Privacy pop-off must be detectable in server.py _SIGNAL_WORDS and state_writer must
emit the correct command fields when those intents fire.

AT-1  All privacy phrases present in server.py _SIGNAL_WORDS → step_out
AT-2  Return phrases (come back / you there) map to return_elo in _SIGNAL_WORDS
AT-3  state_writer.write(intent='step_out') emits leave_command with _ts field
AT-4  state_writer.write(intent='return_elo') emits return_command with _ts field
AT-5  write_with_presence(intent='step_out') also emits leave_command (both paths covered)
AT-6  py_compile clean on server.py + state_writer.py
"""
import os
import sys
import json
import tempfile
import py_compile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT          = os.path.join(os.path.dirname(__file__), "..")
_SERVER_PY     = os.path.join(_ROOT, "server.py")
_SW_PY         = os.path.join(_ROOT, "blender_bridge", "state_writer.py")

_IDLE_MOTION = {
    "animation": "idle",
    "speed": 0.5,
    "intensity": 0.5,
    "duration": 4.0,
    "mood": "neutral",
    "mode": "idle",
}


def _sw_module():
    import blender_bridge.state_writer as _sw
    return _sw


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_privacy_phrases_in_signal_words():
    """
    All "take five" family phrases must be present in server.py _SIGNAL_WORDS
    mapping to step_out intent. Missing a phrase means David saying it gets no
    pop-off, leaving eLo listening when privacy was requested.
    """
    src = open(_SERVER_PY, encoding="utf-8").read()
    required = [
        "take 5", "take five", "give me a minute",
        "some privacy", "step away", "leave me to it", "pop off",
    ]
    missing = [p for p in required if f'"{p}"' not in src and f"'{p}'" not in src]
    assert not missing, (
        f"AT-1 FAIL: missing privacy phrases from _SIGNAL_WORDS: {missing}"
    )


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_return_phrases_map_to_return_elo():
    """
    Return phrases ("come back", "you there") must map to return_elo in
    server.py _SIGNAL_WORDS so eLo knows to resume from pop-off.
    """
    src = open(_SERVER_PY, encoding="utf-8").read()
    assert '"return_elo"' in src or "'return_elo'" in src, (
        "AT-2 FAIL: 'return_elo' intent not found in server.py _SIGNAL_WORDS"
    )
    assert '"come back"' in src or "'come back'" in src, (
        "AT-2 FAIL: 'come back' phrase not in server.py _SIGNAL_WORDS"
    )
    assert '"you there"' in src or "'you there'" in src, (
        "AT-2 FAIL: 'you there' phrase not in server.py _SIGNAL_WORDS"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_state_writer_write_step_out_emits_leave_command():
    """
    state_writer.write(intent='step_out') must produce a payload with a
    leave_command key containing a _ts timestamp. This is the Unity signal
    that triggers eLo to step back / reduce presence.
    """
    sw = _sw_module()
    orig_path = sw._STATE_PATH
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    sw._STATE_PATH = tmp.name
    try:
        sw.write(motion=_IDLE_MOTION, intent="step_out")
        result = json.loads(open(tmp.name).read())
        assert "leave_command" in result, (
            f"AT-3 FAIL: leave_command not in payload keys: {list(result.keys())}"
        )
        assert "_ts" in result["leave_command"], (
            f"AT-3 FAIL: leave_command missing _ts: {result['leave_command']}"
        )
    finally:
        sw._STATE_PATH = orig_path
        try: os.unlink(tmp.name)
        except: pass


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_state_writer_write_return_elo_emits_return_command():
    """
    state_writer.write(intent='return_elo') must produce a payload with a
    return_command key containing _ts. This signals Unity to resume eLo presence.
    """
    sw = _sw_module()
    orig_path = sw._STATE_PATH
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    sw._STATE_PATH = tmp.name
    try:
        sw.write(motion=_IDLE_MOTION, intent="return_elo")
        result = json.loads(open(tmp.name).read())
        assert "return_command" in result, (
            f"AT-4 FAIL: return_command not in payload keys: {list(result.keys())}"
        )
        assert "_ts" in result["return_command"], (
            f"AT-4 FAIL: return_command missing _ts: {result['return_command']}"
        )
    finally:
        sw._STATE_PATH = orig_path
        try: os.unlink(tmp.name)
        except: pass


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_write_with_presence_step_out_emits_leave_command():
    """
    write_with_presence(intent='step_out') must also emit leave_command — this
    path is called from the presence-aware server path, not just the direct path.
    Both server paths must honour the pop-off signal.
    """
    sw = _sw_module()
    orig_path = sw._STATE_PATH
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    sw._STATE_PATH = tmp.name
    try:
        sw.write_with_presence(motion=_IDLE_MOTION, intent="step_out")
        result = json.loads(open(tmp.name).read())
        assert "leave_command" in result, (
            f"AT-5 FAIL: leave_command not in write_with_presence payload: {list(result.keys())}"
        )
        assert "_ts" in result["leave_command"], (
            f"AT-5 FAIL: leave_command missing _ts in write_with_presence result"
        )
    finally:
        sw._STATE_PATH = orig_path
        try: os.unlink(tmp.name)
        except: pass


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_py_compile_clean():
    for path in (_SERVER_PY, _SW_PY):
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"AT-6 FAIL: {os.path.basename(path)} does not compile: {e}")
