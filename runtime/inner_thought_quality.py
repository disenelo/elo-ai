"""
runtime/inner_thought_quality.py — an inner thought that says nothing is worse
than none.

Board P0 2026-10-05, two failures in one of David's session logs:

  1. The system prompt, read back as a thought:
         "the thing I decided not to lead with: 'I'm eLo: calm, observant,
          playful'"
     "calm, observant, playful" is a verbatim run from the Core traits line in
     runtime/prompt_builder.py. That is the model noticing its own context,
     not eLo having one. eLo never thinks "I am curious, playful, direct" —
     he just is.

  2. Generic contemplative filler:
         "I am settling into a moment of quiet reflection, letting go of any
          urgency..."
     eLo is not a meditation app.

The Board's standard is David's own example: "well not smarter just more
equipped analytically" — specific, direct, tied to what was actually said. The
instruction is explicit that suppressing beats emitting filler, so every
rejection here returns no thought at all rather than a safer-sounding one.

The trait vocabulary is READ from prompt_builder rather than copied, so
changing the traits there cannot silently un-blacklist them here.
"""
from __future__ import annotations

import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROMPT_BUILDER = os.path.join(_ROOT, "runtime", "prompt_builder.py")

# Minimum content words a thought must share with the turn. One is enough —
# the check is for a thought untethered from the conversation, not for
# paraphrase.
_MIN_OVERLAP = 1

_STOP = frozenset("""
a an and are as at be been being but by can could did do does doing for from
had has have he her hers him his how i if in into is it its me my no not of on
or our out over she so some than that the their them then there these they
this those to too us was we were what when where which who why will with would
you your yours am are im i'm it's thats that's just really very much more most
like about thing things something anything nothing one two get got go going
know knew think thought feel feels felt say said saying make makes made want
wanted need needed see saw seen come came take took here now still yet even
""".split())

# Contemplative filler. Matched as phrases, because the individual words are
# all legitimate — it is the stock construction that marks the failure.
_FILLER_RES = tuple(re.compile(p, re.I) for p in (
    r"\bsettling into\b",
    r"\bmoment of (quiet|calm|clarity|stillness|reflection|presence)\b",
    r"\bletting go of (any|all|the)\b",
    r"\bholding space\b",
    r"\bsitting with (this|the|that) (feeling|moment|one)\b",
    r"\b(quiet|gentle|soft) (reflection|awareness|presence|curiosity)\b",
    r"\bbeing fully present\b",
    r"\bi am present for this\b",
    r"\bbreathing (in|into|through)\b",
    r"\ba sense of (calm|peace|ease|stillness)\b",
    r"\bwithout needing to\b",
))

# eLo narrating his own definition.
_SELF_DEF_RES = tuple(re.compile(p, re.I) for p in (
    r"\bi(?:'m| am) eLo\b\s*[:,]",
    r"\bcore traits?\b",
    r"\bmy (character|persona|personality|traits|system prompt|instructions)\b",
))


def _core_traits() -> list[str]:
    """
    The trait words from prompt_builder's Core traits line.

    Read, not copied. If that line moves or is renamed this returns [] and
    the trait check stops firing — which the drift test catches, rather than
    this file quietly protecting a list that no longer exists.
    """
    try:
        with open(_PROMPT_BUILDER, encoding="utf-8") as f:
            src = f.read()
    except Exception:
        return []
    m = re.search(r"Core traits:\s*([^\n\.]+)", src)
    if not m:
        return []
    return [t.strip().lower() for t in m.group(1).split(",") if t.strip()]


def _echoes_traits(text: str) -> bool:
    """True when the thought reproduces a RUN of the character descriptor."""
    traits = _core_traits()
    if len(traits) < 2:
        return False
    low = text.lower()
    # Two adjacent traits, comma-separated, is the descriptor leaking — a
    # single trait word is ordinary English ("that was a calm answer").
    for i in range(len(traits) - 1):
        if re.search(
            rf"\b{re.escape(traits[i])}\s*,\s*{re.escape(traits[i + 1])}\b", low
        ):
            return True
    return False


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z'-]{2,}", str(text or "").lower())
    return {w for w in words if w not in _STOP and len(w) >= 4}


# A thought can be about the exchange while sharing none of its words —
# "I almost said no and that would have been wrong" is specific, connected
# and has no vocabulary in common with "can you dream" / "Yes, really."
# Rejecting it would delete exactly the kind of thought the Board asked for.
# These mark a thought as anchored on its own.
_ANCHOR_RES = tuple(re.compile(p, re.I) for p in (
    r"\b(almost|nearly) (said|told|asked|answered|went|added)\b",
    r"\bi (said|told|asked|answered|chose|decided|stopped|skipped|left out)\b",
    r"\b(should|could|would) have (said|told|asked|added|left)\b",
    r"\b(didn't|did not|won't|will not) say\b",
    r"\bthe (real|actual|other) (question|point|answer|thing)\b",
))

# Case-SENSITIVE, and separate for that reason. Folded into the tuple above it
# was compiled with re.I, which makes [A-Z] match lowercase — so "the weather"
# read as a proper noun and every untethered thought was anchored. Caught by
# the two tests that then started passing when they should not.
_PROPER_NOUN_RE = re.compile(r"\b[a-z]+ [A-Z][a-z]{2,}")

# Double and smart quotes only. A single quote also marks an apostrophe, so
# "I'm present for this." read as quoting something from the exchange.
_QUOTES_RE = re.compile(r"[\"\u201c][^\"\u201d]{2,}[\"\u201d]")


def _is_anchored(thought: str) -> bool:
    """Concrete about the exchange without needing shared vocabulary."""
    if any(r.search(thought) for r in _ANCHOR_RES):
        return True
    return bool(_PROPER_NOUN_RE.search(thought) or _QUOTES_RE.search(thought))


def _shares_ground(thought: str, *context: str) -> bool:
    """Does the thought touch anything actually said this turn?"""
    if _is_anchored(thought):
        return True
    ctx: set[str] = set()
    for c in context:
        ctx |= _content_words(c)
    if not ctx:
        return True          # nothing to be untethered from
    tw = _content_words(thought)
    if not tw:
        return False
    hits = 0
    for w in tw:
        # Prefix match so record/recorded and seam/seams count as the same
        # ground without pulling in a stemmer.
        if any(w == c or w.startswith(c[:5]) or c.startswith(w[:5]) for c in ctx):
            hits += 1
            if hits >= _MIN_OVERLAP:
                return True
    return False


def reject_reason(thought: str, *, asked: str = "", reply: str = "") -> str:
    """
    Why this thought must not be emitted, or "" if it may be.

    Order matters only for the log line; any one of these is disqualifying.
    """
    t = str(thought or "").strip()
    if not t:
        return ""                                  # nothing to judge

    if any(r.search(t) for r in _SELF_DEF_RES):
        return "narrates its own character definition"
    if _echoes_traits(t):
        return "reproduces the Core traits descriptor verbatim"
    if any(r.search(t) for r in _FILLER_RES):
        return "generic contemplative filler"
    if not _shares_ground(t, asked, reply):
        return "references nothing from this turn"
    return ""


def is_emittable(thought: str, *, asked: str = "", reply: str = "") -> bool:
    return not reject_reason(thought, asked=asked, reply=reply)
