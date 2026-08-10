"""
tests/test_wo082_decision_journal.py — WO-082: Executive Decision Journal

Tests that eLo records a real decision trace per executive action and can
explain it back on demand — never fabricating a motive.

  AT-0: py_compile clean on server.py
  AT-1: record() appends a valid JSONL entry with expected fields
  AT-2: last_n() returns the last N entries correctly (ordering)
  AT-3: record_failure() writes known_failure_condition + drops reliability
  AT-4: get_reliability() starts at 1.0, drops 0.15 per failure, floors at 0.0
  AT-5: explain_last() returns a string mentioning action + trigger (no fabrication)
  AT-6: WO-082 marker + _WHY_TRACE_TRIGGERS wired in server.py

Run: python3 tests/test_wo082_decision_journal.py
"""
from __future__ import annotations
import sys, os, json, py_compile, tempfile, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── Patch journal + reliability paths to a temp dir for isolation ─────────────
_tmp_dir = tempfile.mkdtemp(prefix="wo082_test_")
_journals_dir = os.path.join(_tmp_dir, "journals")
os.makedirs(_journals_dir, exist_ok=True)

import self.decision_journal as _dj

_orig_journal     = _dj._JOURNAL
_orig_reliability = _dj._RELIABILITY
_dj._JOURNAL      = os.path.join(_journals_dir, "decision_journal.jsonl")
_dj._RELIABILITY  = os.path.join(_journals_dir, "action_reliability.json")


def _reset():
    """Clear journal + reliability between tests."""
    for p in (_dj._JOURNAL, _dj._RELIABILITY):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass


# ── AT-0: py_compile clean on server.py ──────────────────────────────────────
try:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_compile.compile(os.path.join(_base, "server.py"), doraise=True)
    ok("AT-0: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: record() appends a valid entry with expected fields ─────────────────
try:
    _reset()
    _dj.record(
        turn="Hey eLo what's happening",
        action="celebrate",
        exec_decision={
            "cal_reason": "how are you",
            "intent":     "connection",
            "tone":       "CHILDLIKE-WISE",
            "confidence": 0.85,
        },
        backend="openai",
        outcome="success",
    )
    with open(_dj._JOURNAL, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 1, f"expected 1 entry, got {len(lines)}"
    entry = json.loads(lines[0])
    assert entry["action"]  == "celebrate",       f"action mismatch: {entry['action']}"
    assert entry["trigger"] == "how are you",     f"trigger mismatch: {entry['trigger']}"
    assert entry["intent"]  == "connection",      f"intent mismatch: {entry['intent']}"
    assert entry["outcome"] == "success",         f"outcome mismatch: {entry['outcome']}"
    assert entry["backend"] == "openai",          f"backend mismatch: {entry['backend']}"
    assert "ts" in entry,                         "ts missing"
    assert "alternatives_rejected" in entry,      "alternatives_rejected missing"
    ok("AT-1: record() appends valid JSONL entry with correct fields")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: last_n() returns last N entries (oldest first, capped at N) ─────────
try:
    _reset()
    for i in range(5):
        _dj.record(
            turn=f"turn {i}",
            action=f"action_{i}",
            exec_decision={"cal_reason": f"reason_{i}"},
            backend="mock",
        )
    result = _dj.last_n(3)
    assert len(result) == 3, f"expected 3 entries, got {len(result)}"
    assert result[0]["action"] == "action_2", f"oldest of last-3 wrong: {result[0]['action']}"
    assert result[1]["action"] == "action_3", f"middle wrong: {result[1]['action']}"
    assert result[2]["action"] == "action_4", f"newest wrong: {result[2]['action']}"
    ok("AT-2: last_n() returns correct N entries oldest-first")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: record_failure() writes known_failure_condition entry ───────────────
try:
    _reset()
    _dj.record_failure("answer", "backend timed out after 10s")
    with open(_dj._JOURNAL, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 1, f"expected 1 failure entry, got {len(lines)}"
    entry = json.loads(lines[0])
    assert entry["outcome"] == "failure",                        "outcome not failure"
    assert entry["known_failure_condition"] == "backend timed out after 10s", \
        f"condition mismatch: {entry.get('known_failure_condition')}"
    assert "learning" in entry and "avoid" in entry["learning"], \
        f"learning field missing or wrong: {entry.get('learning')}"
    ok("AT-3: record_failure() writes known_failure_condition entry correctly")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: reliability drops 0.15 per failure, floors at 0.0 ──────────────────
try:
    _reset()
    assert _dj.get_reliability("answer") == 1.0, "baseline should be 1.0"
    _dj.record_failure("answer", "first fail")
    r1 = _dj.get_reliability("answer")
    assert abs(r1 - 0.85) < 0.001, f"after 1 failure expected 0.85, got {r1}"
    _dj.record_failure("answer", "second fail")
    r2 = _dj.get_reliability("answer")
    assert abs(r2 - 0.70) < 0.001, f"after 2 failures expected 0.70, got {r2}"
    # Floor test — 7 more failures should not go below 0.0
    for _ in range(7):
        _dj.record_failure("answer", "repeated fail")
    r_floor = _dj.get_reliability("answer")
    assert r_floor >= 0.0, f"reliability went negative: {r_floor}"
    ok("AT-4: reliability drops 0.15/failure, floors at 0.0")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: explain_last() references action + trigger, not invented motive ─────
try:
    _reset()
    _dj.record(
        turn="play something calm",
        action="answer",
        exec_decision={
            "cal_reason":       "music request",
            "intent":           "creativity",
            "tone":             "CALM",
            "original_action":  "reflect",
            "reason":           "direct command override",
            "overridden_by_routing": True,
        },
        backend="spotify_direct",
        outcome="success",
    )
    explanation = _dj.explain_last()
    assert isinstance(explanation, str),          "explain_last() must return str"
    assert "answer" in explanation,               f"action not in explanation: {explanation}"
    assert "music request" in explanation,        f"trigger not in explanation: {explanation}"
    assert "reflect" in explanation,              f"rejected alternative not mentioned: {explanation}"
    ok("AT-5: explain_last() returns trace-grounded explanation (action + trigger + alternative)")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: WO-082 marker + _WHY_TRACE_TRIGGERS in server.py ───────────────────
try:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(_base, "server.py"), encoding="utf-8") as _f:
        _src = _f.read()
    assert "WO-082"              in _src, "WO-082 marker not found in server.py"
    assert "_WHY_TRACE_TRIGGERS" in _src, "_WHY_TRACE_TRIGGERS not found in server.py"
    assert "decision_journal"    in _src, "decision_journal import not found in server.py"
    assert "explain_last"        in _src, "explain_last not wired in server.py"
    assert "_dj_record"          in _src, "_dj_record call not found in server.py"
    ok("AT-6: WO-082 marker + all journal hooks wired in server.py")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── Cleanup ───────────────────────────────────────────────────────────────────
_dj._JOURNAL      = _orig_journal
_dj._RELIABILITY  = _orig_reliability
shutil.rmtree(_tmp_dir, ignore_errors=True)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-082 decision journal   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
