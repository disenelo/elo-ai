"""
runtime/reflection_faculty.py — Reflection & Growth Engine (WO-005)

Replaces compress_session() as the session integration path.

Spec:  docs/architecture/17_memory_update.md §6
       docs/architecture/Volume_V/06_Reflection_Growth_Engine.md
Canon: integrate_session() replaces compress_session()
       "Compression stores. Integration grows."  (16_runtime_contracts.md)

CRITICAL PLACEMENT (MUST):
  This faculty NEVER runs in the response path.
  It runs only at session close or idle (offline integration window).
  It writes to vault and journals — never to output.

FREEZE_V1_LOCK: does not touch runtime/executive.py or prompts/.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JOURNAL_DIR = os.path.join(_ROOT, "self", "journals")
_LESSON_LOG  = os.path.join(_ROOT, "self", "lessons_ledger.jsonl")
_FAILURE_LOG = os.path.join(_ROOT, "self", "failure_log.jsonl")


# ── Significance threshold ────────────────────────────────────────────────────
# Full Significance Engine is WO-009. Until then: simple heuristic.
# An episode is worth consolidating when any of these are true.

_SIG_MIN_WORDS      = 20    # user input long enough to contain substance
_SIG_ACTIONS        = {"build", "connect", "reflect", "remember", "design", "fix", "explain"}
_SIG_WEIGHT_MIN     = 5     # weight below this → peripheral, skip deep journal


def _is_significant(
    session_summary: str,
    action: str = "",
    weight: int = 5,
) -> bool:
    """Basic significance gate (pre-Significance-Engine heuristic)."""
    if weight >= 7:
        return True
    word_count = len(session_summary.split())
    if word_count < _SIG_MIN_WORDS:
        return False
    if action.lower() in _SIG_ACTIONS:
        return True
    return weight >= _SIG_WEIGHT_MIN


# ── Lesson formation ──────────────────────────────────────────────────────────

def _form_lesson(
    session_summary: str,
    action: str,
    completion_state: str,
    planned_objective: str,
) -> dict | None:
    """
    Extract a candidate lesson from the gap between intention and reality.
    Returns None if there's nothing durable to learn.
    """
    if not session_summary:
        return None

    delta = "met"
    if completion_state in ("partial", "failed"):
        delta = completion_state
    elif "error" in session_summary.lower() or "fail" in session_summary.lower():
        delta = "partial"

    if delta == "met" and not planned_objective:
        return None

    scope = "behaviour"
    if action.lower() in ("build", "design", "fix"):
        scope = "capability"
    elif action.lower() in ("connect", "remember"):
        scope = "relationship"

    statement = _derive_statement(session_summary, action, delta, scope)
    if not statement:
        return None

    return {
        "id":        f"L-{_ts_compact()}",
        "statement": statement,
        "evidence":  [session_summary[:120]],
        "scope":     scope,
        "strength":  0.3,         # candidate — strengthens with confirming evidence
        "delta":     delta,
        "status":    "candidate",
        "ts":        _now_iso(),
    }


def _derive_statement(summary: str, action: str, delta: str, scope: str) -> str:
    """Produce a one-sentence lesson from the episode."""
    s = summary.lower()
    if delta == "failed":
        return f"When {action} meets an obstacle here, adapt the approach rather than retrying identically."
    if delta == "partial":
        return f"Partial progress on {action} — check dependencies before next attempt."
    if "build" in action.lower():
        return f"Completed a {scope} milestone — reinforce this pattern."
    return ""


# ── Journal writers ──────────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    os.makedirs(_JOURNAL_DIR, exist_ok=True)
    os.makedirs(os.path.join(_ROOT, "self"), exist_ok=True)


def _append_jsonl(path: str, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_journal_entry(
    session_summary: str,
    project: str,
    action: str,
    lesson: dict | None,
    spot: str | None,
    completion_state: str,
) -> None:
    """Append to the Growth Journal and (on failure) the Failure Log."""
    _ensure_dirs()
    entry = {
        "ts":          _now_iso(),
        "project":     project,
        "action":      action,
        "summary":     session_summary[:300],
        "spot":        spot,
        "completion":  completion_state,
        "has_lesson":  lesson is not None,
    }

    # Growth Journal — all consolidated episodes
    journal_path = os.path.join(_JOURNAL_DIR, "growth_journal.jsonl")
    _append_jsonl(journal_path, entry)

    # Lessons Ledger — confirmed + candidate lessons
    if lesson:
        _append_jsonl(_LESSON_LOG, lesson)

    # Failure Log — partial/failed turns with cause tagging
    if completion_state in ("partial", "failed"):
        failure_entry = {
            "ts":      _now_iso(),
            "project": project,
            "action":  action,
            "delta":   completion_state,
            "summary": session_summary[:200],
        }
        _append_jsonl(_FAILURE_LOG, failure_entry)


# ── Core: integrate_session() ─────────────────────────────────────────────────

def integrate_session(
    session_summary: str,
    *,
    project:           str = "general",
    weight:            int = 5,
    tags:              list[str] | None = None,
    action:            str = "",
    planned_objective: str = "",
    completion_state:  str = "met",
    execution_report:  Any = None,  # ExecutionReport dataclass if available
) -> dict:
    """
    Integrate a session into durable memory. Replaces compress_session().

    "Compression stores. Integration grows."  — 16_runtime_contracts.md

    This function:
      1. Gates on significance (only meaningful episodes are consolidated).
      2. Writes a tiered vault record (SPOT_CODES → summary → deep).
      3. Forms a candidate lesson from the intention↔reality gap.
      4. Emits journal entries (Growth Journal, Lessons Ledger, Failure Log).
      5. Returns a result dict — never raises (atomic: vault preserved on failure).

    Args:
        session_summary:   The meaning-compressed session text (from summariser).
        project:           Domain label for vault record (e.g. "elo-game").
        weight:            Importance weight 1–10 (higher → more durable).
        tags:              Additional vault tags.
        action:            CAL action that drove the session (e.g. "build").
        planned_objective: What the Executive intended for this turn.
        completion_state:  "met" | "partial" | "failed" | "exceeded".
        execution_report:  ExecutionReport dataclass (optional; used when available).

    Returns:
        {
          "spot":    str | None,   # SPOT_CODES record ID
          "lesson":  dict | None,  # candidate lesson formed
          "skipped": bool,         # True if significance gate blocked consolidation
          "error":   str | None,   # non-None if vault write failed
        }
    """
    # Unpack ExecutionReport if passed as a dataclass
    if execution_report is not None:
        try:
            if not action:
                action = getattr(execution_report, "planned_action", "") or action
            if not planned_objective:
                planned_objective = getattr(execution_report, "planned_objective", "") or planned_objective
            if completion_state == "met":
                completion_state = getattr(execution_report, "completion_state", "met") or "met"
        except Exception:
            pass

    # ── 1. Significance gate ──────────────────────────────────────────────────
    if not _is_significant(session_summary, action=action, weight=weight):
        return {"spot": None, "lesson": None, "skipped": True, "error": None}

    # ── 2. Vault write — routed through MemoryFaculty (WO-CANON-VIII §4.1.2) ──
    spot: str | None = None
    vault_error: str | None = None
    try:
        from memory.memory_faculty import MemoryFaculty as _MemFac, MemoryCandidate as _MemCand
        _write_tags = tuple(
            (tags or []) + ["integrated", action.lower()]
            if action else (tags or []) + ["integrated"]
        )
        _decision = _MemFac().submit(_MemCand(
            source_faculty="reflection",
            content=session_summary,
            proposed_type="episodic",
            proposed_weight=weight,
            significance=max(0.2, weight / 9.0),   # already passed _is_significant gate
            project=project,
            summary=_first_sentence(session_summary),
            tags=_write_tags,
        ))
        spot = _decision.get("spot")
        if _decision.get("action") == "drop":
            vault_error = _decision.get("reason", "dropped by MemoryFaculty")
    except Exception as exc:
        vault_error = str(exc)

    # ── 3. Lesson formation ────────────────────────────────────────────────────
    lesson: dict | None = None
    try:
        lesson = _form_lesson(session_summary, action, completion_state, planned_objective)
    except Exception:
        lesson = None

    # ── 4. Journal synthesis ───────────────────────────────────────────────────
    try:
        _write_journal_entry(
            session_summary=session_summary,
            project=project,
            action=action,
            lesson=lesson,
            spot=spot,
            completion_state=completion_state,
        )
    except Exception:
        pass

    return {
        "spot":    spot,
        "lesson":  lesson,
        "skipped": False,
        "error":   vault_error,
    }


# ── Utilities ────────────────────────────────────────────────────────────────

def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)
    return parts[0] if parts else text[:120]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
