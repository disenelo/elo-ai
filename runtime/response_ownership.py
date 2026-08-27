"""
runtime/response_ownership.py — eLo response ownership gate.

L3 Convergence Directive 2026-08-27:
  A faculty provides a CANDIDATE RESULT. eLo evaluates it before speaking.
  eLo owns the final response. The model never gets the final word.

Three checks (in priority order):

  1. EXPLICIT CORRECTION HOLD (R-3)
     If David negated an action this turn ("not sending", "never said that"),
     the candidate must not resurrect it. Sentence containing the negated
     claim is dropped and a WARNING logged.

  2. TOOL CLAIM PROVENANCE (R-1)
     If the candidate claims a tool was called ("I searched", "your calendar
     says", "I sent"), but no tool agent actually ran this turn, the claim
     is dropped. A tool claim is only valid when the tool ran.

  3. UNGROUNDED ACTION CLAIM (R-1)
     If the candidate claims eLo completed a verifiable action ("I moved to",
     "I've sent", "already arrived") without a corresponding confirmed event
     (tool agent or movement ACK), the sentence is dropped.

Safety: if every sentence is dropped, the original candidate is returned.
        Silence is worse than an imperfect response; the WARNING still fires.

This module is called once per turn, in server.py, BEFORE _sanitise() and
the pattern-scrub chain. It operates on the same sentence-split as
memory_claim_guard.py and identity_guard.py.
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())

# ── Sentence splitter ─────────────────────────────────────────────────────────
_SENT_RE = re.compile(r"([^.!?…]*[.!?…]+|[^.!?…]+$)", re.DOTALL)

# ── R-3: Explicit correction signals in user input ────────────────────────────
_CORRECTION_SIGNAL = re.compile(
    r"\b("
    r"not sending|not going to send|i('m| am) not sending"
    r"|never said|didn'?t say|did not say|never told|never asked"
    r"|that'?s not what i (said|meant|was saying)"
    r"|i never|stop (doing|sending|saying|talking about)"
    r"|don'?t (send|do|say|mention|bring up)"
    r"|i'?m not (sending|doing|going|making)"
    r"|not doing (any|that|this)"
    r"|you'?re wrong (about that|about this)"
    r"|that'?s (not true|incorrect|wrong)"
    r")\b",
    re.IGNORECASE,
)

# Specific topic patterns that map onto user corrections
_SEND_SIGNAL = re.compile(
    r"\b(send(ing)?|sent|outbound|out to|reach out|email out|message out)\b",
    re.IGNORECASE,
)
_CALENDAR_SIGNAL = re.compile(
    r"\b(calendar|event|schedule|appointment|booking)\b", re.IGNORECASE
)
_MOVEMENT_SIGNAL = re.compile(
    r"\b(mov(e|ing|ed)|navigat|go(ing)?|walk(ing)?|travel)\b", re.IGNORECASE
)

# ── R-1: Tool claim patterns in candidate response ────────────────────────────
_TOOL_CLAIM = re.compile(
    r"\b("
    r"(your |the |my )?calendar (says?|shows?|has|returned|found)"
    r"|i (checked|looked at|read) (your |the )?calendar"
    r"|i searched (for|the|it)"
    r"|search results? (show|say|indicate|found)"
    r"|weather (shows?|says?|is|reads?|reports?)"
    r"|i found the weather"
    r"|i (sent|called|messaged|emailed|notified)"
    r"|i'?ve (sent|called|messaged)"
    r"|i set (a |the )?reminder"
    r"|reminder (is |was )set"
    r"|i (looked it up|looked up|retrieved|fetched)"
    r"|the (api|tool|system|search|database) (returned|said|shows?|gave)"
    r"|i (opened|launched|closed) (the |an? )"
    r")\b",
    re.IGNORECASE,
)

# ── R-1: Ungrounded action claims in candidate response ───────────────────────
_UNGROUNDED_ACTION = re.compile(
    r"\b("
    r"i'?ve? (sent|moved (to|over)|updated|changed|saved|stored|called|messaged)"
    r"|i'?m now (at|in|on|over|near|by)"
    r"|i moved to"
    r"|i'?ve (arrived|landed|got there|made it)"
    r"|sending (it|that|this|now|shortly)"
    r"|already sent"
    r"|just sent"
    r"|i'?ll send (it|that|this) now"
    r")\b",
    re.IGNORECASE,
)


def _extract_correction_topics(raw_input: str) -> set[str]:
    """Return the set of action topics the user explicitly negated this turn."""
    topics: set[str] = set()
    if not _CORRECTION_SIGNAL.search(raw_input):
        return topics
    if _SEND_SIGNAL.search(raw_input):
        topics.add("send")
    if _CALENDAR_SIGNAL.search(raw_input):
        topics.add("calendar")
    if _MOVEMENT_SIGNAL.search(raw_input):
        topics.add("movement")
    if not topics:
        topics.add("general")  # general negation — flag all action claims
    return topics


def check_candidate(
    candidate: str,
    raw_input: str,
    tool_agent: str = "",
    move_ack_confirmed: bool = False,
) -> str:
    """
    Evaluate the LLM candidate result against current intent and evidence.

    Args:
        candidate:          Raw LLM output (before sanitise/scrubs).
        raw_input:          David's actual words this turn (not enriched).
        tool_agent:         The tool agent that ran this turn (empty = no tool).
        move_ack_confirmed: True if a movement ACK was received this turn.

    Returns:
        Cleaned response. Original returned if every sentence is dropped
        (safety: never silence eLo entirely, but WARNING fires).
    """
    if not candidate or not candidate.strip():
        return candidate

    corrections = _extract_correction_topics(raw_input)
    sentences = _SENT_RE.findall(candidate)
    kept: list[str] = []
    any_dropped = False

    for sent in sentences:
        drop = False
        reason = ""

        # Check 1: explicit correction hold
        if corrections:
            if "send" in corrections and _SEND_SIGNAL.search(sent):
                drop = True
                reason = "correction-hold/send: user negated send-action this turn"
            elif "calendar" in corrections and _CALENDAR_SIGNAL.search(sent):
                drop = True
                reason = "correction-hold/calendar: user negated calendar claim this turn"
            elif "movement" in corrections and _MOVEMENT_SIGNAL.search(sent):
                drop = True
                reason = "correction-hold/movement: user negated movement this turn"
            elif "general" in corrections and _UNGROUNDED_ACTION.search(sent):
                drop = True
                reason = "correction-hold/general: general negation, candidate asserts action"

        # Check 2: tool claim provenance
        if not drop and _TOOL_CLAIM.search(sent) and not tool_agent:
            drop = True
            reason = "tool-provenance: candidate claims tool result but no tool ran this turn"

        # Check 3: ungrounded action claims
        if not drop and _UNGROUNDED_ACTION.search(sent):
            if not tool_agent and not move_ack_confirmed:
                drop = True
                reason = "ungrounded-action: completed-action claim without tool or movement ACK"

        if drop:
            _log.warning(
                "response_ownership: dropped sentence [%s] | %r",
                reason, sent[:120],
            )
            any_dropped = True
        else:
            kept.append(sent)

    if not kept:
        if any_dropped and corrections:
            # Correction-hold caused all drops. Returning the original would
            # just re-assert what David explicitly negated — never do that.
            # A grounded minimal response is better than contradiction.
            _log.warning(
                "response_ownership: ALL sentences dropped by correction-hold. "
                "Returning grounded fallback. candidate=%r", candidate[:200],
            )
            return "Understood."
        # Other checks caused all drops — return original to avoid silence.
        _log.warning(
            "response_ownership: ALL sentences dropped (no correction active) — "
            "returning original to avoid silence. candidate=%r", candidate[:200],
        )
        return candidate

    result = "".join(kept).strip()
    return result if result else candidate
