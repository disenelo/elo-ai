"""
memory/intentions.py — WO-ELO-IDENTITY-CANONICAL-001 / Intentions

eLo as a holder of intentions: can hold an unfinished thread, defer it, resume it.

Schema: ACTIVE → DEFERRED → RESUMED → COMPLETED | ABANDONED

Wired into the turn path via:
  1. intentions_prompt_block() — surfaces ACTIVE + DEFERRED at prompt-build time
  2. relevant_to_turn(text) — detects when a deferred intention matches the current turn
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Lock
from typing import Optional

_log = logging.getLogger(__name__)

_ROOT        = Path(__file__).parent.parent
_STORE       = _ROOT / "data" / "intentions.json"
_LOCK        = Lock()

# ── Status ────────────────────────────────────────────────────────────────────

STATUS_ACTIVE    = "ACTIVE"
STATUS_DEFERRED  = "DEFERRED"
STATUS_RESUMED   = "RESUMED"
STATUS_COMPLETED = "COMPLETED"
STATUS_ABANDONED = "ABANDONED"

_OPEN_STATUSES   = {STATUS_ACTIVE, STATUS_DEFERRED, STATUS_RESUMED}

# ── Schema ────────────────────────────────────────────────────────────────────

@dataclass
class Intention:
    intention_id:       str
    content:            str
    context:            str   = ""
    deferred_at:        float = 0.0
    deferred_reason:    str   = ""
    created_at:         float = field(default_factory=time.time)
    last_touched:       float = field(default_factory=time.time)
    status:             str   = STATUS_ACTIVE
    priority:           float = 0.5
    relevance_keywords: list  = field(default_factory=list)
    resumed_count:      int   = 0

    def as_dict(self) -> dict:
        return asdict(self)

    def as_prompt_line(self) -> str:
        age_h = (time.time() - self.created_at) / 3600
        age_str = f"{age_h:.0f}h ago" if age_h < 48 else f"{age_h/24:.0f} days ago"
        tag = f"[{self.status}]"
        reason = f" — held: {self.deferred_reason}" if self.deferred_reason else ""
        return f"{tag} {self.content}{reason} (from {age_str})"


# ── Storage ───────────────────────────────────────────────────────────────────

def _load() -> list[dict]:
    if not _STORE.exists():
        return []
    try:
        with _STORE.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        _log.warning("intentions: load failed: %s", exc)
        return []


def _save(records: list[dict]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _STORE.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        _log.warning("intentions: save failed: %s", exc)


def _records_to_intentions(records: list[dict]) -> list[Intention]:
    out = []
    for r in records:
        try:
            out.append(Intention(**{k: v for k, v in r.items() if k in Intention.__dataclass_fields__}))
        except Exception:
            pass
    return out


# ── Write API ─────────────────────────────────────────────────────────────────

def hold(
    content: str,
    context: str = "",
    priority: float = 0.5,
    keywords: list[str] | None = None,
) -> Intention:
    """
    Create a new ACTIVE intention — eLo is holding this thread.
    Returns the new Intention.
    """
    intention = Intention(
        intention_id=str(uuid.uuid4()),
        content=content.strip(),
        context=context.strip(),
        status=STATUS_ACTIVE,
        priority=priority,
        relevance_keywords=keywords or _extract_keywords(content),
    )
    with _LOCK:
        records = _load()
        records.append(intention.as_dict())
        _save(records)
    _log.info("intentions: holding — %r", content[:60])
    return intention


def defer(intention_id: str, reason: str = "") -> bool:
    """
    Move an ACTIVE/RESUMED intention to DEFERRED with a reason.
    Returns True if found and updated.
    """
    with _LOCK:
        records = _load()
        for r in records:
            if r.get("intention_id") == intention_id and r.get("status") in _OPEN_STATUSES:
                r["status"]          = STATUS_DEFERRED
                r["deferred_at"]     = time.time()
                r["deferred_reason"] = reason
                r["last_touched"]    = time.time()
                _save(records)
                _log.info("intentions: deferred %s — %r", intention_id[:8], reason[:60])
                return True
    return False


def resume(intention_id: str) -> bool:
    """
    Move a DEFERRED intention back to RESUMED.
    Increments resumed_count.
    """
    with _LOCK:
        records = _load()
        for r in records:
            if r.get("intention_id") == intention_id and r.get("status") == STATUS_DEFERRED:
                r["status"]       = STATUS_RESUMED
                r["last_touched"] = time.time()
                r["resumed_count"] = r.get("resumed_count", 0) + 1
                _save(records)
                _log.info("intentions: resumed %s", intention_id[:8])
                return True
    return False


def complete(intention_id: str) -> bool:
    """Mark an intention COMPLETED."""
    with _LOCK:
        records = _load()
        for r in records:
            if r.get("intention_id") == intention_id and r.get("status") in _OPEN_STATUSES:
                r["status"]       = STATUS_COMPLETED
                r["last_touched"] = time.time()
                _save(records)
                return True
    return False


def abandon(intention_id: str, reason: str = "") -> bool:
    """Mark an intention ABANDONED."""
    with _LOCK:
        records = _load()
        for r in records:
            if r.get("intention_id") == intention_id and r.get("status") in _OPEN_STATUSES:
                r["status"]          = STATUS_ABANDONED
                r["deferred_reason"] = reason
                r["last_touched"]    = time.time()
                _save(records)
                return True
    return False


# ── Read API ──────────────────────────────────────────────────────────────────

def open_intentions() -> list[Intention]:
    """Return all ACTIVE + DEFERRED + RESUMED intentions, sorted by priority desc."""
    records = _load()
    intentions = _records_to_intentions(records)
    return sorted(
        [i for i in intentions if i.status in _OPEN_STATUSES],
        key=lambda i: -i.priority,
    )


def deferred_intentions() -> list[Intention]:
    """Return only DEFERRED intentions."""
    return [i for i in open_intentions() if i.status == STATUS_DEFERRED]


def relevant_to_turn(turn_text: str, max_results: int = 2) -> list[Intention]:
    """
    Find deferred intentions whose relevance_keywords match the current turn text.
    Returns up to max_results, sorted by priority.

    Used to surface "you had an unfinished thread about X" during a relevant turn.
    """
    text_lower = turn_text.lower()
    matches: list[tuple[float, Intention]] = []
    for intention in deferred_intentions():
        score = 0.0
        for kw in intention.relevance_keywords:
            if kw.lower() in text_lower:
                score += 1.0
        if score > 0:
            matches.append((score * intention.priority, intention))
    matches.sort(key=lambda x: -x[0])
    return [m[1] for m in matches[:max_results]]


def intentions_prompt_block(turn_text: str = "", max_open: int = 3) -> str:
    """
    Build a prompt block showing eLo its open intentions.
    Returns "" if nothing open (never blocks the turn).

    - ACTIVE intentions: eLo is currently working on these
    - DEFERRED: held for later — check if relevant to this turn
    """
    try:
        open_i = open_intentions()
        if not open_i:
            return ""

        relevant = relevant_to_turn(turn_text) if turn_text else []
        relevant_ids = {i.intention_id for i in relevant}

        lines = ["[OPEN INTENTIONS — unfinished threads eLo is holding]"]
        count = 0
        for intention in open_i[:max_open]:
            marker = " ← RELEVANT TO THIS TURN" if intention.intention_id in relevant_ids else ""
            lines.append(f"  • {intention.as_prompt_line()}{marker}")
            count += 1

        if len(open_i) > max_open:
            lines.append(f"  … and {len(open_i) - max_open} more deferred")

        return "\n".join(lines)
    except Exception as exc:
        _log.warning("intentions_prompt_block failed (non-fatal): %s", exc)
        return ""


# ── WO-INTENTIONS-001: vault persistence ─────────────────────────────────────

def persist_active_intentions_to_vault() -> str | None:
    """
    WO-INTENTIONS-001: write current active + deferred intentions to vault so they
    survive across sessions. Called at session close (server.py shutdown) and
    whenever the intentions list changes significantly.

    Returns the vault spot code on success, None if nothing to persist or on error.
    """
    try:
        open_list = open_intentions()
        if not open_list:
            return None
        lines = []
        for intent in open_list:
            lines.append(f"[{intent.status}] (p={intent.priority}) {intent.content}")
            if intent.context:
                lines.append(f"  context: {intent.context[:120]}")
        body = "\n".join(lines)
        summary = f"active_intentions: {len(open_list)} open — {open_list[0].content[:80]}"
        from memory.memory_faculty import MemoryFaculty, MemoryCandidate
        result = MemoryFaculty().submit(MemoryCandidate(
            source_faculty="intentions",
            content=body,
            proposed_type="semantic",
            proposed_weight=6,
            significance=0.72,
            project="general",
            summary=summary[:200],
            tags=("active_intentions", "INTERNAL"),
            epistemic_class="canonical",
            source_type="INTERNAL",
            author="elo",
        ))
        return result.get("spot")
    except Exception as exc:
        _log.warning("persist_active_intentions_to_vault failed (non-fatal): %s", exc)
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_keywords(text: str) -> list[str]:
    """Extract simple keywords from intention text for relevance matching."""
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "and",
                 "in", "that", "it", "for", "on", "with", "this", "we", "elo",
                 "i", "you", "what", "how", "can", "do", "did", "be", "about"}
    words = [w.strip(".,?!:;\"'()[]") for w in text.lower().split()]
    keywords = [w for w in words if len(w) > 3 and w not in stopwords]
    return list(dict.fromkeys(keywords))[:8]
