"""
memory/journal_router.py — Multi-Journal Routing System for eLo OS.

Takes a significance profile (from significance_engine.evaluate()) and routes
the interaction to the appropriate journals:

  RUNTIME JOURNAL  — always (ephemeral session state in elo_state.json)
  OBSIDIAN JOURNAL — when significance justifies long-term semantic memory
  GITHUB JOURNAL   — when system structure has changed (pending commit log)

Replaces the dumb turn-counter in truth_sync.maybe_compress with
significance-driven routing.

Routing thresholds (tunable via .env):
    ELO_OBS_THRESHOLD=0.55    overall significance → Obsidian
    ELO_OBS_PEAK=0.80         any single dim peak → Obsidian
    ELO_GH_THRESHOLD=0.65     system_change dim → GitHub pending log
    ELO_DEEP_THRESHOLD=0.82   overall → use weight=7 (important memory)
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

# ── Thresholds ────────────────────────────────────────────────────────────────

_OBS_THRESHOLD  = float(os.environ.get("ELO_OBS_THRESHOLD",  "0.42"))
_OBS_PEAK       = float(os.environ.get("ELO_OBS_PEAK",       "0.80"))
_GH_THRESHOLD   = float(os.environ.get("ELO_GH_THRESHOLD",   "0.65"))
_DEEP_THRESHOLD = float(os.environ.get("ELO_DEEP_THRESHOLD", "0.82"))

_STANDARD_WEIGHT = 5
_DEEP_WEIGHT     = 7

_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PENDING_FILE = os.path.join(_ROOT, "logs", "pending_commits.jsonl")


# ── Routing decision ──────────────────────────────────────────────────────────

def _should_obsidian(profile: dict) -> bool:
    overall = profile.get("overall", 0.0)
    if overall >= _OBS_THRESHOLD:
        return True
    return any(
        v >= _OBS_PEAK
        for k, v in profile.items()
        if k != "overall"
    )


def _should_github(profile: dict) -> bool:
    return profile.get("system_change", 0.0) >= _GH_THRESHOLD


def _memory_weight(profile: dict) -> int:
    return _DEEP_WEIGHT if profile.get("overall", 0.0) >= _DEEP_THRESHOLD else _STANDARD_WEIGHT


# ── Journal writes ────────────────────────────────────────────────────────────

def _write_obsidian(
    raw: str, response: str, action: str,
    state: dict, profile: dict, weight: int,
) -> Optional[str]:
    """Compress to Obsidian via truth_sync."""
    try:
        from tools.truth_sync import compress_to_obsidian
        return compress_to_obsidian(raw, response, action, state, weight=weight)
    except Exception as e:
        print(f"[journal-router] Obsidian write failed: {e}")
        return None


def _log_github_pending(
    raw: str, response: str, action: str, profile: dict,
) -> None:
    """Append a pending commit entry for user review — never auto-commits."""
    try:
        os.makedirs(os.path.dirname(_PENDING_FILE), exist_ok=True)
        entry = {
            "ts":            datetime.now().isoformat(),
            "action":        action,
            "system_change": round(profile.get("system_change", 0.0), 3),
            "overall":       round(profile.get("overall",       0.0), 3),
            "user_input":    raw[:200],
            "elo_response":  response[:200],
            "status":        "pending",
        }
        with open(_PENDING_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"[journal-router] GitHub pending commit logged → {_PENDING_FILE}")
    except Exception as e:
        print(f"[journal-router] GitHub log failed: {e}")


# ── Public API ────────────────────────────────────────────────────────────────

def route(
    raw:      str,
    response: str,
    action:   str,
    plan=None,
    state:    dict | None = None,
) -> dict:
    """
    Evaluate significance and route to journals accordingly.

    This is the main entry point called from server.py after each turn.
    It replaces the turn-counter threshold in truth_sync.maybe_compress.

    Returns: routing_decision dict with profile + journal flags.
    """
    if state is None:
        state = {}

    # Score
    from memory.significance_engine import evaluate, format_profile
    profile  = evaluate(raw, response, action, plan=plan, state=state)
    weight   = _memory_weight(profile)

    decision = {
        "runtime":      True,                     # always written (elo_state.json)
        "obsidian":     _should_obsidian(profile),
        "github_flag":  _should_github(profile),
        "weight":       weight,
        "significance": format_profile(profile),
        "profile":      profile,
    }

    # Runtime is always written — no action needed here (state_manager handles it)

    # Trust signal: deep relationship or creative moments accelerate rapport
    # relationship_faculty reads trust_signals to boost familiarity score.
    if profile.get("overall", 0) > 0.85:
        dominant = max(("relationship", "creation"), key=lambda k: profile.get(k, 0))
        if profile.get(dominant, 0) > 0.60:
            import time as _t
            signals = state.get("trust_signals", [])
            signals = list(signals)  # don't mutate in place
            signals.append({"ts": round(_t.time(), 3), "category": dominant})
            state["trust_signals"] = signals[-10:]  # keep last 10

    # Obsidian
    if decision["obsidian"]:
        spot = _write_obsidian(raw, response, action, state, profile, weight)
        decision["obsidian_spot"] = spot

    # GitHub pending log
    if decision["github_flag"]:
        _log_github_pending(raw, response, action, profile)

    return decision
