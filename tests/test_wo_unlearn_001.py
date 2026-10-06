"""WO-UNLEARN-001: tests for self_improvement/unlearn.py."""
import json
import os
import tempfile
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_lesson(lesson_id, lesson_key, statement, status="confirmed", strength=1.0, successes=3):
    evidence = [{"episode_ref": f"ep-{i}", "verified": True, "ts": 1700000000.0 + i,
                 "outcome": "complete"} for i in range(successes)]
    return {
        "id":          lesson_id,
        "lesson_key":  lesson_key,
        "statement":   statement,
        "evidence":    evidence,
        "scope":       "capability",
        "strength":    strength,
        "status":      status,
        "retired_at":  None,
        "reason":      None,
    }


def _write_ledger(path, lessons):
    with open(path, "w", encoding="utf-8") as f:
        for l in lessons:
            f.write(json.dumps(l) + "\n")


# ── Tests: flag_obsolete ──────────────────────────────────────────────────────

def test_flag_obsolete_sets_retired(tmp_path):
    import self_improvement.unlearn as ul
    ledger = tmp_path / "lessons_ledger.jsonl"
    _write_ledger(ledger, [_make_lesson("L-001", "abc123", "test lesson")])
    old = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    try:
        found = ul.flag_obsolete("L-001", reason="test")
        assert found is True
        data = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
        assert data[0]["status"] == "retired"
        assert data[0]["reason"] == "test"
        assert data[0]["retired_at"] is not None
    finally:
        ul._LESSONS_PATH = old


def test_flag_obsolete_returns_false_when_not_found(tmp_path):
    import self_improvement.unlearn as ul
    ledger = tmp_path / "lessons_ledger.jsonl"
    _write_ledger(ledger, [_make_lesson("L-001", "abc", "test")])
    old = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    try:
        found = ul.flag_obsolete("L-999")
        assert found is False
    finally:
        ul._LESSONS_PATH = old


def test_flag_obsolete_preserves_history(tmp_path):
    import self_improvement.unlearn as ul
    ledger = tmp_path / "lessons_ledger.jsonl"
    lessons = [_make_lesson("L-001", "abc", "keep this"), _make_lesson("L-002", "xyz", "other")]
    _write_ledger(ledger, lessons)
    old = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    try:
        ul.flag_obsolete("L-001")
        data = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
        # Both records must still exist
        assert len(data) == 2
        ids = [d["id"] for d in data]
        assert "L-001" in ids
        assert "L-002" in ids
    finally:
        ul._LESSONS_PATH = old


# ── Tests: deprioritise ───────────────────────────────────────────────────────

def test_deprioritise_reduces_strength(tmp_path):
    import self_improvement.unlearn as ul
    ledger = tmp_path / "lessons_ledger.jsonl"
    _write_ledger(ledger, [_make_lesson("L-001", "movement.sit", "movement.sit learned")])
    old = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    try:
        count = ul.deprioritise("movement.sit", reason="repeated failure")
        assert count == 1
        data = json.loads(ledger.read_text().strip())
        assert data["strength"] == pytest.approx(0.5, abs=0.01)
    finally:
        ul._LESSONS_PATH = old


def test_deprioritise_skips_retired(tmp_path):
    import self_improvement.unlearn as ul
    ledger = tmp_path / "lessons_ledger.jsonl"
    lesson = _make_lesson("L-001", "music.spotify", "spotify learned", status="retired")
    _write_ledger(ledger, [lesson])
    old = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    try:
        count = ul.deprioritise("music.spotify")
        assert count == 0
    finally:
        ul._LESSONS_PATH = old


# ── Tests: active_lessons ─────────────────────────────────────────────────────

def test_active_lessons_excludes_retired(tmp_path):
    import self_improvement.unlearn as ul
    ledger = tmp_path / "lessons_ledger.jsonl"
    lessons = [
        _make_lesson("L-001", "abc", "active lesson", status="confirmed"),
        _make_lesson("L-002", "xyz", "retired lesson", status="retired"),
    ]
    _write_ledger(ledger, lessons)
    old = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    try:
        active = ul.active_lessons()
        assert len(active) == 1
        assert active[0]["id"] == "L-001"
    finally:
        ul._LESSONS_PATH = old


# ── Tests: check_and_flag (integration) ──────────────────────────────────────

def test_check_and_flag_flags_obsolete_when_streak_meets_ceiling(tmp_path):
    import self_improvement.unlearn as ul
    import unittest.mock as mock
    ledger = tmp_path / "lessons_ledger.jsonl"
    lesson = _make_lesson("L-001", "music.spotify", "spotify capability learned", successes=3)
    _write_ledger(ledger, [lesson])
    old_path = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    old_ceiling = ul.FAILURE_CEILING
    ul.FAILURE_CEILING = 2
    try:
        # Patch the imported name inside capability_learning as used by check_and_flag
        with mock.patch("runtime.capability_learning.failure_streak", return_value=2):
            flagged = ul.check_and_flag("music.spotify")
        assert flagged is True
        data = json.loads(ledger.read_text().strip())
        assert data["status"] == "retired"
    finally:
        ul._LESSONS_PATH = old_path
        ul.FAILURE_CEILING = old_ceiling


def test_check_and_flag_noop_when_streak_below_ceiling(tmp_path):
    import self_improvement.unlearn as ul
    import unittest.mock as mock
    ledger = tmp_path / "lessons_ledger.jsonl"
    lesson = _make_lesson("L-001", "music.spotify", "spotify learned", successes=3)
    _write_ledger(ledger, [lesson])
    old_path = ul._LESSONS_PATH
    ul._LESSONS_PATH = str(ledger)
    old_ceiling = ul.FAILURE_CEILING
    ul.FAILURE_CEILING = 4
    try:
        with mock.patch("runtime.capability_learning.failure_streak", return_value=1):
            flagged = ul.check_and_flag("music.spotify")
        assert flagged is False
    finally:
        ul._LESSONS_PATH = old_path
        ul.FAILURE_CEILING = old_ceiling
