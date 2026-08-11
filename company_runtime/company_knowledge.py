"""
company_runtime/company_knowledge.py — WO-080: Company Knowledge Interface (depth layer)

Extends the WO-048 company briefing path with deeper, WO-level detail.
READS company_state.json — never scans the codebase or filesystem.
ADDITIVE ONLY — never duplicates handle_company_voice_intent, never re-reads the board directly.

Guardrails (WO-080 §spec):
  - Read-only: only blender/company_state.json (the curated sandbox), not raw files
  - permitted_actions gate: check_permitted() enforced HERE before any action returns
  - L3 for anything real: prepare freely; commit/send/spend is refused with honest message
  - Honest gap: "I don't have that" returned when data is absent — never fabricated

Entry points:
  load_state(state_path=None)                  → dict  (read-only)
  query_active_wos(state)                      → list[dict]  (non-done/blocked WOs)
  query_regressions(state)                     → list[dict]  (active regressions)
  check_permitted(action, state)               → bool  (permitted_actions gate)
  build_deep_brief(query, state)               → str   (rich real answer; honest gap on missing)
  prepare_review_pack(state)                   → dict  (structured summary, prepare only)
"""
from __future__ import annotations

import json
import os
import re

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "blender", "company_state.json")

# Actions permitted by default when the state file has no permitted_actions field
_DEFAULT_PERMITTED: frozenset[str] = frozenset({
    "assemble_review_pack",
    "query_active_wos",
    "query_regressions",
    "summarise_sprint",
})

# Actions that always require David L3 — never auto-permitted
_L3_REQUIRED: frozenset[str] = frozenset({
    "commit", "send", "spend", "approve", "publish", "deploy",
    "pay", "sign", "submit",
})

# Query patterns that signal a deep-WO question
_DEEP_TASK_PATTERNS: tuple[str, ...] = (
    "what tasks", "what work orders", "what are we working on", "active wos",
    "what wos", "which wos", "any regressions", "what's broken",
    "review pack", "sprint summary", "sprint close",
)

# ── State reader ──────────────────────────────────────────────────────────────

def load_state(state_path: str | None = None) -> dict:
    """
    Load company_state.json read-only. Returns {} if absent or unreadable.
    Never writes, never re-publishes from the board (that is company_state_writer's job).
    """
    path = state_path or _STATE_PATH
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── WO query ──────────────────────────────────────────────────────────────────

def query_active_wos(state: dict, max_items: int = 10) -> list[dict]:
    """
    Return non-done, non-blocked WOs from the board in state.
    Each result: {id, title, status, priority}. No fabrication — empty state = [].
    """
    board = state.get("board", [])
    if not board:
        return []
    active = [
        {
            "id":       row.get("id", "?"),
            "title":    row.get("title", "?")[:60],
            "status":   row.get("status", "?"),
            "priority": row.get("pri", "?"),
        }
        for row in board
        if row.get("status") not in ("DONE", "BLOCKED")
    ]
    return active[:max_items]


# ── Regression query ──────────────────────────────────────────────────────────

def query_regressions(state: dict) -> list[dict]:
    """
    Return active regression entries from state["regressions"].
    Returns [] when none exist or field absent — never fabricates.
    """
    return [
        {"module": r.get("module", "?"), "severity": r.get("severity", "?"),
         "description": r.get("description", "?")}
        for r in state.get("regressions", [])
        if r.get("severity") in ("critical", "major", "minor")
    ]


# ── Permitted-actions gate ────────────────────────────────────────────────────

def check_permitted(action: str, state: dict) -> bool:
    """
    Return True if action is in the permitted_actions list.
    L3-required actions always return False regardless of state.
    """
    if not action:
        return False
    action_lower = action.lower().strip()
    # L3 wall — always refused
    if any(kw in action_lower for kw in _L3_REQUIRED):
        return False
    permitted = set(state.get("permitted_actions", list(_DEFAULT_PERMITTED)))
    return action_lower in permitted or action in permitted


# ── Deep brief ────────────────────────────────────────────────────────────────

def is_deep_company_query(raw: str) -> bool:
    """Return True for queries that warrant the deep WO-level answer."""
    low = raw.lower()
    return any(p in low for p in _DEEP_TASK_PATTERNS)


def build_deep_brief(query: str, state: dict) -> str:
    """
    Return a deep, real answer derived from company_state. Honest gap when data is absent.
    Never invents WO IDs, deadlines, or team members.
    """
    if not state:
        return honest_gap("company state")

    low = query.lower()

    # Review pack
    if "review pack" in low or "sprint close" in low or "sprint summary" in low:
        pack = prepare_review_pack(state)
        if not pack.get("active_wos") and not pack.get("completed_this_sprint"):
            return honest_gap("sprint data")
        lines = ["Here's what I can put together for the sprint review:"]
        if pack.get("milestone"):
            lines.append(f"  Milestone: {pack['milestone']}.")
        if pack.get("completed_this_sprint"):
            done_ids = ", ".join(w["id"] for w in pack["completed_this_sprint"][:5])
            lines.append(f"  Completed: {done_ids}.")
        if pack.get("active_wos"):
            active_ids = ", ".join(w["id"] for w in pack["active_wos"][:5])
            lines.append(f"  Still active: {active_ids}.")
        if pack.get("regressions"):
            lines.append(f"  Regressions open: {len(pack['regressions'])}.")
        lines.append("  This is a prepared summary — real actions need your sign-off.")
        return " ".join(lines)

    # Regression query
    if "regression" in low or "broken" in low or "failing" in low:
        regs = query_regressions(state)
        if not regs:
            return "No active regressions logged in company state."
        reg_lines = "; ".join(
            f"{r['module']} ({r['severity']}): {r['description'][:40]}"
            for r in regs[:3]
        )
        return f"Active regressions: {reg_lines}."

    # Active WOs / tasks query
    active = query_active_wos(state, max_items=6)
    if not active:
        return honest_gap("active work orders")
    wo_lines = "; ".join(
        f"{w['id']} {w['status'].lower()} ({w['priority']})"
        for w in active[:5]
    )
    suffix = f" and {len(active) - 5} more" if len(active) > 5 else ""
    return f"Active work orders: {wo_lines}{suffix}. Board: engineering/work_orders/DISPATCH_BOARD.md."


def honest_gap(topic: str) -> str:
    """Return an honest 'I don't have that data' message for a missing topic."""
    return (
        f"I don't have {topic} data in my company state right now. "
        "Check the board directly: engineering/work_orders/DISPATCH_BOARD.md."
    )


# ── Review pack ───────────────────────────────────────────────────────────────

def prepare_review_pack(state: dict) -> dict:
    """
    Prepare a structured sprint review summary from real state.
    Returns a dict — pure data, no side effects.
    Real actions (commit/send) are L3-gated — this only assembles the summary.
    """
    board = state.get("board", [])
    return {
        "milestone":            state.get("company_focus", {}).get("milestone", ""),
        "active_wos":           query_active_wos(state),
        "completed_this_sprint": [
            {"id": r.get("id", "?"), "title": r.get("title", "?")[:50]}
            for r in board if r.get("status") == "DONE"
        ][:10],
        "regressions":          query_regressions(state),
        "waiting_david":        state.get("waiting_for_approval", []),
        "_note":                "prepare-only — commit/send requires David L3",
    }
