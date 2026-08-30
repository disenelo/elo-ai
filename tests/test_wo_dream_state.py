"""
tests/test_wo_dream_state.py — WO-DREAM-STATE acceptance tests.

AT-1: With asleep=true, run_dream_window() does NOT emit user-facing response (response=None).
AT-2: dream_log.jsonl written with valid entry after dream cycle.
AT-3: dream_faculty.run_dream() invoked during asleep window (ran=True in result).
AT-4: creative_imagination path in LOOP-8 (spine.py) unchanged — not broken.
AT-5: When asleep=false, run_dream_window() returns action="awake", ran=False.
AT-6: py_compile clean on executive.py.

Run: python3 tests/test_wo_dream_state.py
"""
from __future__ import annotations
import sys, os, json, py_compile, tempfile, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── helpers ───────────────────────────────────────────────────────────────────
import runtime.executive as _exec_mod

_ORIG_BLENDER = _exec_mod._BLENDER_STATE_PATH
_ORIG_DREAM_LOG = _exec_mod._DREAM_LOG_PATH


def _use_temp_blender(asleep: bool) -> tuple[str, str]:
    """Write a temp blender_state.json and dream log dir; return (bs_path, log_dir)."""
    _tmp = tempfile.mkdtemp(prefix="wo_dream_test_")
    _bs  = os.path.join(_tmp, "blender_state.json")
    with open(_bs, "w") as _f:
        json.dump({"asleep": asleep}, _f)
    _log = os.path.join(_tmp, "dream_log.jsonl")
    return _bs, _log, _tmp


def _restore():
    _exec_mod._BLENDER_STATE_PATH = _ORIG_BLENDER
    _exec_mod._DREAM_LOG_PATH     = _ORIG_DREAM_LOG


# ── AT-1: asleep=true → response=None (no user-facing output) ─────────────────
try:
    _bs, _log, _tmp = _use_temp_blender(asleep=True)
    _exec_mod._BLENDER_STATE_PATH = _bs
    _exec_mod._DREAM_LOG_PATH     = _log

    _result = _exec_mod.run_dream_window(recent_topics=["creativity", "connection"])
    assert _result.get("response") is None, \
        f"dream window must not emit response; got: {_result.get('response')!r}"
    assert _result.get("action") == "dream", \
        f"action should be 'dream', got: {_result.get('action')}"
    shutil.rmtree(_tmp)
    _restore()
    ok(f"AT-1: asleep=true → action='dream', response=None")
except AssertionError as e:
    _restore()
    fail("AT-1", e)
except Exception as e:
    _restore()
    fail("AT-1", e)


# ── AT-2: dream_log.jsonl written with valid entry ────────────────────────────
try:
    _bs, _log, _tmp = _use_temp_blender(asleep=True)
    _exec_mod._BLENDER_STATE_PATH = _bs
    _exec_mod._DREAM_LOG_PATH     = _log

    _exec_mod.run_dream_window(recent_topics=[])

    assert os.path.exists(_log), f"dream_log.jsonl not created at: {_log}"
    with open(_log) as _f:
        _entries = [json.loads(l) for l in _f if l.strip()]
    assert _entries, "dream_log.jsonl is empty"
    _last = _entries[-1]
    assert "ts"           in _last, f"dream log entry missing 'ts': {_last}"
    assert "cycle_type"   in _last, f"dream log entry missing 'cycle_type': {_last}"
    assert "memory_written" in _last, f"dream log entry missing 'memory_written': {_last}"

    shutil.rmtree(_tmp)
    _restore()
    ok(f"AT-2: dream_log.jsonl written with valid entry: {list(_last.keys())}")
except AssertionError as e:
    _restore()
    fail("AT-2", e)
except Exception as e:
    _restore()
    fail("AT-2", e)


# ── AT-3: dream_faculty.run_dream() invoked (ran=True) ───────────────────────
try:
    _bs, _log, _tmp = _use_temp_blender(asleep=True)
    _exec_mod._BLENDER_STATE_PATH = _bs
    _exec_mod._DREAM_LOG_PATH     = _log

    _result3 = _exec_mod.run_dream_window(recent_topics=["elo", "book", "robot"])
    assert _result3.get("ran") is True, \
        f"dream faculty should have run (ran=True); got: {_result3}"

    shutil.rmtree(_tmp)
    _restore()
    ok(f"AT-3: dream_faculty.run_dream() invoked — ran=True, phase={_result3.get('phase')!r}")
except AssertionError as e:
    _restore()
    fail("AT-3", e)
except Exception as e:
    _restore()
    fail("AT-3", e)


# ── AT-4: creative_imagination (LOOP-8) still importable + callable ───────────
try:
    from faculties.creative.creative_imagination import diverge as _ci_diverge
    _candidates = _ci_diverge(goal="create", seeds=["test"], breadth_budget=1)
    assert isinstance(_candidates, list), f"diverge should return list, got {type(_candidates)}"
    ok(f"AT-4: creative_imagination.diverge() still callable (returned {len(_candidates)} candidates)")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: asleep=false → action="awake", ran=False ────────────────────────────
try:
    _bs, _log, _tmp = _use_temp_blender(asleep=False)
    _exec_mod._BLENDER_STATE_PATH = _bs
    _exec_mod._DREAM_LOG_PATH     = _log

    _result5 = _exec_mod.run_dream_window()
    assert _result5.get("action") == "awake", \
        f"action should be 'awake' when not asleep, got: {_result5.get('action')}"
    assert _result5.get("ran") is False, \
        f"ran should be False when not asleep, got: {_result5.get('ran')}"

    shutil.rmtree(_tmp)
    _restore()
    ok(f"AT-5: asleep=false → action='awake', ran=False (no dream cycle)")
except AssertionError as e:
    _restore()
    fail("AT-5", e)
except Exception as e:
    _restore()
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_compile.compile(os.path.join(_ROOT, "runtime/executive.py"), doraise=True)
    ok("AT-6: py_compile clean on executive.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-DREAM-STATE   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
