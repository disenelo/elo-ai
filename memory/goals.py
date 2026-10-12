"""
memory/goals.py — WO-B1-0138: active_goals store for eLo.

Goals are longer-running than intentions (which are per-turn / per-session).
A goal has a progress field and survives indefinitely until completed or abandoned.

Storage: data/goals.json
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path

_log = logging.getLogger("elo.goals")

_STORE = Path(__file__).parent.parent / "data" / "goals.json"

STATUS_ACTIVE    = "ACTIVE"
STATUS_DEFERRED  = "DEFERRED"
STATUS_COMPLETED = "COMPLETED"
STATUS_ABANDONED = "ABANDONED"


@dataclass
class Goal:
    goal_id:            str
    content:            str
    project_id:         str   = ""     # links to DISENELO project (elo-ai, elo-planet, etc.)
    progress:           str   = ""     # free-text progress note; updated as work advances
    progress_pct:       float = 0.0    # 0.0 → 1.0
    created_at:         float = field(default_factory=time.time)
    updated_at:         float = field(default_factory=time.time)
    status:             str   = STATUS_ACTIVE
    priority:           float = 0.5
    relevance_keywords: list  = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def as_prompt_line(self) -> str:
        age_h = (time.time() - self.created_at) / 3600
        age_str = f"{age_h:.0f}h" if age_h < 48 else f"{age_h/24:.0f}d"
        pct = f" {self.progress_pct*100:.0f}%" if self.progress_pct > 0 else ""
        proj = f" [{self.project_id}]" if self.project_id else ""
        prog_note = f" — {self.progress[:60]}" if self.progress else ""
        return f"[{self.status}]{pct}{proj} {self.content}{prog_note} (started {age_str} ago)"


# ── Storage ───────────────────────────────────────────────────────────────────

def _load() -> list[dict]:
    if not _STORE.exists():
        return []
    try:
        with _STORE.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        _log.warning("goals: load failed: %s", exc)
        return []


def _save(records: list[dict]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _STORE.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        _log.warning("goals: save failed: %s", exc)


def _records_to_goals(records: list[dict]) -> list[Goal]:
    out = []
    for r in records:
        try:
            out.append(Goal(**{k: v for k, v in r.items() if k in Goal.__dataclass_fields__}))
        except Exception:
            pass
    return out


# ── Write API ─────────────────────────────────────────────────────────────────

def add(
    content: str,
    *,
    project_id: str = "",
    priority: float = 0.5,
    relevance_keywords: list | None = None,
) -> Goal:
    """Create and persist a new active goal."""
    goal = Goal(
        goal_id=str(uuid.uuid4()),
        content=content,
        project_id=project_id,
        priority=priority,
        relevance_keywords=relevance_keywords or [],
    )
    records = _load()
    records.append(goal.as_dict())
    _save(records)
    _log.info("goals: added %s — %s", goal.goal_id[:8], content[:60])
    return goal


def update_progress(goal_id: str, progress: str = "", progress_pct: float | None = None) -> bool:
    """Update the progress note and/or percentage of a goal."""
    records = _load()
    for r in records:
        if r.get("goal_id") == goal_id:
            if progress:
                r["progress"] = progress
            if progress_pct is not None:
                r["progress_pct"] = max(0.0, min(1.0, progress_pct))
            r["updated_at"] = time.time()
            _save(records)
            return True
    return False


def complete(goal_id: str) -> bool:
    """Mark a goal as completed."""
    records = _load()
    for r in records:
        if r.get("goal_id") == goal_id:
            r["status"] = STATUS_COMPLETED
            r["progress_pct"] = 1.0
            r["updated_at"] = time.time()
            _save(records)
            return True
    return False


def abandon(goal_id: str) -> bool:
    """Mark a goal as abandoned."""
    records = _load()
    for r in records:
        if r.get("goal_id") == goal_id:
            r["status"] = STATUS_ABANDONED
            r["updated_at"] = time.time()
            _save(records)
            return True
    return False


# ── Read API ──────────────────────────────────────────────────────────────────

def active_goals() -> list[Goal]:
    """Return all non-completed, non-abandoned goals."""
    records = _load()
    goals = _records_to_goals(records)
    return [g for g in goals if g.status in (STATUS_ACTIVE, STATUS_DEFERRED)]


def goals_for_project(project_id: str) -> list[Goal]:
    """Return active goals for a specific project."""
    return [g for g in active_goals() if g.project_id == project_id]


def goals_prompt_block(max_goals: int = 3) -> str:
    """
    Build a prompt block showing eLo its active goals.
    Returns "" if no active goals.
    """
    try:
        open_g = active_goals()
        if not open_g:
            return ""
        open_g.sort(key=lambda g: -g.priority)
        lines = ["[ACTIVE GOALS — longer-running objectives eLo is tracking]"]
        for goal in open_g[:max_goals]:
            lines.append(f"  • {goal.as_prompt_line()}")
        if len(open_g) > max_goals:
            lines.append(f"  … and {len(open_g) - max_goals} more")
        return "\n".join(lines)
    except Exception as exc:
        _log.warning("goals_prompt_block failed (non-fatal): %s", exc)
        return ""
