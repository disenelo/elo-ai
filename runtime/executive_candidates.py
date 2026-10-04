"""
runtime/executive_candidates.py — Candidate-set logic for executive decisions.

WO-112 / BOARD-RULING-2026-09-27 Option (b).

FREEZE_V1_LOCK: runtime/executive.py is frozen and must not be modified.
This module adds candidate-set capability by being called FROM executive.py
(read-only from executive.py's perspective). executive.py never changes.

Candidate schema:
{
    "intent": "explore_upper_surface",
    "options": [
        {"action": "walk",      "utility": 0.42},
        {"action": "jump",      "utility": 0.68},
        {"action": "wall_jump", "utility": 0.87}
    ],
    "chosen":     "wall_jump",
    "reason":     "highest viable exploration route",
    "confidence": 0.81
}

Every decision path journals to self/journals/action_candidates.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Sequence

# Its OWN file. This pointed at self/journals/action_reliability.json, which
# self/decision_journal.py also owns — as a DICT of action -> score, while
# this module writes a LIST of decision events. The list on disk made
# decision_journal.get_reliability() raise AttributeError, taking out
# explain_last() ("why did you do that?"), and decision_journal's dict write
# would silently have destroyed every entry appended here. Two owners, one
# file, incompatible shapes, both directions lossy.
_RELIABILITY_LOG = Path(__file__).parent.parent / "self" / "journals" / "action_candidates.json"


# ── Journal helpers ────────────────────────────────────────────────────────────

def _load_log() -> list[dict]:
    try:
        _RELIABILITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        if _RELIABILITY_LOG.exists():
            with open(_RELIABILITY_LOG, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        pass
    return []


def _save_log(entries: list[dict]) -> None:
    try:
        _RELIABILITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_RELIABILITY_LOG, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def record_failure(intent: str, chosen: str, reason: str) -> None:
    entries = _load_log()
    entries.append({
        "ts":     time.strftime("%Y-%m-%dT%H:%M:%S"),
        "intent": intent,
        "chosen": chosen,
        "result": "FAIL",
        "reason": reason,
    })
    _save_log(entries)


def record_success(intent: str, chosen: str) -> None:
    entries = _load_log()
    entries.append({
        "ts":     time.strftime("%Y-%m-%dT%H:%M:%S"),
        "intent": intent,
        "chosen": chosen,
        "result": "PASS",
    })
    _save_log(entries)


# ── Candidate set building ─────────────────────────────────────────────────────

def build_candidate_set(
    intent: str,
    options: Sequence[dict],
    *,
    context: dict | None = None,
) -> dict:
    """
    Select the best action from candidates and return the full candidate record.

    options — list of {"action": str, "utility": float} dicts.
              utility is 0.0-1.0; higher is preferred.
    context — optional world context (platform, health, etc.) for future weighting.
    """
    if not options:
        return {
            "intent":     intent,
            "options":    [],
            "chosen":     None,
            "reason":     "no candidates",
            "confidence": 0.0,
        }

    ranked = sorted(options, key=lambda o: float(o.get("utility", 0.0)), reverse=True)
    best = ranked[0]
    chosen = best["action"]
    top_util = float(best.get("utility", 0.0))
    second_util = float(ranked[1].get("utility", 0.0)) if len(ranked) > 1 else 0.0

    confidence = round(top_util - second_util * 0.5, 3)

    reason = f"highest utility ({top_util:.2f})"
    if context:
        if context.get("health_low") and chosen in ("jump", "wall_jump"):
            reason += " — health low, prefer grounded action"
            chosen = next(
                (o["action"] for o in ranked if o["action"] not in ("jump", "wall_jump")),
                chosen,
            )

    record = {
        "intent":     intent,
        "options":    list(ranked),
        "chosen":     chosen,
        "reason":     reason,
        "confidence": confidence,
    }
    return record


# ── Early-return journals (four paths from server.py) ─────────────────────────
# server.py lines 1618/1638/1810/1564 are early-return decision points.
# They cannot be changed (server.py is live). This module provides journal
# helpers that can be called from wrapping layers.

def journal_early_return(path_id: str, intent: str, outcome: str) -> None:
    """
    Record an early-return decision from a server.py bypass path.

    path_id — identifies which early-return fired (e.g. "server:1618").
    intent  — the detected intent at that point.
    outcome — what was returned (e.g. "self_ref_rationale", "cached_response").
    """
    entries = _load_log()
    entries.append({
        "ts":      time.strftime("%Y-%m-%dT%H:%M:%S"),
        "type":    "early_return",
        "path_id": path_id,
        "intent":  intent,
        "outcome": outcome,
    })
    _save_log(entries)
