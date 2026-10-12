"""
faculties/metacognition/deferred_threads.py — something set down is not the
same as something dropped.

Builder 2 brief, two NO verdicts:

    capable of deferring something without losing it?  NO  "No deferral store."
    capable of recovering unfinished thoughts?         NO  "No deferred_threads
                                                            store — your WO."

There are TWO deferral stores and neither has ever held anything.

    EloSelfState.open_threads            read by spine.py:1264, value []
    conversation_tracker._open_threads   filled only by restore()

spine turns the first into has_deferred_threads, and executive_context:281
uses that to prefer "reflect" — pick up the open thread. It has been False on
every turn eLo has ever taken, so that preference has never once fired. The
tracker's own store is worse: open_thread() is called from exactly one place,
restore(), replaying a payload whose open_threads list is always empty. A
closed loop on nothing.

So the gap is not storage, which the brief assumed. It is that nothing ever
DECIDES a thread is unfinished.

WHAT COUNTS AS UNFINISHED, and why this source rather than a new one. eLo
already forms questions and keeps them (5d7de05): a question he formed, stored
and has not yet surfaced is by definition something he set down without
finishing. curiosity_faculty holds them with a surfaced flag and a weight, so
the deferral state is already modelled — it was just never connected to the
field that makes the Executive act on it.

No third store. Two empty ones are the problem; a third would be the same
mistake with better intentions.
"""
from __future__ import annotations

import logging

_log = logging.getLogger("elo.deferred_threads")

# A thread label has to be short — it goes into the Executive's context as a
# reminder of what was set down, not as the thing itself.
_LABEL_MAX = 80

# More than this and "pick up the open thread" stops meaning anything.
MAX_THREADS: int = 5


def _unsurfaced() -> list[dict]:
    try:
        from faculties.curiosity.curiosity_faculty import _load_questions, prioritise
        return prioritise([q for q in _load_questions() if not q.get("surfaced")])
    except Exception as e:
        _log.debug("open questions unreadable (non-fatal): %s", e)
        return []


def _label(q: dict) -> str:
    text = str(q.get("text", "") or "").strip()
    return text[:_LABEL_MAX] if text else str(q.get("topic", "") or "")[:_LABEL_MAX]


def current() -> list[str]:
    """
    The threads eLo has set down and not picked up, most significant first.

    Empty is an honest answer and the common one — it means nothing was
    deferred, not that deferral is broken.
    """
    return [l for l in (_label(q) for q in _unsurfaced()) if l][:MAX_THREADS]


def records(include_resolved: bool = False) -> list[dict]:
    """
    Full thread records, in the shape WO-B2-0014 asks for.

    NO THIRD STORE. The card asks for `faculties/deferred_threads.json` with
    thread_id / summary / reason / created_at / session_id / status. Five of
    those six already exist on the curiosity question that IS the deferred
    thread:

        thread_id  <- question_id        created_at <- ts
        summary    <- text               status     <- surfaced
        reason     <- reason             session_id <- (absent)

    This module's whole argument is that the gap was never storage — it was
    that nothing ever DECIDED a thread was unfinished. Two empty stores were
    the problem; a third would be the same mistake with better intentions, and
    a question could then be open in one place and closed in the other.

    So this reads the one store that holds them and returns the card's shape.

    `session_id` is "" and will stay "" until it is captured at the write
    site, which is `faculties/curiosity/` — not Builder 2's seat. Specced to
    Board rather than reached into. An empty string is honest; an invented
    session id would not be.
    """
    out: list[dict] = []
    try:
        from faculties.curiosity.curiosity_faculty import _load_questions
        for q in _load_questions():
            if not isinstance(q, dict):
                continue
            resolved = str(q.get("surfaced", "")).lower() == "true" or q.get("surfaced") is True
            if resolved and not include_resolved:
                continue
            label = _label(q)
            if not label:
                continue
            out.append({
                "thread_id":  str(q.get("question_id") or ""),
                "summary":    label,
                "reason":     str(q.get("reason") or ""),
                "created_at": float(q.get("ts") or 0.0),
                "session_id": "",          # see docstring — not written yet
                "status":     "resolved" if resolved else "active",
            })
    except Exception as e:
        _log.debug("deferred records unreadable (non-fatal): %s", e)
    return out


def relevant_to(text: str, limit: int = 2) -> list[dict]:
    """
    The threads this turn actually reaches for.

    Card 0014's "eLo naturally picks up a deferred thread when relevant
    context appears". Relevance, not availability: surfacing every open thread
    on every turn is how eLo started narrating his own state. Matched on
    shared content words, the same test `pre_thought` uses, so the two cannot
    disagree about what counts as relevant.
    """
    try:
        from faculties.inner_thought.preprocess import _words
    except Exception:
        return []
    asked = _words(text)
    if not asked:
        return []
    hits = []
    for rec in records():
        if asked & (_words(rec["summary"]) | _words(rec.get("reason", ""))):
            hits.append(rec)
        if len(hits) >= limit:
            break
    return hits


def sync_to_self_state() -> list[str]:
    """
    Put them where spine.py already looks.

    spine reads EloSelfState.open_threads and turns it into
    has_deferred_threads, which executive_context reads to prefer "reflect".
    The whole chain exists; this is the first thing to ever write its first
    link.

    Returns what was written. Never raises.
    """
    threads = current()
    try:
        from self.elo_self_model import update as _update

        def _set(state):
            if hasattr(state, "open_threads"):
                state.open_threads = list(threads)
            return state

        _update(_set)
    except Exception as e:
        _log.debug("open_threads not written (non-fatal): %s", e)
        return []

    if threads:
        _log.info("deferred threads carried forward: %d", len(threads))
    return threads


def mark_picked_up(label: str) -> bool:
    """
    A thread returned to is no longer deferred.

    Goes through curiosity_faculty's own mark_surfaced so one question cannot
    be both open there and closed here.
    """
    text = str(label or "").strip()
    if not text:
        return False
    try:
        from faculties.curiosity.curiosity_faculty import _load_questions, mark_surfaced
        for q in _load_questions():
            if str(q.get("text", "") or "").startswith(text[:_LABEL_MAX]):
                mark_surfaced(q.get("text", ""))
                return True
    except Exception as e:
        _log.debug("thread not marked picked up (non-fatal): %s", e)
    return False
