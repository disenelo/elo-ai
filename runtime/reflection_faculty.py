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

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JOURNAL_DIR = os.path.join(_ROOT, "self", "journals")
_LESSON_LOG  = os.path.join(_ROOT, "self", "lessons_ledger.jsonl")
_FAILURE_LOG = os.path.join(_ROOT, "self", "failure_log.jsonl")

# W2 (card 0040): stable, monotonic, persisted session id — one per process
# start. Shared with self.decision_journal so a turn's decision row and any
# lesson evidence it produces carry the same session_id.
from runtime.session_id import SESSION_ID
_SESSION_ID: str = SESSION_ID


# ── Significance threshold ────────────────────────────────────────────────────
# Full Significance Engine is WO-009. Until then: simple heuristic.
# An episode is worth consolidating when any of these are true.

_SIG_MIN_WORDS      = 20    # user input long enough to contain substance
_SIG_ACTIONS        = {"build", "connect", "reflect", "remember", "design", "fix", "explain"}
_SIG_WEIGHT_MIN     = 5     # weight below this → peripheral, skip deep journal

# Card 0019 P0-B: only emit a personality proposal when the action names an
# actual trait in the eight-trait vector (personality_evolution_faculty).
_PERSONALITY_TRAIT_NAMES = frozenset({
    "curiosity", "patience", "confidence", "empathy",
    "discipline", "wonder", "playfulness", "directness",
})


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
    elif action.lower() in ("prefer", "choose", "enjoy", "like"):
        scope = "preference"

    statement = _derive_statement(session_summary, action, delta, scope)
    if not statement:
        return None

    # WO-095: sha1 identity key so repeats strengthen, never duplicate
    cause = delta
    norm_stmt = re.sub(r"\s+", " ", statement.strip().lower())
    lkey = hashlib.sha1(f"{scope}|{norm_stmt}|{cause}".encode()).hexdigest()[:16]

    # Card 0019 P0-B: emit a WELL-FORMED proposes dict.
    # Prior payload used `direction ∈ {1, -1}` and no `magnitude`; PersonalityDelta
    # requires `direction ∈ {"increase","decrease"}` and `magnitude ≤ MAX_STEP`.
    # Also: `action` is a CAL verb ("prefer", "choose", …), not a trait — only emit
    # when the verb actually names one of the eight personality traits.
    proposes: dict | None = None
    if scope == "preference" and action.lower() in _PERSONALITY_TRAIT_NAMES:
        proposes = {
            "trait":     action.lower(),
            "direction": "increase" if delta == "met" else "decrease",
            "magnitude": 0.02,  # MAX_STEP — bounded step per §7.5
        }

    # card 0082 F-3: applies_when, reason, prefers_action — required for consult()
    # to generate preferences, and for the D1 gate's _fit() to score the lesson.
    _cal_map = {
        "build": "build", "design": "build", "fix": "build",
        "connect": "connect", "remember": "reflect", "reflect": "reflect",
        "answer": "answer", "prefer": "answer", "choose": "answer",
        "enjoy": "celebrate", "like": "celebrate", "celebrate": "celebrate",
        "ground": "ground", "challenge": "challenge",
        "witness": "witness", "silence": "silence",
    }
    prefers_action = _cal_map.get(action.lower(), "")
    applies_when   = [x for x in [scope, action.lower()] if x]
    reason         = f"{delta} outcome during '{action}' ({scope}) — {statement}"

    return {
        "id":            f"L-{_ts_compact()}",
        "lesson_key":    lkey,
        "statement":     statement,
        "evidence":      [],     # filled by lesson_store.record_outcome() with SPOT codes
        "scope":         scope,
        "cause":         cause,
        "strength":      0.3,
        "delta":         delta,
        "status":        "candidate",
        "first_seen":    _now_iso(),
        "last_seen":     _now_iso(),
        "promoted_at":   None,
        "retired_at":    None,
        "reason":        reason,       # card 0082 F-3 — the why travels with the lesson
        "applies_when":  applies_when, # card 0082 F-3 — context for _fit() scoring
        "prefers_action": prefers_action,  # card 0082 F-3 — CAL action to prefer
        "proposes":      proposes,
        "ts":            _now_iso(),
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

    # Lessons Ledger — dedupe by lesson_key (WO-095: repeats strengthen, never duplicate)
    if lesson:
        lkey = lesson.get("lesson_key")
        if lkey:
            try:
                from self.lesson_store import record_outcome as _ls_record
                _ls_record(
                    lkey=lkey,
                    episode_ref=str(time.time()),   # unique per invocation; spot is verification, not episode ID
                    verified=bool(spot),             # vault-backed = verified
                    session_id=_SESSION_ID,
                    action=action,                   # card 0082 F-2 — D1 gate requires executed action
                    outcome=completion_state,        # card 0082 F-2 — D1 gate requires verified outcome
                    contradicting=(lesson.get("delta") in ("failed", "partial")),
                )
                # Only append to ledger if this lesson_key is new
                _existing_keys: set = set()
                try:
                    with open(_LESSON_LOG, encoding="utf-8") as _lf:
                        for _ll in _lf:
                            _ll = _ll.strip()
                            if _ll:
                                import json as _j
                                _existing_keys.add(_j.loads(_ll).get("lesson_key", ""))
                except FileNotFoundError:
                    pass
                if lkey not in _existing_keys:
                    _append_jsonl(_LESSON_LOG, lesson)
            except Exception:
                _append_jsonl(_LESSON_LOG, lesson)
        else:
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

    # WO-CANON-VII §7.4 preference update: only confirmed preference-scope lessons
    # promote to the PersonalityVector.preferences map. Trait deltas stay behind
    # the §7.5 validate_delta gate (identity-continuity) — this path is preferences
    # only, which are PATCH-versioned and independent from trait vectors.
    if lesson and lesson.get("scope") == "preference" and lesson.get("cause") == "met":
        try:
            from faculties.personality.personality_evolution_faculty import (
                load_personality as _pv_load,
                update_preference as _pv_update_pref,
                save_personality as _pv_save,
            )
            _pv = _pv_load()
            _pv2, _ver = _pv_update_pref(
                _pv,
                key=lesson.get("statement", "")[:64] or lesson.get("lesson_key", "unknown"),
                value=(lesson.get("evidence") or [None])[0] or "confirmed",
                strength=float(lesson.get("strength", 0.7)),
                evidence=lesson.get("id", ""),
            )
            _pv_save(_pv2)
        except Exception:
            pass

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
