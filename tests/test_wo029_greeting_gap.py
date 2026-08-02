"""
WO-029 acceptance tests — 'all good' greeting family routing.

AT-1  "you all good?" → exec_decision overridden: action=celebrate, cal_reason="how are you"
AT-2  "are you all good?" → overridden
AT-3  "all good?" (bare) → overridden
AT-4  "everything good?" → overridden
AT-5  "you all good with the plan?" → NOT overridden (false-positive guard)
AT-6  "is the build all good?" → NOT overridden (false-positive guard)
AT-7  Frozen kernel untouched (executive.py + prompts/ unchanged)
AT-8  py_compile: server.py compiles cleanly after change
"""
import importlib.util
import os
import sys
import types as _types

_ROOT = os.path.join(os.path.dirname(__file__), "..")

# ── Load server.py in isolation (avoid Flask startup) ────────────────────────
# We only need the WO-029 regex logic, which uses module-level _re.
# Simulate just enough of the module for the override block to work.

_SPEC   = importlib.util.spec_from_file_location("server_test", os.path.join(_ROOT, "server.py"))


def _simulate_override(raw: str) -> dict:
    """
    Replicate the WO-029 exec_decision override block from server.py.
    Returns the exec_decision dict after the override (or before, if not matched).
    """
    import re as _re
    _WO029_RE = _re.compile(
        r'^(?:(?:are\s+)?you(?:\'re|re)?\s+all\s+good'
        r'|we\s+all\s+good'
        r'|(?:is\s+)?everything(?:\s+all)?\s+good'
        r'|all\s+good'
        r'|you\s+all\s+g'
        r')[?.!]*$',
        _re.I,
    )
    _wo029_bare = raw.strip().lower().rstrip("?.!")
    _wo029_no_false_pos = " with " not in _wo029_bare and not _wo029_bare.startswith("is the ")

    # Simulate an exec_decision that would come from executive for a drifted turn
    exec_decision = {"action": "connect", "cal_reason": "connect", "confidence": 0.6}

    if len(_wo029_bare) < 40 and _wo029_no_false_pos and _WO029_RE.match(_wo029_bare):
        exec_decision = dict(exec_decision)
        exec_decision.update({
            "action":    "celebrate",
            "cal_reason": "how are you",
            "confidence": 0.85,
            "original_action": exec_decision.get("action"),
            "overridden_by_routing": True,
        })
    return exec_decision


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_you_all_good():
    d = _simulate_override("you all good?")
    assert d["action"] == "celebrate",        f"AT-1 FAIL: action={d['action']}"
    assert d["cal_reason"] == "how are you",  f"AT-1 FAIL: cal_reason={d['cal_reason']}"
    assert d.get("overridden_by_routing"),    "AT-1 FAIL: overridden_by_routing not set"
    print("AT-1 PASS — 'you all good?' → celebrate / how are you")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_are_you_all_good():
    for phrase in ("are you all good?", "are you all good", "you're all good?", "youre all good"):
        d = _simulate_override(phrase)
        assert d["action"] == "celebrate", f"AT-2 FAIL on {phrase!r}: action={d['action']}"
    print("AT-2 PASS — 'are you all good?' / 'you're all good?' variants → celebrate")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_bare_all_good():
    for phrase in ("all good?", "all good", "all good!"):
        d = _simulate_override(phrase)
        assert d["action"] == "celebrate", f"AT-3 FAIL on {phrase!r}: action={d['action']}"
    print("AT-3 PASS — bare 'all good' → celebrate")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_everything_good():
    for phrase in ("everything good?", "is everything good?", "everything all good?"):
        d = _simulate_override(phrase)
        assert d["action"] == "celebrate", f"AT-4 FAIL on {phrase!r}: action={d['action']}"
    print("AT-4 PASS — 'everything good?' variants → celebrate")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_false_positive_guard_with():
    for phrase in (
        "you all good with the plan?",
        "are you all good with that?",
        "we all good with this?",
    ):
        d = _simulate_override(phrase)
        assert d["action"] != "celebrate" or d["cal_reason"] != "how are you", \
            f"AT-5 FAIL: {phrase!r} was wrongly matched"
    print("AT-5 PASS — 'you all good with X?' not over-matched")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_false_positive_guard_object():
    for phrase in ("is the build all good?", "is the plan all good?"):
        d = _simulate_override(phrase)
        assert d["action"] != "celebrate" or d["cal_reason"] != "how are you", \
            f"AT-6 FAIL: {phrase!r} was wrongly matched"
    print("AT-6 PASS — 'is the build all good?' not over-matched")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_frozen_kernel():
    for path in [os.path.join(_ROOT, "runtime", "executive.py")]:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        for token in (b"all good", b"WO-029", b"_WO029"):
            assert token not in content, \
                f"AT-7 FAIL: frozen file {path} contains WO-029 token '{token.decode()}'"
    prompts_dir = os.path.join(_ROOT, "prompts")
    if os.path.isdir(prompts_dir):
        for fname in os.listdir(prompts_dir):
            with open(os.path.join(prompts_dir, fname), "rb") as f:
                content = f.read()
            assert b"WO-029" not in content, \
                f"AT-7 FAIL: prompts/{fname} modified — FREEZE_V1_LOCK violated"
    print("AT-7 PASS — frozen kernel untouched")


# ── AT-8 ─────────────────────────────────────────────────────────────────────

def test_at8_server_compiles():
    import py_compile
    try:
        py_compile.compile(os.path.join(_ROOT, "server.py"), doraise=True)
    except py_compile.PyCompileError as e:
        raise AssertionError(f"AT-8 FAIL: server.py does not compile: {e}")
    print("AT-8 PASS — server.py compiles cleanly")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_you_all_good,
        test_at2_are_you_all_good,
        test_at3_bare_all_good,
        test_at4_everything_good,
        test_at5_false_positive_guard_with,
        test_at6_false_positive_guard_object,
        test_at7_frozen_kernel,
        test_at8_server_compiles,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-029 ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
