"""
self_improvement/unlearn.py — WO-UNLEARN-001

Deprioritises obsolete learned behaviour. Complements capability_learning.py
(which records failures → candidates) by marking lessons as superseded when
prior successes are overwhelmed by subsequent failures.

API:
    deprioritise(pattern_id, reason)  — reduce weight of a learned pattern
    flag_obsolete(lesson_id, reason)  — mark a lesson superseded; removed from
                                        active injection but kept in history
    check_and_flag(capability_id)     — call from record_failure() after N
                                        failures on a previously-successful pattern
"""
from __future__ import annotations

import json
import logging
import os
import time

_log = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LESSONS_PATH = os.path.join(_ROOT, "self", "lessons_ledger.jsonl")
_UNLEARN_LOG  = os.path.join(_ROOT, "self", "unlearn_log.jsonl")

# A pattern that had >= SUCCESS_FLOOR successes is worth protecting; if it then
# accumulates FAILURE_CEILING additional failures it is flagged obsolete.
SUCCESS_FLOOR   = 3
FAILURE_CEILING = 4


# ── Disk helpers ──────────────────────────────────────────────────────────────

def _load_lessons() -> list[dict]:
    try:
        with open(_LESSONS_PATH, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        return [json.loads(l) for l in lines]
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    except Exception:
        return []


def _save_lessons(lessons: list[dict]) -> None:
    try:
        os.makedirs(os.path.dirname(_LESSONS_PATH), exist_ok=True)
        with open(_LESSONS_PATH, "w", encoding="utf-8") as f:
            for lesson in lessons:
                f.write(json.dumps(lesson) + "\n")
    except Exception as e:
        _log.warning("unlearn: failed to save lessons_ledger: %s", e)


def _append_unlearn_log(entry: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_UNLEARN_LOG), exist_ok=True)
        with open(_UNLEARN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── Public API ────────────────────────────────────────────────────────────────

def flag_obsolete(lesson_id: str, reason: str = "") -> bool:
    """
    Mark a lesson as retired/superseded. It stays in lessons_ledger (provenance
    preserved) but its status is set to 'retired' so active injection skips it.

    Returns True if the lesson was found and flagged, False if not found.
    """
    lessons = _load_lessons()
    found = False
    for lesson in lessons:
        if lesson.get("id") == lesson_id:
            lesson["status"]     = "retired"
            lesson["retired_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            lesson["reason"]     = reason or "flagged obsolete by unlearn.py"
            found = True
            break

    if found:
        _save_lessons(lessons)
        _append_unlearn_log({
            "ts":        time.time(),
            "action":    "flag_obsolete",
            "lesson_id": lesson_id,
            "reason":    reason,
        })
        _log.info("unlearn: lesson %s flagged obsolete — %s", lesson_id, reason or "no reason given")

    return found


def deprioritise(pattern_id: str, reason: str = "") -> int:
    """
    Reduce the strength of all lessons whose lesson_key or statement contains
    pattern_id. Does NOT retire them — just reduces their influence weight by 50%.

    Returns the number of lessons updated.
    """
    lessons = _load_lessons()
    updated = 0
    for lesson in lessons:
        key = lesson.get("lesson_key", "") or ""
        stmt = lesson.get("statement", "") or ""
        if pattern_id.lower() in key.lower() or pattern_id.lower() in stmt.lower():
            if lesson.get("status") in (None, "confirmed"):
                old = lesson.get("strength", 1.0)
                lesson["strength"] = round(max(0.1, old * 0.5), 4)
                lesson["reason"]   = reason or f"deprioritised by unlearn.py (pattern: {pattern_id})"
                updated += 1

    if updated:
        _save_lessons(lessons)
        _append_unlearn_log({
            "ts":         time.time(),
            "action":     "deprioritise",
            "pattern_id": pattern_id,
            "reason":     reason,
            "count":      updated,
        })
        _log.info("unlearn: deprioritised %d lesson(s) matching %r", updated, pattern_id)

    return updated


def check_and_flag(capability_id: str) -> bool:
    """
    Inspect lessons_ledger for lessons related to capability_id that previously
    had >= SUCCESS_FLOOR successes but now also have >= FAILURE_CEILING failures
    recorded in capability_learning's failure streak.

    Called from capability_learning.record_failure() after the streak threshold
    is met. Returns True if any lesson was flagged.
    """
    try:
        from runtime.capability_learning import failure_streak
        streak = failure_streak(capability_id)
    except Exception:
        streak = 0

    if streak < FAILURE_CEILING:
        return False

    lessons = _load_lessons()
    flagged = False
    for lesson in lessons:
        stmt = (lesson.get("statement") or "").lower()
        key  = (lesson.get("lesson_key") or "").lower()
        cid  = capability_id.lower()
        if cid not in stmt and cid not in key:
            continue
        if lesson.get("status") in ("retired",):
            continue
        # Check prior success count from evidence
        evidence = lesson.get("evidence") or []
        successes = sum(1 for e in evidence if e.get("outcome") == "complete")
        if successes < SUCCESS_FLOOR:
            continue
        flag_obsolete(
            lesson["id"],
            reason=(
                f"capability '{capability_id}' had {successes} prior successes "
                f"but accumulated {streak} consecutive failures — pattern superseded"
            ),
        )
        flagged = True

    return flagged


def active_lessons() -> list[dict]:
    """Return only non-retired lessons for prompt injection."""
    return [l for l in _load_lessons() if l.get("status") != "retired"]
