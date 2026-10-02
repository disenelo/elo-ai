"""
WO-002: Per-session conversational state tracker.

Tracks current_subject, active_thread, and recent_referents across turns.
Pure Python — no LLM call, no I/O. Maintained in-memory; dies with the session.

This is NOT a database. It does NOT persist across sessions.
It is a rolling buffer of the last N turns, indexed by session_id.

WO-002 changes:
  - _Turn gets response_type field (STEP 5)
  - _extract_referents filters DISCOURSE_MARKER tokens (STEP 3)
  - get_context() returns immediate_subject (last turn only) + stale_subjects (4+ turns ago)
  - Recency tiers: immediate (turn -1), recent (turns -2/-3), stale (4+) — STEP 4
  - Thread continuity: requires 3 of last 4 turns on same subject (was 2 of last 3)
"""

import json
import os
import re
import time
from collections import defaultdict

_CONTINUITY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "conversation_continuity.json",
)
_CONTINUITY_MAX_AGE_S = 86400  # 24h — stale after this

from faculties.grounding import entity_classifier as ec

# lightweight stopword filter — enough for subject extraction
_STOPWORDS = frozenset(
    "i me my myself we our ours ourselves you your yours yourself yourselves "
    "he him his himself she her hers herself it its itself they them their theirs "
    "themselves what which who whom this that these those am is are was were be "
    "been being have has had do does did doing a an the and but if or because as "
    "until while of at by for with about against between into through during before "
    "after above below to from up down in out on off over under again further then "
    "once here there when where why how all both each few more most other some such "
    "no nor not only own same so than too very s t can will just don should now "
    "ve re m ll d".split()
)

# max referents to carry forward per turn
_MAX_REFERENTS = 8

# response type constants
RT_NORMAL       = "NORMAL_CONVERSATION"
RT_DIRECT       = "DIRECT_RESPONSE"
RT_PENDING      = "PENDING_MESSAGE"
RT_DIAGNOSTIC   = "DIAGNOSTIC"
RT_SYSTEM       = "SYSTEM"
RT_TOOL_RESULT  = "TOOL_RESULT"

# proper-noun-ish tokens: capitalised mid-sentence (title-case, not sentence-start)
_NAMED_RE = re.compile(r"(?<=[a-z]\s)([A-Z][a-z]{2,})", re.M)


class _Turn:
    __slots__ = (
        "user", "elo", "subject", "referents", "register", "response_type",
        "responding_to", "active_thread_at_response", "response_rationale",
        "ts",
    )

    def __init__(
        self, user, elo, subject, referents, register, response_type, ts,
        responding_to="", active_thread_at_response="", response_rationale="",
    ):
        self.user = user
        self.elo = elo
        self.subject = subject
        self.referents = referents
        self.register = register
        self.response_type = response_type
        self.ts = ts
        self.responding_to = responding_to
        self.active_thread_at_response = active_thread_at_response
        self.response_rationale = response_rationale


