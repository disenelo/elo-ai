"""
faculties/metacognition/open_question_capture.py — eLo keeps the questions he
forms.

Builder 2 brief, three NO verdicts in a row:

    a system capable of recognising unanswered questions?  NO
    a system capable of retaining unanswered questions?    NO
    a system capable of returning to unanswered questions? NO
    "No unanswered_questions store. inner_thought generates curiosity
     language but does not store questions."

Half of that is wrong, and the half that is wrong is the useful half. The
store exists: faculties/curiosity keeps self/state/open_questions.json with
store_question(), prioritise() and top_question(). server.py:5571 already
READS it to surface a question back to David.

Measured 2026-10-06: the file holds 0 questions, and nothing in production
calls store_question() or detect_gap(). The read side was wired and the write
side never was — so eLo could surface a question he was never able to keep.

Same shape as the rest of today: relay_body_event with no caller, the dream
latch nothing set, significance checked at a gate and discarded. The component
is fine. Nothing feeds it.

This is the feed. A formed inner thought that is a wondering becomes a stored
question, which then returns through the path that already existed.

It does NOT invent a parallel store. One behaviour with two stores is the
mistake this codebase keeps making, and curiosity_faculty's dedupe,
prioritisation and cap are already correct.
"""
from __future__ import annotations

import logging
import re
import time

_log = logging.getLogger("elo.open_question")

# A thought is a wondering when it asks, or when it reaches for something it
# does not have. David's own examples of eLo's voice include both shapes:
# "I wonder how plotters function." and "Skipping this song, huh?"
_WONDER_RES = tuple(re.compile(p, re.I) for p in (
    r"\bi wonder\b",
    r"\bwhat (is|are|was|were|does|do|did|makes?|happens?)\b",
    r"\bhow (do|does|did|is|are|would|come)\b",
    r"\bwhy\b",
    r"\bi (don't|do not|never) know\b",
    r"\bno idea\b",
    r"\bcurious (about|what|how|why)\b",
))

# Words that carry no topic. Shared in spirit with spg_backfill's list, kept
# separate because this one must also drop interrogatives.
_STOP = frozenset("""
a an and are as at be but by can could did do does for from had has have how
i if in into is it its me my no not of on or our so than that the their them
then there these they this those to too us was we were what when where which
who why will with would you your am just really very much more most like about
thing things something anything nothing know knew think thought wonder curious
does doing done idea
""".split())


def is_wondering(thought: str) -> bool:
    """Does this thought leave something open?"""
    t = str(thought or "").strip()
    if not t:
        return False
    if t.endswith("?"):
        return True
    return any(r.search(t) for r in _WONDER_RES)


def topic_of(thought: str) -> str:
    """
    The subject the question is about.

    curiosity_faculty dedupes by topic, so this has to be stable: the same
    wondering twice must not become two questions. Longest content word, which
    is crude but repeatable — and repeatable matters more than clever when it
    is a dedupe key.
    """
    words = [w for w in re.findall(r"[a-z][a-z'-]{2,}", str(thought or "").lower())
             if w not in _STOP]
    return max(words, key=len) if words else ""


def capture(thought: str, *, asked: str = "", weight: int = 5) -> dict | None:
    """
    Store a wondering as an open question. Returns the record, or None.

    Never raises: failing to keep a question must not cost the turn it arrived
    in.
    """
    t = str(thought or "").strip()
    if not t or not is_wondering(t):
        return None

    topic = topic_of(t)
    if not topic:
        return None

    record = {
        "question_id": f"q-{int(time.time() * 1000)}-{abs(hash(topic)) % 9999:04d}",
        "topic": topic,
        "text": t,
        # Marks where it came from. A question eLo formed while thinking is a
        # different thing from one derived from a gap in the knowledge graph,
        # and "returning to it" reads differently for each.
        "reason": "inner_thought",
        "confidence": 0.0,
        "weight": max(1, min(int(weight), 10)),
        "ts": time.time(),
        "surfaced": False,
        "asked": str(asked or "")[:200],
    }

    try:
        from faculties.curiosity.curiosity_faculty import store_question
        store_question(record)
        _log.info("open question kept (%s): %r", topic, t[:80])
    except Exception as e:
        _log.warning("open question not stored (non-fatal): %s", e)
        return None

    return record
