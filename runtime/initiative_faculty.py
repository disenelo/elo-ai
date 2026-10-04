"""
runtime/initiative_faculty.py — Initiative Faculty

IS ELO: — Capable of Initiative?
  can eLo initiate something?
  can he initiate something for a reason?
  can he explain why he initiated it?
  can he initiate something without being explicitly asked?
  can he distinguish useful initiative from interruption?
  can he connect initiative to an active thread?
  can he connect initiative to an unfinished intention?
  can he connect initiative to a recognised pattern?
  can he defer an initiative?

THE DISTINCTION FROM self_initiation.py:
  self_initiation.py = the GATE: may eLo fire a spine turn? (SP-31/SP-32)
  initiative_faculty.py = the COGNITIVE SOURCE: what is the initiative, why, and
                          is it connected to an active thread?

Without this faculty, initiative is only permissioned — not reasoned.
With it, eLo can initiate WITH a reason and a thread connection.

WHAT GENERATES INITIATIVE:
  1. An unfinished intention in temporal_state — work started but not completed
  2. A recurring pattern (habit) that has not been explicitly addressed
  3. A novelty signal on a topic related to an active project
  4. An expectation_tracker surprise that connects to a current thread

WHAT INITIATIVE IS NOT:
  - Interruption: initiative is not appropriate when the conversation is active
  - Distraction: initiative connects to real threads, not random thoughts
  - Compulsion: initiative can be deferred if timing is wrong

THE CAUSAL CHAIN:
  active_intentions (temporal_state) + novelty/habit signals
  → initiative_faculty reads both → generates initiative suggestion with reason
  → [INITIATIVE] block in system prompt
  → LLM can choose to surface the initiative, defer it, or set it aside

Never raises — all exceptions caught and logged.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

_log = logging.getLogger(__name__)

_ROOT    = Path(__file__).parent.parent
_SIGNALS = _ROOT / "data" / "spg_signals.jsonl"


@dataclass
class InitiativeSuggestion:
    """A proposed eLo initiative with its reason and thread connection."""
    initiative_type:  str   # 'unfinished_thread' | 'pattern_connection' | 'curiosity_follow'
    reason:           str   # why this initiative is relevant now
    thread:           str   # which active thread this connects to (empty if none)
    can_defer:        bool = True   # always True — initiative is never forced
    priority:         str  = "low"  # 'low' | 'moderate' | 'high'


@dataclass
class InitiativeRead:
    """Result of reading the initiative state for this turn."""
    suggestions:     List[InitiativeSuggestion] = field(default_factory=list)
    has_suggestions: bool = False
    active_threads:  List[str] = field(default_factory=list)
    total_signals:   int = 0


def _read_intentions_safe() -> tuple[List[str], List[str]]:
    """
    Active and deferred intentions, read through the module that owns them.

    This read its own file — self/intentions.jsonl, parsed as JSONL — while
    memory/intentions.py owns data/intentions.json, a JSON array. Three
    mismatches, not one:

      path     self/intentions.jsonl  vs  data/intentions.json
      format   one object per line    vs  a JSON array
      status   it tested for "PAUSED", which is not one of the five
               statuses, and never tested RESUMED — so an intention eLo
               had deliberately picked back up counted as nothing

    Neither file existed, so both sides read nothing and the disagreement
    never surfaced. It would have, the moment anything wrote one.

    Going through open_intentions() fixes all three at once, because the
    owner handles path, format and vocabulary. Same move as routing
    spg_faculty's claims read through wkg_faculty.all_claims().

    Never raises.
    """
    try:
        from memory.intentions import (
            open_intentions, STATUS_ACTIVE, STATUS_DEFERRED, STATUS_RESUMED,
        )
        active:   List[str] = []
        deferred: List[str] = []
        for i in open_intentions():
            text = str(getattr(i, "content", "") or "").strip()
            if not text:
                continue
            if i.status in (STATUS_ACTIVE, STATUS_RESUMED):
                active.append(text)
            elif i.status == STATUS_DEFERRED:
                deferred.append(text)
        return active, deferred

    except Exception:
        return [], []


def _recent_edge_hints(signals_path: Path, n: int = 10) -> List[str]:
    """Get the last N edge_hints from signals."""
    try:
        rows: List[dict] = []
        if signals_path.exists():
            with open(signals_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return [r.get("edge_hint", "") for r in rows[-n:] if r.get("edge_hint")]
    except Exception:
        return []


def read_initiative_state(signals_path: Optional[Path] = None) -> InitiativeRead:
    """
    Read the current initiative state.

    Generates initiative suggestions when:
    1. There are unfinished active intentions
    2. The recent signal pattern shows curiosity / novelty / challenge
    3. Both together (strongest signal)

    Never raises.
    """
    path = signals_path or _SIGNALS
    try:
        active, deferred = _read_intentions_safe()
        recent_hints = _recent_edge_hints(path)

        # Count total signals
        total = 0
        if Path(path).exists():
            with open(path, encoding="utf-8") as f:
                total = sum(1 for line in f if line.strip())

        suggestions: List[InitiativeSuggestion] = []

        # Source 1: unfinished intentions → eLo could return to them
        if active:
            suggestions.append(InitiativeSuggestion(
                initiative_type = "unfinished_thread",
                reason          = f"There are {len(active)} active intention(s) in progress. "
                                   "One of them may be worth picking up.",
                thread          = active[0] if active else "",
                can_defer       = True,
                priority        = "moderate" if len(active) >= 2 else "low",
            ))

        # Source 2: curiosity / novelty / challenge signal in recent interaction
        engaging_hints = {"challenge", "curiosity", "novelty", "explore"}
        recent_engaging = [h for h in recent_hints if h in engaging_hints]
        if recent_engaging and active:
            suggestions.append(InitiativeSuggestion(
                initiative_type = "curiosity_follow",
                reason          = (
                    f"Recent interaction included '{recent_engaging[-1]}' signal. "
                    "This may connect to an active thread."
                ),
                thread = active[0] if active else "",
                can_defer = True,
                priority  = "moderate",
            ))

        # Source 3: deferred work that could be resumed
        if deferred:
            suggestions.append(InitiativeSuggestion(
                initiative_type = "unfinished_thread",
                reason          = f"{len(deferred)} deferred intention(s) — work that was paused.",
                thread          = deferred[0] if deferred else "",
                can_defer       = True,
                priority        = "low",
            ))

        return InitiativeRead(
            suggestions     = suggestions,
            has_suggestions = len(suggestions) > 0,
            active_threads  = active,
            total_signals   = total,
        )

    except Exception as exc:
        _log.warning("initiative_faculty.read_initiative_state failed: %s", exc)
        return InitiativeRead()


def initiative_faculty_prompt_block(signals_path: Optional[Path] = None) -> str:
    """
    Build a prompt block surfacing initiative suggestions.

    Returns "" when no initiative is warranted (non-blocking).
    Returns an [INITIATIVE] block when suggestions exist.

    IMPORTANT: initiative is always deferrable. The block presents suggestions,
    not commands. eLo decides whether to surface the initiative in the response.

    THE CAUSAL CHAIN:
      active_intentions + signal pattern → initiative_faculty
      → [INITIATIVE] block with reason + thread connection
      → LLM can choose to raise the initiative, defer, or set aside

    Never raises.
    """
    try:
        state = read_initiative_state(signals_path=signals_path)

        if not state.has_suggestions:
            return ""

        # Only surface if there are actual active threads to connect to
        if not state.active_threads:
            return ""

        lines = ["[INITIATIVE — you have the capacity to initiate, not just respond]"]
        lines.append(
            "  These are suggestions, not commands. You decide whether to surface one."
        )
        lines.append(
            "  Rule: initiative connects to real threads. It is not interruption or distraction."
        )

        shown = 0
        for s in state.suggestions[:2]:  # max 2 suggestions per turn
            if not s.thread:
                continue
            lines.append(f"  [{s.initiative_type.upper()}] priority:{s.priority}")
            lines.append(f"    Reason:  {s.reason}")
            lines.append(f"    Thread:  {s.thread[:100]}")
            lines.append(f"    Deferrable: yes — if timing is wrong, set it aside.")
            shown += 1

        if shown == 0:
            return ""

        return "\n".join(lines)

    except Exception as exc:
        _log.warning("initiative_faculty_prompt_block failed (non-fatal): %s", exc)
        return ""
