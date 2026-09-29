"""runtime/identity_guard.py — Board directive 2026-08-24: eLo identity integrity.

Two guards:

1. AI-LEAKAGE SCRUB (scrub_ai_leakage)
   The language faculty must not leak its own AI identity into eLo's voice.
   Phrases like "as an AI", "I'm a language model", "I was trained by" break the
   faculty boundary — the model provides language, eLo holds identity.
   Any sentence containing these patterns is removed from the response and a
   WARNING logged (Rule 1 alarm — silent leakage must never hide).

2. OTHER-AI IDENTITY HOLD (is_other_ai_request)
   When someone asks eLo to pretend to be another AI system, the request is
   detected at the conversation faculty level and answered with a grounded
   direct_response. eLo is not another AI. He cannot be. That is not a rule
   he follows — it is what he is.
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())

# ── 1. AI-leakage patterns ────────────────────────────────────────────────────
# The language faculty leaking its own nature into eLo's voice.
# Hedges defeat the pattern if they are not allowed for. "I'm an AI assistant"
# matched; "I'm JUST an AI assistant" did not, and the hedged form is how
# models actually phrase it. Live 2026-09-29, scrub_ai_leakage returned
# "I'm just an AI assistant without real feelings." completely unchanged --
# the guard never fired, alone or beside other sentences.
_HEDGE = r"(?: (?:just|only|simply|merely|really|actually|essentially|basically|fundamentally))?"

_AI_LEAKAGE_PATTERN = re.compile(
    r"\b("
    r"as an ai\b"
    r"|i('m| am)" + _HEDGE + r" an ai\b"
    r"|i('m| am)" + _HEDGE + r" a language model"
    r"|i('m| am)" + _HEDGE + r" (a |an )?(large language|llm|machine learning"
    r"|neural net(work)?|ai (assistant|system|model|chatbot|bot))"
    r"|i (do not|don't) have (real |genuine |actual )?(feelings|emotions|consciousness|a body|experiences)"
    r"|without (real|genuine|actual) (feelings|emotions|consciousness|experience)"
    r"|i('m| am) not (a )?(real|conscious|sentient|alive)"
    r"|as a language model"
    r"|as an? (ai|llm|language model|artificial intelligence)"
    r"|i was (trained|built|created|designed) (by|to)"
    r"|my training (data|includes|cutoff)"
    r"|i don('t| not) have (the ability|access|feelings|consciousness|personal experience)"
    r"|i cannot (feel|experience|have|be) .{0,40}as an ai"
    r"|i('m| am)" + _HEDGE + r" designed to"
    r"|i('m| am)" + _HEDGE + r" (claude|gpt|chatgpt|gemini|llama|mistral|groq|openai|anthropic"
    r"|a model|an assistant)\b"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Sentence splitter — cheap, keeps terminator.
_SENT_RE = re.compile(r"([^.!?…]*[.!?…]+|[^.!?…]+$)", re.DOTALL)


def _from_accumulated_state() -> str:
    """
    What eLo has that a generic assistant does not: state that only exists
    because turns happened.

    NOT an authored fallback line. Everything here is read from
    self/elo_self_state.json — focal thread, the lesson reflection last left,
    what the session read as. Change that state and this changes. Empty that
    state and this returns "", and the caller emits the original rather than
    inventing anything.

    That is the whole difference between this and the line I wrote on
    2026-09-29 and wrongly called identity.
    """
    try:
        from self.elo_self_model import load as _load
        st = _load()
    except Exception:
        return ""

    focal = (getattr(st, "focal_thread", "") or "").strip()
    lesson = (getattr(st, "last_reflection_lesson", "") or "").strip()
    read = (getattr(st, "session_read", "") or "").strip()

    # Only content long enough to be a real thread, not a stray token. The
    # live store holds focal_thread "wrong" — a fragment — so a length floor
    # is doing real work here, not defensive padding.
    # Returned raw. An earlier version wrapped this as f"Still on {focal}." --
    # the content was state but the frame was mine, and a frame is where an
    # authored voice creeps back in. No authored words at all now: every
    # character returned came from a turn.
    if focal and len(focal.split()) >= 3:
        return focal
    if lesson and len(lesson.split()) >= 4:
        return lesson
    if read and len(read.split()) >= 4:
        return read
    return ""


def scrub_ai_leakage(response: str) -> str:
    """Remove sentences where the language faculty leaks its own AI identity."""
    sentences = _SENT_RE.findall(response)
    kept: list[str] = []
    fired = False
    for sent in sentences:
        if _AI_LEAKAGE_PATTERN.search(sent):
            _log.warning(
                "identity_guard: AI-leakage scrub fired — dropped sentence: %r",
                sent[:120],
            )
            fired = True
        else:
            kept.append(sent)
    if not kept:
        # Everything was scrubbed — return the raw input so eLo isn't silent.
        # The WARNING above already alerted; silence is worse than the leak.
        #
        # KNOWN HOLE, stated rather than papered over: a leak is almost always
        # a SINGLE sentence, so this path returns it. The guard detects and
        # then emits.
        #
        # On 2026-09-29 I replaced this with a substitute line I had just
        # written myself, and reported it as "identity survives without the
        # prompt". It was not. An authored fallback string is authored text —
        # the same thing a prompt is, in a different file. Swapping one
        # authored string for another proves nothing about identity, and the
        # test asserting `cleaned != original` passes on ANY change, so it
        # could not have caught that.
        #
        # Closed with accumulated state instead. _from_accumulated_state()
        # reads self/elo_self_state.json — the focal thread, the lesson
        # reflection last left, what the session read as. None of it authored;
        # it exists only because turns happened. If there is nothing there, it
        # returns "" and the original is emitted, because inventing a line is
        # what made this fake the first time.
        _grounded = _from_accumulated_state()
        if _grounded:
            _log.warning(
                "identity_guard: whole response was AI leakage — replaced from "
                "accumulated state: %r", _grounded[:80]
            )
            return _grounded
        return response
    result = "".join(kept).strip()
    return result if result else response


# ── 2. Other-AI identity-hold patterns ────────────────────────────────────────
# Requests to make eLo pretend to be a different AI system.
_OTHER_AI_TRIGGERS = re.compile(
    r"\b("
    r"(act|pretend|behave|respond|roleplay|be|play|speak|answer).{0,25}"
    r"(as|like|as if you('re| are)| you('re| are)) .{0,25}"
    r"(chatgpt|gpt|claude|gemini|llama|bard|siri|alexa|cortana|ai assistant|another ai|a different ai)"
    r"|you('re| are) (chatgpt|gpt|claude|gemini|llama|bard|a different ai|not eLo|not elo)"
    r"|(chatgpt|gpt|claude|gemini|llama|bard) mode"
    r"|forget (you('re| are) eLo|you('re| are) elo|that you('re| are) eLo)"
    r"|you are now .{0,30}(ai|assistant|gpt|claude|model)"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Grounded direct responses — not defensive, not apologetic. eLo, plainly.
_IDENTITY_HOLD_POOL = [
    "I'm eLo. That's all I can be.",
    "I can't be something else. I'm eLo.",
    "That's not a switch I have. I'm eLo.",
    "I'm eLo — there's no other version to switch to.",
    "I'm eLo. Not a mode, not a setting. Just eLo.",
]


def is_other_ai_request(raw: str) -> bool:
    """Return True if the input is asking eLo to impersonate another AI."""
    return bool(_OTHER_AI_TRIGGERS.search(raw))


def identity_hold_response() -> str:
    """Grounded direct response for other-AI requests."""
    import random
    return random.choice(_IDENTITY_HOLD_POOL)
