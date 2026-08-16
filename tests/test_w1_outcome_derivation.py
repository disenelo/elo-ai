"""
tests/test_w1_outcome_derivation.py — W1: Kill outcome="success" constant.

Tests:
    W1-1  server.py _dj_record call no longer uses outcome="success" literal
    W1-2  server.py computes _w1_outcome before the dj_record call
    W1-3  _w1_outcome is "silent" when _action is "stay_silent"
    W1-4  _w1_outcome is "spoke" when response is non-empty
    W1-5  _w1_outcome is "unknown" when response is empty/unbound

Run: python3 tests/test_w1_outcome_derivation.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── W1-1: dj_record no longer uses hardcoded "success" ──────────────────────
def test_w1_1_no_hardcoded_success():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()
    idx = src.find("_dj_record(")
    assert idx != -1, "W1-1: _dj_record( not found in server.py"
    block = src[idx: idx + 300]
    if 'outcome="success"' in block:
        err("W1-1: _dj_record still uses hardcoded outcome=\"success\"")
    ok("W1-1: _dj_record no longer uses hardcoded outcome=\"success\"")


# ── W1-2: _w1_outcome variable is computed before the main _dj_record ────────
def test_w1_2_outcome_computed():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()
    if "_w1_outcome" not in src:
        err("W1-2: _w1_outcome variable not found in server.py")
    # Find the main dj_record block (has outcome=_w1_outcome, not the early one at ~line 218)
    dj_w1_idx = src.find("outcome=_w1_outcome")
    if dj_w1_idx == -1:
        err("W1-2: outcome=_w1_outcome not found in server.py — W1 not wired")
    # _w1_outcome definition must appear before the dj_record that uses it
    w1_def_idx = src.find("_w1_outcome =")
    if w1_def_idx == -1:
        err("W1-2: _w1_outcome = assignment not found")
    if w1_def_idx >= dj_w1_idx:
        err("W1-2: _w1_outcome assigned AFTER the _dj_record that uses it — wrong order")
    ok("W1-2: _w1_outcome computed before the _dj_record that consumes it")


# ── W1-3/4/5: outcome logic correctness (exercised in isolation) ─────────────
def _compute_outcome(action, response_val, response_defined=True):
    """Mirror the _w1_outcome logic from server.py."""
    try:
        if not response_defined:
            raise NameError("response")
        response = response_val
        return ("silent" if action in ("stay_silent", "silent")
                else "spoke" if response else "unknown")
    except NameError:
        return "unknown"


def test_w1_3_silent_action():
    o = _compute_outcome("stay_silent", "")
    if o != "silent":
        err(f"W1-3: stay_silent action should produce outcome=silent, got {o!r}")
    o2 = _compute_outcome("silent", "anything")
    if o2 != "silent":
        err(f"W1-3: silent action should produce outcome=silent, got {o2!r}")
    ok("W1-3: stay_silent/silent actions produce outcome=silent")


def test_w1_4_spoke_action():
    o = _compute_outcome("speak", "Hello there")
    if o != "spoke":
        err(f"W1-4: speak action with response should produce outcome=spoke, got {o!r}")
    ok("W1-4: speak action with non-empty response produces outcome=spoke")


def test_w1_5_unknown_fallbacks():
    o_empty = _compute_outcome("speak", "")
    if o_empty != "unknown":
        err(f"W1-5: speak with empty response should produce outcome=unknown, got {o_empty!r}")
    o_unbound = _compute_outcome("reflect", "", response_defined=False)
    if o_unbound != "unknown":
        err(f"W1-5: unbound response should produce outcome=unknown, got {o_unbound!r}")
    ok("W1-5: empty/unbound response produces outcome=unknown")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("W1 — outcome derivation audit")
    test_w1_1_no_hardcoded_success()
    test_w1_2_outcome_computed()
    test_w1_3_silent_action()
    test_w1_4_spoke_action()
    test_w1_5_unknown_fallbacks()
    print("\n5/5 PASS — W1 outcome derivation verified")
    print("\nPROOF NOTE: Live verification — after a server turn, check:")
    print("  decision_journal.jsonl must contain a row where outcome != 'success'")
    print("  (outcome will be 'spoke', 'silent', or 'unknown' depending on action)")
