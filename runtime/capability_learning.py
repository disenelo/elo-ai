"""
runtime/capability_learning.py — WO-055: Capability Learning

Activates the router learning_buffer as an ACTIVE system.
Tracks repeated capability failures → records rule candidates →
after threshold accumulates, proposes a WO automatically.

Vol V Ch.6 (Reflection & Growth) — operational self-improvement.

API:
    record_failure(capability_id, context)  — note a failure
    record_success(capability_id)           — reset the streak
    get_candidates()                        — list current rule candidates
    maybe_propose()                         — write a WO proposal if threshold met
    scan_buffer(n)                          — ingest recent buffer entries
    capability_learning_prompt_block()      — formatted prompt block for injection
"""
from __future__ import annotations

import json
import os
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_PATH = os.path.join(_ROOT, "logs", "learning_proposals.jsonl")
# _failure_streaks disk persistence — streaks survive process restarts
_STREAKS_PATH = os.path.join(_ROOT, "self", "state", "failure_streaks.json")

FAILURE_THRESHOLD  = 3    # consecutive failures → rule candidate
PROPOSAL_THRESHOLD = 3    # rule candidates → WO proposal

# ── In-memory state ───────────────────────────────────────────────────────────
_failure_streaks: dict[str, int] = {}         # capability_id → consecutive fails
_rule_candidates: list[dict]     = []         # accumulated candidates this session


def _load_streaks() -> None:
    """Load failure streaks from disk into _failure_streaks on startup."""
    global _failure_streaks
    try:
        with open(_STREAKS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            _failure_streaks = {k: int(v) for k, v in data.items() if isinstance(v, (int, float))}
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    except Exception:
        pass


def _save_streaks() -> None:
    """Persist _failure_streaks to disk. Fail-quiet."""
    try:
        os.makedirs(os.path.dirname(_STREAKS_PATH), exist_ok=True)
        with open(_STREAKS_PATH, "w", encoding="utf-8") as f:
            json.dump(_failure_streaks, f)
    except Exception:
        pass


# Load persisted streaks on module import
_load_streaks()


# ── Core tracking ─────────────────────────────────────────────────────────────

def record_failure(capability_id: str, context: str = "") -> None:
    """
    Note a capability failure. If the consecutive streak reaches
    FAILURE_THRESHOLD, a rule candidate is recorded.

    Args:
        capability_id — e.g. "movement.sit", "music.spotify"
        context       — short description of what failed
    """
    _failure_streaks[capability_id] = _failure_streaks.get(capability_id, 0) + 1
    streak = _failure_streaks[capability_id]
    _save_streaks()

    if streak >= FAILURE_THRESHOLD:
        _add_candidate(capability_id, streak, context)


def record_success(capability_id: str) -> None:
    """Reset the failure streak for this capability on success."""
    _failure_streaks.pop(capability_id, None)
    _save_streaks()


def get_candidates() -> list[dict]:
    """Return current rule candidates (accumulated this session)."""
    return list(_rule_candidates)


def failure_streak(capability_id: str) -> int:
    """Return the current consecutive failure count for a capability."""
    return _failure_streaks.get(capability_id, 0)


# ── Rule candidate ────────────────────────────────────────────────────────────

def _add_candidate(capability_id: str, streak: int, context: str) -> None:
    already = any(c["capability_id"] == capability_id for c in _rule_candidates)
    candidate = {
        "_ts":           round(time.time(), 3),
        "capability_id": capability_id,
        "streak":        streak,
        "context":       context[:300],
        "rule_draft":    _draft_rule(capability_id, streak, context),
    }
    if already:
        # Update streak on existing candidate, don't duplicate
        for c in _rule_candidates:
            if c["capability_id"] == capability_id:
                c["streak"] = streak
                c["rule_draft"] = candidate["rule_draft"]
                c["_ts"] = candidate["_ts"]
    else:
        _rule_candidates.append(candidate)

    maybe_propose()


def _draft_rule(capability_id: str, streak: int, context: str) -> str:
    return (
        f"Rule candidate: '{capability_id}' failed {streak}× consecutively. "
        f"Context: {context or 'no context'}. "
        f"Never announce {capability_id} success before receiving an ACK. "
        f"Propose: gate '{capability_id}' announcements behind confirm signal."
    )


# ── WO proposal ───────────────────────────────────────────────────────────────

def maybe_propose() -> bool:
    """
    Write a WO proposal to logs/learning_proposals.jsonl if the candidate
    count hits PROPOSAL_THRESHOLD.

    Returns True if a proposal was written, False otherwise.
    """
    if len(_rule_candidates) < PROPOSAL_THRESHOLD:
        return False

    proposal = {
        "_ts":        round(time.time(), 3),
        "type":       "wo_proposal",
        "source":     "capability_learning",
        "candidates": list(_rule_candidates),
        "title":      f"Learning: {len(_rule_candidates)} rule candidates accumulated",
        "body":       (
            f"Capability Learning detected {len(_rule_candidates)} repeated failures. "
            f"Capabilities involved: "
            f"{', '.join(c['capability_id'] for c in _rule_candidates)}. "
            f"Proposed action: review ACK contracts + add faculty-health gates. "
            f"Auto-generated — review in engineering/work_orders/."
        ),
    }
    _write_proposal(proposal)
    return True


def _write_proposal(proposal: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(proposal) + "\n")
    except Exception:
        pass


# ── Buffer scan ───────────────────────────────────────────────────────────────

def scan_buffer(n: int = 50) -> dict:
    """
    Ingest the last n entries from learning_buffer and update in-memory state.

    Consecutive "failed"/"no_agent" entries for the same intent increment the
    streak; "success"/"confirmed" entries reset it.

    Returns a summary dict for diagnostics.
    """
    try:
        from runtime.router.learning_buffer import recent as _recent
        entries = _recent(n)
    except Exception:
        return {"scanned": 0, "new_candidates": 0}

    new_candidates = 0
    for entry in reversed(entries):   # oldest-first so streaks accumulate correctly
        intent = entry.get("intent", "")
        outcome = entry.get("outcome", "")
        if not intent:
            continue
        if outcome in ("failed", "no_agent"):
            before = len(_rule_candidates)
            record_failure(intent, context=entry.get("raw", "")[:100])
            if len(_rule_candidates) > before:
                new_candidates += 1
        elif outcome in ("success", "confirmed"):
            record_success(intent)

    return {"scanned": len(entries), "new_candidates": new_candidates}


# ── Prompt injection ──────────────────────────────────────────────────────────

def capability_learning_prompt_block() -> str:
    """
    Build a prompt block summarising active capability failure patterns.

    Calls scan_buffer() to ingest the latest buffer entries, then returns
    a compact block listing any capabilities with repeated failures.
    Returns "" when there are no candidates (non-blocking).
    """
    try:
        scan_buffer(n=50)
        candidates = get_candidates()
        if not candidates:
            return ""
        lines = ["[CAPABILITY FAILURE PATTERNS — learned from interaction]"]
        for c in candidates[:5]:  # cap at 5 to avoid prompt bloat
            cap_id = c.get("capability_id", "unknown")
            streak = c.get("streak", 0)
            lines.append(f"  • {cap_id}: {streak} consecutive failures — "
                         "do not announce success before receiving confirmation")
        lines.append("These are real failure patterns from this session. Adjust accordingly.")
        return "\n".join(lines)
    except Exception:
        return ""
