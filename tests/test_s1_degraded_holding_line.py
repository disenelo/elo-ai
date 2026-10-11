"""
S1-DEGRADED-HOLDING-LINE — acceptance tests

AT-0: _bh_degraded block does NOT replace mock response (pass, not stall line)
AT-1: _condition_outbound empty-response guard fires — logs warning, returns fallback
AT-2: _condition_outbound passes non-empty response unchanged
AT-3: _condition_outbound passes error-mode result unchanged (even if response is "")
AT-4: empty mock response on degraded turn is caught at outbound gate
"""

import sys
import os
import types
import importlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def check(label, cond):
    global PASS, FAIL
    if cond:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}")
        FAIL += 1


# ── AT-0: degraded block in server.py is now `pass` ─────────────────────────
def test_at0_degraded_block_is_pass():
    """The stall-line replacement must not exist in the degraded block."""
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "server.py"), encoding="utf-8") as f:
        src = f.read()
    # Find the _bh_degraded block
    idx = src.find("if _bh_degraded and _agent is None:")
    check("AT-0: _bh_degraded block exists", idx != -1)
    if idx == -1:
        return
    # The next non-blank line after the if should be `pass`, not `response = _bh_rand`
    block = src[idx:idx+600]
    check("AT-0: stall-line assignment NOT present in degraded block",
          "response = _bh_rand" not in block[:600])
    check("AT-0: `pass` present in degraded block",
          "\n                    pass" in block[:600] or "    pass" in block[:600])


# ── AT-1 / AT-2 / AT-3: _condition_outbound guard ───────────────────────────
def _make_result(response="", mode="direct", backend="mock"):
    return {"response": response, "mode": mode, "backend": backend,
            "inner_thought": "", "elo_final": ""}

def _load_condition_outbound():
    """
    Extract _condition_outbound from server.py by executing only the
    function definition in a minimal namespace.
    """
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "server.py"), encoding="utf-8") as f:
        src = f.read()
    # Find the function
    fn_start = src.find("def _condition_outbound(result):")
    fn_end   = src.find("\ndef _watch_parent(", fn_start)
    fn_src   = src[fn_start:fn_end]
    ns = {}
    try:
        exec(compile(fn_src, "<condition_outbound>", "exec"), ns)
    except Exception:
        pass
    return ns.get("_condition_outbound")

_cond = _load_condition_outbound()

def test_at1_empty_response_gets_fallback():
    if _cond is None:
        check("AT-1: _condition_outbound loaded", False)
        return
    result = _make_result(response="", mode="direct")
    out = _cond(result)
    check("AT-1: empty response replaced with fallback",
          bool((out.get("response") or "").strip()))

def test_at2_nonempty_response_unchanged():
    if _cond is None:
        check("AT-2: _condition_outbound loaded", False)
        return
    msg = "That grew out of something real."
    result = _make_result(response=msg, mode="direct")
    out = _cond(result)
    check("AT-2: non-empty response passes through (contains original)",
          msg in (out.get("response") or ""))

def test_at3_error_mode_not_patched():
    if _cond is None:
        check("AT-3: _condition_outbound loaded", False)
        return
    result = _make_result(response="", mode="error")
    out = _cond(result)
    # error-mode empty response must NOT be replaced with fallback text
    check("AT-3: error-mode empty response not patched",
          not (out.get("response") or "").strip())

def test_at4_whitespace_only_response_gets_fallback():
    if _cond is None:
        check("AT-4: _condition_outbound loaded", False)
        return
    result = _make_result(response="   \n  ", mode="direct")
    out = _cond(result)
    check("AT-4: whitespace-only response replaced with fallback",
          bool((out.get("response") or "").strip()))


if __name__ == "__main__":
    print("S1-DEGRADED-HOLDING-LINE tests")
    test_at0_degraded_block_is_pass()
    test_at1_empty_response_gets_fallback()
    test_at2_nonempty_response_unchanged()
    test_at3_error_mode_not_patched()
    test_at4_whitespace_only_response_gets_fallback()
    print(f"\nS1-DEGRADED  {PASS} passed  {FAIL} failed")
    sys.exit(0 if FAIL == 0 else 1)
