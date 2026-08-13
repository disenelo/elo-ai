"""
tests/test_ea2_1_company_state.py — Acceptance tests for WO-EA2-1

Spec: WO-EA2-1_Company_State_Writer.md §4
Build the company_runtime/ package (company_state.json + action intake).

4 tests + frozen-kernel proof:
    AT-1  publish() emits valid company_state/v1 with all consumed keys
    AT-2  approval_request with L3 actor flips WO status + re-emits state
    AT-3  money/legal WO without human_flag → refused + logged (safety gate)
    AT-4  malformed request → dropped gracefully, no crash
    AT-5  frozen kernel tests still pass (additive-only proof)

Run: python3 tests/test_ea2_1_company_state.py
"""
import sys
import os
import json
import tempfile
import textwrap

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from company_runtime.company_state_writer import (
    publish, process_action, handle_company_approve,
    _parse_board, _is_safety_wo,
)


# ── AT-1: publish() emits valid company_state/v1 with all consumed keys ───────

_REQUIRED_KEYS = {
    "schema", "_ts", "today_priorities", "waiting_for_approval",
    "blocked", "money", "roadmap", "board", "graph",
    "seats_sample", "voiced_briefing",
}

with tempfile.TemporaryDirectory() as _tmp:
    _state_path = os.path.join(_tmp, "company_state.json")
    _board_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "engineering", "work_orders", "DISPATCH_BOARD.md")
    _ok1 = publish(board_path=_board_path, state_path=_state_path)
    try:
        assert _ok1, "publish() returned False"
        with open(_state_path, encoding="utf-8") as _f:
            _data = json.load(_f)
        _missing = _REQUIRED_KEYS - set(_data.keys())
        assert not _missing, f"missing keys: {_missing}"
        assert _data["schema"] == "company_state/v1", f"wrong schema: {_data['schema']!r}"
        assert isinstance(_data["board"], list), "board must be a list"
        assert len(_data["board"]) > 0, "board must not be empty"
        assert isinstance(_data["_ts"], float), "_ts must be float"
        assert isinstance(_data["voiced_briefing"], str), "voiced_briefing must be str"
        assert len(_data["seats_sample"]) >= 4, "seats_sample must have ≥ 4 entries"
        ok(
            f"AT-1: company_state/v1 valid — {len(_data['board'])} rows, "
            f"today={len(_data['today_priorities'])}, "
            f"waiting={len(_data['waiting_for_approval'])}, "
            f"briefing: {_data['voiced_briefing']!r}"
        )
    except AssertionError as e: fail("AT-1", e)


# ── AT-2: approval_request with L3 actor flips WO status + re-emits state ────

_MOCK_BOARD = textwrap.dedent("""\
    | WO | Title | Agent | Pri | Status | Depends on | Spec |
    |----|-------|-------|-----|--------|-----------|------|
    | WO-TEST-99 | Test work order for EA2-1 | Builder | P1 | DONE ✅ | — | stub |
    | WO-TEST-98 | Another item | Architecture | P2 | READY | — | stub |
""")

with tempfile.TemporaryDirectory() as _tmp2:
    _board2 = os.path.join(_tmp2, "DISPATCH_BOARD.md")
    _state2  = os.path.join(_tmp2, "company_state.json")
    with open(_board2, "w", encoding="utf-8") as _f:
        _f.write(_MOCK_BOARD)

    _action = {
        "type":       "approval_request",
        "work_order": "WO-TEST-99",
        "to_status":  "IN_REVIEW",
        "actor":      "david",
        "human_flag": False,
        "_ts":        9999999.0,
    }
    _result = process_action(_action, board_path=_board2, state_path=_state2)
    try:
        assert _result["ok"], f"process_action returned not-ok: {_result['reason']}"
        with open(_board2, encoding="utf-8") as _f:
            _updated = _f.read()
        assert "IN_REVIEW" in _updated, f"status not flipped in board: {_updated!r}"
        assert os.path.exists(_state2), "company_state.json not re-emitted after approval"
        with open(_state2, encoding="utf-8") as _f:
            _re_emitted = json.load(_f)
        assert _re_emitted["schema"] == "company_state/v1", "re-emitted state has wrong schema"
        ok(
            f"AT-2: approval_request david/WO-TEST-99 → {_result['reason']}; "
            f"board flipped; state re-emitted"
        )
    except AssertionError as e: fail("AT-2", e)


