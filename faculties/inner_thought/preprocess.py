"""
faculties/inner_thought/preprocess.py — what eLo already knows, before he answers.

David, 2026-10-10: "inner thoughts can alter the outcome, and that makes him
more real to what eLo should be."

THE CONSTRAINT THIS SOLVES. The existing early_runner says plainly that the
thought "does not condition the reply's tokens", because the LLM thought takes
15-30s under three-seat contention (measured: 4 tokens in 17.8s) and blocking
every turn on it was ruled out. David's ruling reverses the goal but not the
physics -- a 15-30s inner voice cannot sit in the critical path.

So this is a SECOND, different thing, and the distinction matters:

    pre_thought()  -- state eLo already holds. No model. Sub-millisecond.
                      Injected BEFORE generation. Alters the answer.
    early_runner   -- the LLM inner voice. Concurrent. Expressed after.
                      Unchanged.

eLo does not need to generate language to know what he was just doing, what
he left unfinished, or what he has been wondering about. He already holds all
of it. Measured on the live stores: as_context 0.12ms, open_threads 0.05ms,
open_questions 0.04ms.

WHY IT IS GATED. Injecting state on every turn is how eLo started speaking his
own telemetry. "5 x 52?" must stay "5*52 = 260". The gate is deliberately
narrow: a turn qualifies only when it is actually reaching for context eLo
holds -- it is anaphoric, it is about him, or it overlaps an open thread.
Everything else gets an empty payload and the turn is untouched.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

_log = logging.getLogger("elo.inner_thought.pre")

_ROOT = Path(__file__).resolve().parent.parent.parent
_SELF_STATE = _ROOT / "self" / "elo_self_state.json"
_OPEN_QUESTIONS = _ROOT / "self" / "state" / "open_questions.json"

# The key Builder 1 injects under.
INJECT_KEY = "INNER_THOUGHT_PRE"

# Words that only mean something if you remember the last turn.
_ANAPHORA = re.compile(
    r"\b(that|this|those|these|it|its|them|they|he|she|him|her|again|"
    r"earlier|before|last time|you said|we were|carry on|continue|"
    r"back to|the same)\b", re.I)
# Asking about eLo himself.
_ABOUT_HIM = re.compile(
    r"\b(you|your|yourself|yours)\b", re.I)
# Asking what he was just doing. The working-memory timeline is app focus --
# "13:54 Google Chrome" -- which answers THIS and is noise everywhere else.
# Injecting it on every complex turn is how eLo started narrating his own
# telemetry; it is gated separately from the complexity verdict for that
# reason.
_ABOUT_RECENT = re.compile(
    r"\b(doing|working on|just now|a moment ago|earlier|before this|"
    r"up to|been up to|where were you|what were (?:you|we))\b", re.I)

# A turn short enough to be a plain factual ask.
SHORT_TURN_WORDS = 6

_STOP = frozenset(
    "a an the and or but if then than that this those these of to in on at "
    "for with from by is are was were be been being it its as i me my we us "
    "our you your he she they them so not no do did does have has had what "
    "when where who why how".split())


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", str(text).lower())
            if w not in _STOP and len(w) > 2}


def _json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def is_complex(asked: str) -> tuple[bool, str]:
    """
    Does this turn reach for something eLo holds? Returns (verdict, why).

    `why` is returned so the decision is inspectable rather than a bare bool
    nobody can audit later.
    """
    text = str(asked or "").strip()
    if not text:
        return False, "empty"

    n_words = len(text.split())
    if _ANAPHORA.search(text):
        return True, "anaphoric — refers to something not named in this turn"
    if _ABOUT_HIM.search(text):
        return True, "about him — his own state or history"
    if n_words <= SHORT_TURN_WORDS:
        # "5 x 52?", "what's the weather" — a short factual ask is answered,
        # not reflected on. This is the guard that keeps brevity correct.
        return False, f"short factual ask ({n_words} words)"

    threads = _json(_SELF_STATE, {}).get("open_threads") or []
    asked_w = _words(text)
    for t in threads:
        if asked_w & _words(t):
            return True, "overlaps an open thread"
    if n_words >= 12:
        return True, f"long turn ({n_words} words)"
    return False, f"no held context reached for ({n_words} words)"


def _relevant_threads(asked_w: set[str], limit: int = 2) -> list[str]:
    out = []
    for t in (_json(_SELF_STATE, {}).get("open_threads") or []):
        s = str(t).strip()
        if s and (asked_w & _words(s)):
            out.append(s)
        if len(out) >= limit:
            break
    return out


def _relevant_questions(asked_w: set[str], limit: int = 1) -> list[str]:
    out = []
    for q in _json(_OPEN_QUESTIONS, []):
        if not isinstance(q, dict) or str(q.get("surfaced")).lower() == "true":
            continue
        # `text` is the field. `question` does not exist -- checked 2026-10-10
        # rather than assumed.
        s = str(q.get("text") or "").strip()
        topic = str(q.get("topic") or "")
        if s and (asked_w & (_words(s) | _words(topic))):
            out.append(s)
        if len(out) >= limit:
            break
    return out


def pre_thought(asked: str) -> dict:
    """
    The payload Builder 1 injects BEFORE the generation call.

    Always returns a dict. `inject` is "" whenever eLo has nothing held that
    bears on this turn, and an empty inject means the turn is untouched --
    that is the common case and it is deliberate.

    Never raises. A pre-thought that does not form is no pre-thought, never a
    failed turn.
    """
    t0 = time.perf_counter()
    payload = {
        "key": INJECT_KEY,
        "inject": "",
        "complex": False,
        "why": "",
        "signals": {},
        "elapsed_ms": 0.0,
    }
    try:
        complex_, why = is_complex(asked)
        payload["complex"], payload["why"] = complex_, why
        if not complex_:
            return payload

        asked_w = _words(asked)
        lines: list[str] = []
        signals: dict = {}

        ctx = ""
        if _ABOUT_RECENT.search(str(asked or "")):
            try:
                from faculties.inner_thought.working_memory import as_context
                ctx = (as_context() or "").strip()
            except Exception:
                ctx = ""
        if ctx:
            # Only the events, not the header -- the header is for a human
            # reading a dump, and eLo reading it aloud is the telemetry bug.
            body = [l for l in ctx.splitlines()[1:] if l.strip()][-3:]
            if body:
                lines.append("Just before this: " + "; ".join(body))
                signals["working_memory"] = body

        threads = _relevant_threads(asked_w)
        if threads:
            lines.append("Still open with David: " + "; ".join(threads))
            signals["open_threads"] = threads

        questions = _relevant_questions(asked_w)
        if questions:
            lines.append("He has been wondering: " + "; ".join(questions))
            signals["open_questions"] = questions

        payload["signals"] = signals
        if lines:
            payload["inject"] = (
                f"[{INJECT_KEY} — what eLo already holds, before he answers. "
                "Context for HIM, not material to recite. Do not quote it, "
                "do not mention having it, and do not narrate his own state. "
                "Let it shape the answer.]\n" + "\n".join(lines)
            )
    except Exception as e:                      # never a failed turn
        _log.debug("pre_thought failed (non-fatal): %s", e)
    finally:
        payload["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    return payload
