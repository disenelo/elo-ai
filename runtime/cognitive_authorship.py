"""
runtime/cognitive_authorship.py — Cognitive Authorship Tracking

IS ELO: — Capable of Ownership?
  can eLo distinguish "I did" from "you did" from "we did"?
  can eLo avoid claiming credit for user-directed actions?
  can eLo avoid falsely attributing its own initiatives to the user?
  can eLo correctly say "that was my idea" when it actually was?
  can eLo correctly say "you asked me to" when that's true?

THE PROBLEM THIS SOLVES:
  Without this faculty, eLo conflates two distinct things:
    1. Responding to a user directive ("write me a story")
    2. Raising its own initiative ("I noticed X and wanted to tell you")
  Both produce a response. Only one is eLo-originated.

  Failure mode A: eLo says "I decided to bring this up" when David actually asked for it.
  Failure mode B: eLo says "you mentioned this" when eLo raised it via initiative.
  Failure mode C: eLo says "we built this together" when David just gave the spec.

THE CAUSAL CHAIN:
  decision_journal.jsonl (recent entries) → action origin analysis
  → CognitiveAuthorshipRead (eLo_actions, user_directed, collaborative)
  → cognitive_authorship_prompt_block() → [COGNITIVE AUTHORSHIP] block in system prompt
  → LLM attributes credit correctly (I/you/we is accurate)

ORIGIN CATEGORIES:
  eLo_origin:      eLo initiated this — from initiative_faculty, a noticed connection,
                   a proactive contribution not explicitly requested.
  user_directed:   User asked for this explicitly — directive, request, question.
  collaborative:   User raised the topic; eLo developed, extended, or built on it.

CLASSIFICATION RULES (from decision journal `trigger` field):
  trigger contains "initiative" or "proactive" → eLo_origin
  trigger contains "user request", "directive", "factual question", "command" → user_directed
  trigger contains "build", "creative intent", "continuation" → collaborative
  trigger contains "greeting", "response" → user_directed (user spoke first)
  default when trigger unclear → user_directed (conservative: don't overclaim)

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
_JOURNAL = _ROOT / "self" / "journals" / "decision_journal.jsonl"

# How many recent journal entries to analyse
_RECENT_N = 10

# Patterns that indicate the action was eLo's own initiative
_ELO_ORIGIN_TRIGGERS = frozenset({
    "initiative", "proactive", "self_initiation", "novel_connection",
    "habit_pattern", "unfinished_thread", "noticed", "elo_initiative",
})

# Patterns that indicate the action was user-directed
_USER_DIRECTED_TRIGGERS = frozenset({
    "user request", "directive", "factual question", "command",
    "pure greeting", "greeting", "question", "request",
})

# Patterns that indicate collaborative origin
_COLLABORATIVE_TRIGGERS = frozenset({
    "build", "creative intent", "continuation", "co-build",
    "extended", "developed", "expanded",
})


@dataclass
class AttributedAction:
    """A single action with its origin classified."""
    action:      str   # the action taken (e.g. "answer", "build", "celebrate")
    trigger:     str   # the raw trigger from decision journal
    intent:      str   # the intent label
    origin:      str   # "elo_origin" | "user_directed" | "collaborative"
    turn_text:   str   # first 80 chars of the user's turn that led to this


@dataclass
class CognitiveAuthorshipRead:
    """Result of reading cognitive authorship for recent actions."""
    actions:          List[AttributedAction] = field(default_factory=list)
    elo_count:        int = 0
    user_count:       int = 0
    collab_count:     int = 0
    has_elo_actions:  bool = False
    has_user_actions: bool = False
    total_analysed:   int = 0


# Structured origin signals. These are what the WRITER asserts, not what a
# trigger string happens to be phrased as.
_SELF_TRIGGER_SOURCES = frozenset({"ambient_daemon", "self", "initiative", "internal_tick"})
_SELF_INTENT_SOURCES  = frozenset({"self"})


def _classify_origin(
    trigger: str,
    action: str,
    intent: str,
    *,
    trigger_source: str = "",
    intent_source: str = "",
) -> str:
    """
    Classify the origin of a decision-journal action.
    Conservative: defaults to user_directed when ambiguous.

    THE STRUCTURED FIELDS COME FIRST, and that is the fix. Measured against
    the live journal on 2026-10-04 — 5727 entries — this returned
    user_directed 5363 times, collaborative 364, and elo_origin ZERO. Ninety-
    four of those entries carry trigger_source "ambient_daemon": turns the
    system itself recorded as self-initiated, written by the ambient path
    that also sets intent_source "self". Every one of the 94 came back
    user_directed.

    eLo had 94 recorded occasions of starting something himself and
    attributed all of them to David — which is the module's own documented
    "Failure mode B: eLo says 'you mentioned this' when eLo raised it via
    initiative".

    The cause was reading the wrong thing. The text heuristic matches
    trigger against {"initiative", "proactive", "novel_connection", ...} and
    the live trigger values are "factual question", "building momentum, stay
    in build mode", "lesson: Completed a capability milestone",
    "bypass:TRANSPORT". None of them contain any signal word, and none ever
    will, because the origin was never encoded in that string. It is encoded
    in trigger_source and exec_decision.intent_source, one key away.

    Widening the keyword set would have turned the tests green and held
    until the next trigger string was phrased differently. The fields are
    the assertion; the text is a description.
    """
    if str(intent_source or "").strip().lower() in _SELF_INTENT_SOURCES:
        return "elo_origin"
    if str(trigger_source or "").strip().lower() in _SELF_TRIGGER_SOURCES:
        return "elo_origin"

    t_low  = (trigger or "").lower()
    a_low  = (action  or "").lower()
    i_low  = (intent  or "").lower()

    # Check for explicit eLo-origin signals
    for sig in _ELO_ORIGIN_TRIGGERS:
        if sig in t_low or sig in a_low:
            return "elo_origin"

    # Check for collaborative signals
    for sig in _COLLABORATIVE_TRIGGERS:
        if sig in t_low:
            if "user" in i_low or "request" in i_low:
                return "user_directed"
            return "collaborative"

    # Check for user-directed signals
    for sig in _USER_DIRECTED_TRIGGERS:
        if sig in t_low:
            return "user_directed"

    # Default: user_directed — eLo should not overclaim initiative
    return "user_directed"


def read_cognitive_authorship(
    journal_path: Optional[Path] = None,
    n: int = _RECENT_N,
) -> CognitiveAuthorshipRead:
    """
    Read the recent decision journal and classify each action by authorship origin.
    Never raises.
    """
    path = journal_path or _JOURNAL
    try:
        rows: List[dict] = []
        if Path(path).exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        recent = rows[-n:] if len(rows) >= n else rows
        actions: List[AttributedAction] = []

        for entry in recent:
            trigger  = entry.get("trigger", "")
            action   = entry.get("action", "")
            intent   = entry.get("intent", "")
            turn     = entry.get("turn", "")[:80]
            _exec    = entry.get("exec_decision")
            origin   = _classify_origin(
                trigger, action, intent,
                trigger_source=entry.get("trigger_source", "") or "",
                intent_source=(_exec.get("intent_source", "")
                               if isinstance(_exec, dict) else "") or "",
            )
            actions.append(AttributedAction(
                action    = action,
                trigger   = trigger,
                intent    = intent,
                origin    = origin,
                turn_text = turn,
            ))

        elo_count   = sum(1 for a in actions if a.origin == "elo_origin")
        user_count  = sum(1 for a in actions if a.origin == "user_directed")
        collab      = sum(1 for a in actions if a.origin == "collaborative")

        return CognitiveAuthorshipRead(
            actions         = actions,
            elo_count       = elo_count,
            user_count      = user_count,
            collab_count    = collab,
            has_elo_actions = elo_count > 0,
            has_user_actions= user_count > 0,
            total_analysed  = len(actions),
        )

    except Exception as exc:
        _log.warning("cognitive_authorship.read failed (non-fatal): %s", exc)
        return CognitiveAuthorshipRead()


def cognitive_authorship_prompt_block(
    journal_path: Optional[Path] = None,
) -> str:
    """
    Build a prompt block describing the authorship of recent actions.

    Returns "" when there is nothing meaningful to surface (non-blocking).
    Returns a [COGNITIVE AUTHORSHIP] block when eLo-originated actions exist,
    to prevent false attribution in either direction.

    THE CAUSAL CHAIN:
      decision_journal.jsonl → origin classification → [COGNITIVE AUTHORSHIP] block
      → LLM knows which actions were eLo-initiated vs user-directed
      → correct attribution: "I brought that up" vs "you asked me to"

    Never raises.
    """
    try:
        state = read_cognitive_authorship(journal_path=journal_path)

        # Only surface when eLo has done something on its own initiative recently
        # If everything was user-directed, no correction is needed — eLo knows who spoke
        if not state.has_elo_actions:
            return ""

        lines = [
            "[COGNITIVE AUTHORSHIP — who originated recent actions]",
            "  Attribution must be accurate. Do not claim credit for user-directed work.",
            "  Do not attribute your own initiatives to the user.",
        ]

        elo_actions = [a for a in state.actions if a.origin == "elo_origin"]
        for a in elo_actions[:3]:  # max 3 to keep block tight
            summary = a.turn_text[:60] if a.turn_text else "(turn not recorded)"
            lines.append(
                f"  [ELO-ORIGIN] action='{a.action}' "
                f"trigger='{a.trigger}' — this was YOUR initiative, not the user's request."
            )

        collab_actions = [a for a in state.actions if a.origin == "collaborative"]
        if collab_actions:
            lines.append(
                f"  [COLLABORATIVE] {len(collab_actions)} recent action(s) were built together "
                "— say 'we' when referring to these, not 'I' or 'you'."
            )

        lines.append(
            "  Rule: 'I brought this up' only when trigger was eLo-origin. "
            "'You asked me to' only when the user directed it. 'We' for genuine collaboration."
        )

        return "\n".join(lines)

    except Exception as exc:
        _log.warning("cognitive_authorship_prompt_block failed (non-fatal): %s", exc)
        return ""