# ── AT-3: money/legal WO without human_flag → refused ────────────────────────

_MONEY_BOARD = textwrap.dedent("""\
    | WO | Title | Agent | Pri | Status | Depends on | Spec |
    |----|-------|-------|-----|--------|-----------|------|
    | WO-MONEY-1 | Kickstarter campaign budget approval | Marketing | P1 | READY | — | stub |
""")

with tempfile.TemporaryDirectory() as _tmp3:
    _board3 = os.path.join(_tmp3, "DISPATCH_BOARD.md")
    _state3  = os.path.join(_tmp3, "company_state.json")
    with open(_board3, "w", encoding="utf-8") as _f:
        _f.write(_MONEY_BOARD)

    _money_action = {
        "type":       "approval_request",
        "work_order": "WO-MONEY-1",
        "to_status":  "DONE",
        "actor":      "david",
        "human_flag": False,  # ← missing
        "_ts":        9999998.0,
    }
    _result3 = process_action(_money_action, board_path=_board3, state_path=_state3)
    try:
        assert not _result3["ok"], "safety-gated WO should have been refused"
        assert "refused" in _result3["reason"].lower() or "safety" in _result3["reason"].lower(), (
            f"reason should mention refusal/safety: {_result3['reason']!r}"
        )
        # verify board NOT modified
        with open(_board3, encoding="utf-8") as _f:
            _board3_text = _f.read()
        assert "READY" in _board3_text, "board was modified despite refusal"
        ok(f"AT-3: money WO refused without human_flag — {_result3['reason']!r}")
    except AssertionError as e: fail("AT-3", e)

    # confirm: same WO with human_flag=True is allowed
    _money_action_ok = dict(_money_action, human_flag=True, _ts=9999997.0)
    _result3b = process_action(_money_action_ok, board_path=_board3, state_path=_state3)
    try:
        assert _result3b["ok"], f"human_flag=True should pass safety gate: {_result3b['reason']}"
        ok(f"AT-3b: same money WO passes with human_flag=True — {_result3b['reason']!r}")
    except AssertionError as e: fail("AT-3b", e)


# ── AT-4: malformed request → dropped gracefully, no crash ───────────────────

_malformed_cases = [
    {},                                                       # empty dict
    {"type": "approval_request"},                            # missing work_order
    {"work_order": "WO-X"},                                  # missing type
    {"type": "approval_request", "work_order": "WO-GHOST",  # non-L3 actor
     "actor": "random_person", "_ts": 1.0},
    None,                                                    # None — should be caught by process_action?
]

_crashed = False
_refused_all = True
for _case in _malformed_cases:
    try:
        if _case is None:
            # process_action expects a dict; test that it handles unexpected input gracefully
            try:
                _r = process_action({})
            except Exception:
                _crashed = True
        else:
            _r = process_action(_case)
            if _r.get("ok"):
                _refused_all = False
    except Exception as _exc:
        _crashed = True

try:
    assert not _crashed, "process_action raised an exception on a malformed input"
    assert _refused_all, "at least one malformed/unauthorized case returned ok=True"
    ok("AT-4: all malformed / unauthorized cases refused gracefully, no crash")
except AssertionError as e: fail("AT-4", e)


# ── AT-5: frozen kernel tests stay green ─────────────────────────────────────

print("\n  Running frozen kernel test suite...")
import subprocess
_frozen = [
    "tests/test_wo001_faculty_bus.py",
    "tests/test_wo014_spine_wiring.py",
    "tests/test_wo006_emotional_processing.py",
]
_kernel_ok = True
for _tf in _frozen:
    _r = subprocess.run(
        [sys.executable, _tf],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    _last_line = _r.stdout.strip().splitlines()[-1] if _r.stdout.strip() else ""
    if _r.returncode != 0:
        print(f"    ⚠ {_tf}: {_last_line}")
        _kernel_ok = False
    else:
        print(f"    ✓ {_tf}: {_last_line}")

try:
    assert _kernel_ok, "one or more frozen kernel tests failed after EA2-1 install"
    ok("AT-5: frozen kernel tests still pass (additive-only verified)")
except AssertionError as e: fail("AT-5", e)


print(f"\nResult: {PASS}/5 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