class ConversationTracker:
    """
    Maintains a per-session rolling window of recent turns.

    Usage:
        tracker = ConversationTracker()
        tracker.record(session_id, user_msg, elo_response, subject, register, response_type)
        ctx = tracker.get_context(session_id)
    """

    def __init__(self, window: int = 5):
        self._window = window
        # session_id → list of _Turn (oldest first)
        self._sessions: dict[str, list[_Turn]] = defaultdict(list)
        # session_id → active thread label
        self._threads: dict[str, str] = {}
        # session_id → set of currently unresolved thread labels
        self._open_threads: dict[str, list[str]] = defaultdict(list)

    # ─── PUBLIC API ─────────────────────────────────────────────────────────

    def record(
        self,
        session_id: str,
        user_msg: str,
        elo_response: str,
        subject: str,
        register: str,
        response_type: str = RT_NORMAL,
        thread_at_response: str = "",
        rationale: str = "",
    ) -> None:
        """Record a completed turn. Call AFTER eLo has responded."""
        turns = self._sessions[session_id]
        referents = self._extract_referents(user_msg)
        turn = _Turn(
            user=user_msg[:200],
            elo=elo_response[:200],
            subject=subject,
            referents=referents,
            register=register,
            response_type=response_type,
            ts=time.monotonic(),
            responding_to=user_msg[:200],
            active_thread_at_response=thread_at_response,
            response_rationale=rationale,
        )
        turns.append(turn)
        if len(turns) > self._window:
            turns.pop(0)

        # Thread continuity: require 3 of last 4 turns on same subject (stronger than before)
        if subject and len(turns) >= 3:
            recent_subjects = [t.subject for t in turns[-4:]]
            if recent_subjects.count(subject) >= 3:
                self._threads[session_id] = subject
        elif subject and len(turns) >= 2 and turns[-2].subject == subject:
            # Weaker continuity: still update thread if 2 consecutive turns match
            self._threads[session_id] = subject

    def get_context(self, session_id: str) -> dict:
        """
        Return grounding-relevant context for the CURRENT (incoming) message.
        Called at the START of a turn, before record().

        Returns:
            recent_turns         — list of (user, elo) tuples
            recent_referents     — recency-weighted entity list (immediate turn weighted first)
            active_thread        — current thread label if established
            recent_register      — register from last turn
            recent_conversation_state — brief natural-language summary
            unresolved_threads   — open threads
            immediate_subject    — subject from the very last turn (highest recency)
            stale_subjects       — subjects from 4+ turns ago (informational, not active)
        """
        turns = self._sessions.get(session_id, [])
        if not turns:
            return {
                "recent_turns": [],
                "recent_referents": (),
                "active_thread": "",
                "recent_register": "",
                "recent_conversation_state": "",
                "unresolved_threads": (),
                "immediate_subject": "",
                "stale_subjects": (),
            }

        # Immediate: the most recent completed turn
        immediate_turn = turns[-1] if turns else None
        immediate_subject = immediate_turn.subject if immediate_turn else ""

        # Recent: last 3 turns
        recent = turns[-3:]

        # Stale: everything before the last 3 turns
        stale = turns[:-3] if len(turns) > 3 else []
        stale_subjects = tuple(
            dict.fromkeys(t.subject for t in stale if t.subject)
        )

        # Build recent_referents with recency weighting:
        # Turn -1 (immediate) referents are prioritised, then -2, then -3.
        # This prevents stale turns from contaminating the active context.
        recent_referents: list[str] = []

        # Turn -1: immediate (highest priority)
        if immediate_turn:
            for r in immediate_turn.referents:
                if r not in recent_referents:
                    recent_referents.append(r)

        # Turns -2, -3: append if not already present
        for t in reversed(recent[:-1]):  # recent without the last (already processed)
            for r in t.referents:
                if r not in recent_referents:
                    recent_referents.append(r)
            if len(recent_referents) >= _MAX_REFERENTS:
                break

        last_register = recent[-1].register if recent else ""

        # Build a brief natural-language summary of the last 2 turns
        summary_parts = []
        for t in recent[-2:]:
            if t.user:
                summary_parts.append(f"User said: {t.user[:80]}")
            if t.elo:
                summary_parts.append(f"eLo said: {t.elo[:80]}")
        conversation_state = " | ".join(summary_parts)

        return {
            "recent_turns": [(t.user, t.elo) for t in recent],
            "recent_referents": tuple(recent_referents),
            "active_thread": self._threads.get(session_id, ""),
            "recent_register": last_register,
            "recent_conversation_state": conversation_state,
            "unresolved_threads": tuple(self._open_threads.get(session_id, [])),
            "immediate_subject": immediate_subject,
            "stale_subjects": stale_subjects,
        }

    def open_thread(self, session_id: str, thread_label: str) -> None:
        """Mark a conversational thread as open (unresolved)."""
        threads = self._open_threads[session_id]
        if thread_label and thread_label not in threads:
            threads.append(thread_label)
            if len(threads) > 5:
                threads.pop(0)

    def close_thread(self, session_id: str, thread_label: str) -> None:
        """Mark a thread as resolved."""
        threads = self._open_threads[session_id]
        if thread_label in threads:
            threads.remove(thread_label)

    def get_last_turn_rationale(self, session_id: str) -> dict | None:
        """
        Return provenance for the most recent eLo turn, or None if no turns recorded.
        Used by self-reference interception so "why did you say that" resolves against
        stored conversational state rather than retrospective LLM fabrication.

        Returns dict with keys:
            elo_response    — what eLo said (truncated to 200 chars)
            responding_to   — the user message that triggered it
            subject         — grounding subject at response time
            thread          — active thread at response time
            rationale       — assembled rationale string (may be empty)
        """
        turns = self._sessions.get(session_id, [])
        if not turns:
            return None
        last = turns[-1]
        return {
            "elo_response": last.elo,
            "responding_to": last.responding_to,
            "subject": last.subject,
            "thread": last.active_thread_at_response,
            "rationale": last.response_rationale,
        }

    # ─── CONTINUITY PERSISTENCE ─────────────────────────────────────────────
    # WO-CONV-PERSIST-001: serialise/load last-session context so referents
    # and thread state survive a kill+restart.

    def save_continuity(self, session_id: str) -> None:
        """Serialise the last 3 turns of session_id to _CONTINUITY_PATH."""
        try:
            turns = self._sessions.get(session_id, [])
            saved_turns = [
                {
                    "subject":   t.subject,
                    "referents": list(t.referents),
                    "user":      t.user[:200],
                    "elo":       t.elo[:200],
                    "ts_wall":   time.time(),
                }
                for t in turns[-3:]
            ]
            payload = {
                "saved_at":    time.time(),
                "session_id":  session_id,
                "active_thread": self._threads.get(session_id, ""),
                "open_threads":  list(self._open_threads.get(session_id, [])),
                "turns":       saved_turns,
            }
            os.makedirs(os.path.dirname(_CONTINUITY_PATH), exist_ok=True)
            with open(_CONTINUITY_PATH, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_continuity(self, session_id: str) -> bool:
        """
        Prime session_id from _CONTINUITY_PATH if < 24h old.
        Returns True if state was loaded.
        """
        try:
            if not os.path.exists(_CONTINUITY_PATH):
                return False
            with open(_CONTINUITY_PATH, encoding="utf-8") as fh:
                payload = json.load(fh)
            age = time.time() - float(payload.get("saved_at", 0))
            if age > _CONTINUITY_MAX_AGE_S:
                return False
            # Restore turns as lightweight dicts into the session window
            for t in payload.get("turns", []):
                turn = _Turn(
                    user=t.get("user", ""),
                    elo=t.get("elo", ""),
                    subject=t.get("subject", ""),
                    referents=t.get("referents", []),
                    register="",
                    response_type=RT_NORMAL,
                    ts=time.monotonic(),
                )
                self._sessions[session_id].append(turn)
            if len(self._sessions[session_id]) > self._window:
                self._sessions[session_id] = self._sessions[session_id][-self._window:]
            thread = payload.get("active_thread", "")
            if thread:
                self._threads[session_id] = thread
            for ot in payload.get("open_threads", []):
                self.open_thread(session_id, ot)
            return True
        except Exception:
            return False

    # ─── PRIVATE ────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_referents(text: str) -> list[str]:
        """
        Pull candidate referents from user message text.
        Returns up to _MAX_REFERENTS strings — named entities and salient nouns.

        WO-002: DISCOURSE_MARKER tokens are filtered out here.
        Previously "Exactly" and "Safe" would pollute the referent list.
        """
        candidates = []

        # Multi-word entities first (most specific — "robot arm" not just "robot")
        from faculties.grounding.entity_classifier import extract_multiword_entities
        for mw in extract_multiword_entities(text):
            if mw not in candidates:
                candidates.append(mw)

        # Named-ish tokens (title-case mid-sentence) — skip DISCOURSE_MARKERs
        for m in _NAMED_RE.finditer(text):
            w = m.group(1)
            if w.lower() not in _STOPWORDS and w not in candidates:
                if not ec.is_discourse_marker(w):
                    candidates.append(w)

        # Salient nouns (non-stopword, 4+ chars) — skip DISCOURSE_MARKERs
        tokens = re.findall(r"[a-zA-Z']{3,}", text)
        for tok in tokens:
            low = tok.lower()
            if low not in _STOPWORDS and len(low) >= 4 and tok not in candidates:
                if not ec.is_discourse_marker(tok):
                    candidates.append(tok)
            if len(candidates) >= _MAX_REFERENTS:
                break

        return candidates[:_MAX_REFERENTS]


# module-level singleton — one tracker across the whole process lifetime
_tracker = ConversationTracker()


def get_tracker() -> ConversationTracker:
    return _tracker


def reset_session(session_id: str) -> None:
    """Clear all turns for a session (used by /reset endpoint in tests)."""
    _tracker._sessions.pop(session_id, None)


def save_continuity(session_id: str) -> None:
    """WO-CONV-PERSIST-001: Persist last 3 turns to data/conversation_continuity.json."""
    _tracker.save_continuity(session_id)


def load_continuity(session_id: str) -> bool:
    """WO-CONV-PERSIST-001: Prime session from continuity file if < 24h old."""
    return _tracker.load_continuity(session_id)


# ── Self-reference query detection ──────────────────────────────────────────
# When the user asks eLo to explain its own prior statement, intercept before
# the LLM and resolve against stored provenance — no retrospective fabrication.

_SELF_REF_PATTERNS = frozenset((
    "why did you say that",
    "why did you say",
    "what made you say that",
    "what made you say",
    "why that",
    "what do you mean by that",
    "what do you mean",
    "what did you mean",
    "why did you mention that",
    "why did you mention",
    "what was that you said",
    "what were you saying",
    "what did you just say",
    "why did you bring that up",
    "what do you mean by",
    "why say that",
    "what made you bring that up",
    "what did you say about",
))


def is_self_reference_query(text: str) -> bool:
    """Return True if text is asking eLo to explain or recall its own prior output."""
    t = text.strip().lower()
    return any(p in t for p in _SELF_REF_PATTERNS)
