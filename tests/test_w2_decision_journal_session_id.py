"""
tests/test_w2_decision_journal_session_id.py — Card 0040 §W2 step-4 acceptance.

Card 0040:
    "One session id per process start, stable for its life, monotonic, stored.
     Not os.getpid(). Not str(time.time()) per call."

    Live acceptance (unreachable in one seat run — depends on hours of live
    operation across two process starts): "Two lessons confirm from genuinely
    distinct sessions — different session_id, hours apart, both verified: true."

This test verifies the IMPLEMENTATION CONTRACT that makes the live acceptance
reachable. Four checks:

    W2-DJ-1  decision_journal.record() writes a session_id field on every row.
    W2-DJ-2  Two record() calls in the same process share the same session_id.
    W2-DJ-3  A fresh subprocess allocates a STRICTLY GREATER session_id.
    W2-DJ-4  reflection_faculty._SESSION_ID matches decision_journal._SESSION_ID
             (a decision row and any lesson evidence it produces share one id).

Run: python3 tests/test_w2_decision_journal_session_id.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


def _read_last_row(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    if not lines:
        err(f"expected at least one row in {path}, found none")
    return json.loads(lines[-1])


def test_w2_dj_1_session_id_written(tmp_journal: str) -> str:
    """record() writes a session_id field."""
    from self import decision_journal as dj
    dj._JOURNAL = tmp_journal  # redirect journal writes to the tmp file
    dj.record(
        turn="hello world",
        action="conversation",
        exec_decision={"cal_reason": "test"},
        backend="mock",
        outcome="spoke",
    )
    row = _read_last_row(tmp_journal)
    sid = row.get("session_id")
    if not sid:
        err("W2-DJ-1: decision_journal.record() wrote no session_id field")
    if not isinstance(sid, str):
        err(f"W2-DJ-1: session_id is not a string (got {type(sid).__name__})")
    # card 0082 F-2: format is now "S{n}" — NOT pure-numeric (required by D1 gate).
    # promote_pass() counts distinct_sessions by comparing the full string, not int-parsing.
    if not (sid.startswith("S") and sid[1:].isdigit()):
        err(f"W2-DJ-1: session_id={sid!r} does not match 'S{{n}}' format (card 0082 F-2)")
    if len(sid[1:]) < 9:
        err(f"W2-DJ-1: session_id={sid!r} numeric part shorter than 9 digits — not a real unix epoch")
    ok(f"W2-DJ-1: decision_journal.record() writes session_id={sid!r}")
    return sid


def test_w2_dj_2_stable_within_process(tmp_journal: str, first_sid: str) -> None:
    """Two record() calls in the same process share the same session_id."""
    from self import decision_journal as dj
    dj.record(
        turn="another turn",
        action="conversation",
        exec_decision={"cal_reason": "test-2"},
        backend="mock",
        outcome="spoke",
    )
    row = _read_last_row(tmp_journal)
    sid = row.get("session_id")
    if sid != first_sid:
        err(f"W2-DJ-2: session_id drifted within one process ({first_sid!r} → {sid!r})")
    ok(f"W2-DJ-2: session_id stable across two record() calls ({sid!r})")


def test_w2_dj_3_subprocess_is_monotonic(first_sid: str) -> None:
    """A fresh subprocess allocates a strictly greater session_id."""
    script = (
        "import sys; sys.path.insert(0, %r)\n"
        "from runtime.session_id import SESSION_ID\n"
        "print(SESSION_ID)\n"
    ) % ROOT
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True,
    )
    fresh_sid = result.stdout.strip()
    # card 0082 F-2: format is "S{n}" — check prefix then compare numeric parts
    if not (fresh_sid.startswith("S") and fresh_sid[1:].isdigit()):
        err(f"W2-DJ-3: subprocess produced unexpected session_id format={fresh_sid!r}")
    if int(fresh_sid[1:]) <= int(first_sid[1:]):
        err(f"W2-DJ-3: subprocess session_id={fresh_sid} not strictly greater than "
            f"parent {first_sid} — monotonicity broken")
    ok(f"W2-DJ-3: subprocess session_id={fresh_sid} > parent {first_sid} — monotonic")


def test_w2_dj_4_shared_with_reflection() -> None:
    """decision_journal and reflection_faculty share a single session id."""
    from self import decision_journal as dj
    from runtime import reflection_faculty as rf
    if dj._SESSION_ID != rf._SESSION_ID:
        err(f"W2-DJ-4: decision_journal._SESSION_ID={dj._SESSION_ID!r} != "
            f"reflection_faculty._SESSION_ID={rf._SESSION_ID!r} — "
            "a turn's decision row and its lesson evidence will not share a session")
    ok(f"W2-DJ-4: decision_journal + reflection_faculty share session_id={dj._SESSION_ID!r}")


if __name__ == "__main__":
    print("W2 — decision_journal session_id (card 0040 §W2 step-4)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_journal = os.path.join(tmp, "decision_journal.jsonl")
        first_sid = test_w2_dj_1_session_id_written(tmp_journal)
        test_w2_dj_2_stable_within_process(tmp_journal, first_sid)
        test_w2_dj_3_subprocess_is_monotonic(first_sid)
        test_w2_dj_4_shared_with_reflection()
    print("\n4/4 PASS — W2 session_id wired into decision_journal + reflection_faculty")
    print("\nLIVE ACCEPTANCE (card 0040): reachable but not one-shot verifiable —")
    print("  requires two lessons confirming with distinct session_ids, hours apart.")
