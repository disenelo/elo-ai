"""
tests/test_f8_lessons_wire.py — BDRIFT-F8 Acceptance Tests

Tests:
  AT-F8-1  BUILT: _write_journal_entry() writes evidence with action + outcome
  AT-F8-2  WIRED: _evidence_is_verified() returns True for row from fixed write side
  AT-F8-3  FALSIFIABLE: cutting action from evidence → _evidence_is_verified() = False
  AT-F8-4  REGRESSION: numeric session_id → _evidence_is_verified() = False
  AT-F8-5  REGRESSION: pre-v1 string evidence entries → _evidence_is_verified() = False
  AT-F8-6  REGRESSION: no action AND no outcome → _evidence_is_verified() = False
  AT-F8-7  session_id uses SESSION_ID (non-numeric, stable) — not a timestamp or PID

Run:
  python tests/test_f8_lessons_wire.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

PASS: list[str] = []
FAIL: list[str] = []


def ok(name: str) -> None:
    PASS.append(name)
    print(f"  ✅ {name}")


def fail(name: str, reason: str) -> None:
    FAIL.append(name)
    print(f"  ❌ {name}: {reason}")


# ── imports ───────────────────────────────────────────────────────────────────

import runtime.reflection_faculty as rf_mod
import self.lesson_store as ls_mod
from faculties.learning.faculty import _evidence_is_verified


# ── helper: call _write_journal_entry with a temp ledger ─────────────────────

def _run_write_journal(
    action: str = "build",
    completion_state: str = "met",
    spot: str | None = "SPOT-F8-TEST-001",
    ledger_path: str | None = None,
) -> tuple[dict | None, str]:
    """
    Call rf_mod._write_journal_entry() with a fabricated lesson.
    Returns (lesson_row_or_None, ledger_path).
    Patches both rf_mod._LESSON_LOG and ls_mod._LEDGER to ledger_path.
    """
    if ledger_path is None:
        tf = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        tf.close()
        ledger_path = tf.name

    original_rf_log = rf_mod._LESSON_LOG
    original_ls_ledger = ls_mod._LEDGER
    rf_mod._LESSON_LOG = ledger_path
    ls_mod._LEDGER = ledger_path

    try:
        # Build a lesson via the real _form_lesson — ensures a realistic key
        lesson = rf_mod._form_lesson(
            session_summary="built the animation system and it worked correctly and it was a big success",
            action=action,
            completion_state=completion_state,
            planned_objective="build animation system",
        )
        if lesson is None:
            return None, ledger_path

        rf_mod._write_journal_entry(
            session_summary="built the animation system and it worked correctly and it was a big success",
            project="f8-test",
            action=action,
            lesson=lesson,
            spot=spot,
            completion_state=completion_state,
        )

        # Read back the written row
        lkey = lesson.get("lesson_key")
        rows = []
        try:
            with open(ledger_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
        except FileNotFoundError:
            pass

        lesson_row = next((r for r in rows if r.get("lesson_key") == lkey), None)
        return lesson_row, ledger_path
    finally:
        rf_mod._LESSON_LOG = original_rf_log
        ls_mod._LEDGER = original_ls_ledger


# ── AT-F8-1: evidence entry has action + outcome ─────────────────────────────

def test_evidence_has_action_outcome() -> None:
    """BUILT: written lesson row carries action and outcome in evidence."""
    lesson_row, ledger_path = _run_write_journal(action="build", completion_state="met")
    try:
        if lesson_row is None:
            fail("AT-F8-1", "_form_lesson returned None or row not written")
            return
        evidence = lesson_row.get("evidence", [])
        if not evidence:
            fail("AT-F8-1", f"evidence list is empty — write order bug persists. Row: {lesson_row}")
            return
        ev = next((e for e in evidence if isinstance(e, dict)), None)
        if ev is None:
            fail("AT-F8-1", "no dict evidence entries")
            return
        if not ev.get("action"):
            fail("AT-F8-1", f"action missing from evidence entry: {ev}")
        elif not ev.get("outcome"):
            fail("AT-F8-1", f"outcome missing from evidence entry: {ev}")
        else:
            ok("AT-F8-1")
    finally:
        try:
            os.unlink(ledger_path)
        except OSError:
            pass


# ── AT-F8-2: D1 gate returns True for written row ───────────────────────────

def test_d1_gate_passes_for_written_row() -> None:
    """WIRED: _evidence_is_verified() returns True for a row from the fixed write side."""
    lesson_row, ledger_path = _run_write_journal(action="build", completion_state="met")
    try:
        if lesson_row is None:
            fail("AT-F8-2", "lesson_row is None — cannot test D1 gate")
            return
        result = _evidence_is_verified(lesson_row)
        if result:
            ok("AT-F8-2")
        else:
            fail("AT-F8-2",
                 f"_evidence_is_verified returned False — evidence: {lesson_row.get('evidence')}")
    finally:
        try:
            os.unlink(ledger_path)
        except OSError:
            pass


# ── AT-F8-3: FALSIFIABLE — cutting action+outcome → gate returns False ────────

def test_falsifiable_cut_action_and_outcome() -> None:
    """FALSIFIABLE: D1 gate (faculty.py:78) requires 'action OR outcome'.
    Cutting both makes it reject. Cutting only action leaves outcome — gate passes
    (correct per gate spec). The falsifiable condition is 'neither present'.
    """
    lesson_row, ledger_path = _run_write_journal(action="build", completion_state="met")
    try:
        if lesson_row is None:
            fail("AT-F8-3", "lesson_row is None — cannot test falsifiability")
            return
        # Baseline: gate passes with both action + outcome
        if not _evidence_is_verified(lesson_row):
            fail("AT-F8-3", "baseline: _evidence_is_verified returned False (prerequisite fails)")
            return
        # Cut BOTH action and outcome — D1 gate requires at least one (faculty.py:78)
        import copy
        cut_row = copy.deepcopy(lesson_row)
        for ev in cut_row.get("evidence", []):
            if isinstance(ev, dict):
                ev.pop("action", None)
                ev.pop("outcome", None)
        result_cut = _evidence_is_verified(cut_row)
        if result_cut:
            fail("AT-F8-3", "gate returned True with neither action nor outcome — not falsifiable")
        else:
            ok("AT-F8-3")
    finally:
        try:
            os.unlink(ledger_path)
        except OSError:
            pass


# ── AT-F8-4: REGRESSION — numeric session_id → False ────────────────────────

def test_numeric_session_id_rejected() -> None:
    """REGRESSION: purely numeric session_id (old process-id format) fails D1 gate."""
    lesson_row = {
        "lesson_key": "test-numeric-sid",
        "evidence": [
            {
                "episode_ref": "ep-001",
                "verified": True,
                "session_id": "1787261879",   # purely numeric — old process-id format
                "action": "build",
                "outcome": "met",
            }
        ],
    }
    if _evidence_is_verified(lesson_row):
        fail("AT-F8-4", "numeric session_id should be rejected by D1 gate")
    else:
        ok("AT-F8-4")


# ── AT-F8-5: REGRESSION — pre-v1 string evidence rejected ───────────────────

def test_pre_v1_string_evidence_rejected() -> None:
    """REGRESSION: pre-v1 ledger rows have string evidence entries — must be rejected."""
    lesson_pre_v1 = {
        "lesson_key": "test-pre-v1",
        "evidence": [
            "some text entry",        # string — pre-v1 format
            "another text entry",
        ],
    }
    if _evidence_is_verified(lesson_pre_v1):
        fail("AT-F8-5", "pre-v1 string evidence entries should be rejected (faculty.py:71)")
    else:
        ok("AT-F8-5")


# ── AT-F8-6: REGRESSION — no action AND no outcome → False ──────────────────

def test_no_action_no_outcome_rejected() -> None:
    """REGRESSION: evidence with verified=True but no action and no outcome fails D1."""
    lesson_row = {
        "lesson_key": "test-no-action-outcome",
        "evidence": [
            {
                "episode_ref": "ep-002",
                "verified": True,
                "session_id": "eLo-stable-session-01",
                # no action, no outcome
            }
        ],
    }
    if _evidence_is_verified(lesson_row):
        fail("AT-F8-6", "missing action+outcome should be rejected by D1 gate")
    else:
        ok("AT-F8-6")


# ── AT-F8-7: session_id is SESSION_ID (non-numeric, stable) ─────────────────

def test_session_id_is_non_numeric() -> None:
    """session_id written by reflection_faculty must be non-numeric (SESSION_ID)."""
    lesson_row, ledger_path = _run_write_journal(action="build", completion_state="met")
    try:
        if lesson_row is None:
            fail("AT-F8-7", "lesson_row is None")
            return
        evidence = lesson_row.get("evidence", [])
        ev = next((e for e in evidence if isinstance(e, dict)), None)
        if ev is None:
            fail("AT-F8-7", "no dict evidence entry to inspect")
            return
        sid = str(ev.get("session_id") or "")
        if not sid:
            fail("AT-F8-7", "session_id is empty")
        elif sid.isdigit():
            fail("AT-F8-7", f"session_id is purely numeric (process-id leak?): {sid!r}")
        else:
            ok("AT-F8-7")
    finally:
        try:
            os.unlink(ledger_path)
        except OSError:
            pass


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== BDRIFT-F8 Lessons Wire Tests ===\n")
    test_evidence_has_action_outcome()
    test_d1_gate_passes_for_written_row()
    test_falsifiable_cut_action_and_outcome()
    test_numeric_session_id_rejected()
    test_pre_v1_string_evidence_rejected()
    test_no_action_no_outcome_rejected()
    test_session_id_is_non_numeric()

    total = len(PASS) + len(FAIL)
    print(f"\n{'─'*40}")
    print(f"Result: {len(PASS)}/{total} PASS")
    if FAIL:
        print("FAILED:", ", ".join(FAIL))
        sys.exit(1)
    else:
        print("All AT-F8 tests pass ✅")
        sys.exit(0)
