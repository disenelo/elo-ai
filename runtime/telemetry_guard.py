"""
runtime/telemetry_guard.py — internal records must never be spoken.

Board P0 2026-10-05. David's live log caught eLo saying his own Learning Loop
output, in two forms:

    eLo  {'id': 'L-20261005151905', 'lesson_key': '7d20ac65e9f2aa75',
          'statement': 'Partial progress on witness — ...', ...}
    eLo  Partial progress on reflect — check dependencies before next attempt.

The source is closed in 851e3ae — identity_guard no longer substitutes a
lesson record when it scrubs a whole response. This is the second half the
brief asked for: a guard at the surface, so the next internal structure that
finds its way into an output field does not reach David either.

Deliberately NOT a general "looks like data" filter. eLo talks about code and
JSON with David constantly, and a guard that eats a snippet he was asked for
is worse than the leak it prevents. It catches two specific shapes:

  1. A serialised record — the text IS a dict/JSON object carrying the
     internal keys that only telemetry has (id, lesson_key, epistemic_class,
     claim_id...). A fenced code block is left alone; that is eLo showing
     David something on purpose.

  2. A lesson statement — every one is produced by
     reflection_faculty._derive_statement from a fixed f-string template, so
     the templates are matched rather than the vocabulary.

Mixed content loses only the offending sentence. A response that is nothing
but an internal record returns "", which server.py:7775 already handles as a
silent turn with a WARNING and a short truthful beat.
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger("elo.telemetry_guard")

# Keys that only ever appear in eLo's own records. A dict mentioning these is
# telemetry, not conversation.
_INTERNAL_KEYS = (
    "lesson_key", "epistemic_class", "claim_id", "entity_id", "dream_id",
    "spot_code", "memory_origin", "significance_score", "turn_id",
    "experience_id", "signal_type",
)

_KEYED = "|".join(_INTERNAL_KEYS)

# A serialised record: an object literal carrying at least one internal key.
_RECORD_RE = re.compile(
    r"\{[^{}]*['\"](?:" + _KEYED + r")['\"]\s*:",
    re.IGNORECASE | re.DOTALL,
)

# A repr-style record that opens with 'id': and a generated identifier, which
# is the exact live shape: {'id': 'L-20261005151905', ...}
_ID_RECORD_RE = re.compile(r"\{\s*['\"]id['\"]\s*:\s*['\"][A-Z]-\d{6,}", re.DOTALL)

# reflection_faculty._derive_statement templates. Matched by SHAPE, so a
# change to the wording there is caught by the drift test rather than
# silently passing.
_LESSON_RES = (
    re.compile(r"\bPartial progress on \w+\s*[—–-]\s*check dependencies", re.I),
    re.compile(r"\bWhen \w+ meets an obstacle here, adapt the approach", re.I),
    re.compile(r"\bCompleted a \w+ milestone\s*[—–-]\s*reinforce this pattern", re.I),
)

# Fenced code is eLo showing David something deliberately — never stripped.
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)

_SENT_RE = re.compile(r"([^.!?…]*[.!?…]+|[^.!?…]+$)", re.DOTALL)


def _is_internal(fragment: str) -> bool:
    f = fragment.strip()
    if not f:
        return False
    if _ID_RECORD_RE.search(f) or _RECORD_RE.search(f):
        return True
    return any(r.search(f) for r in _LESSON_RES)


def strip_internal_records(text: str) -> str:
    """
    Remove internal records from something about to be said.

    Returns the text unchanged when it holds none, the surviving sentences
    when it is mixed, and "" when the whole thing was telemetry.
    """
    if not isinstance(text, str) or not text.strip():
        return text

    # Protect fenced blocks so a deliberate code sample is never scanned.
    fences: list[str] = []

    def _stash(m: "re.Match") -> str:
        fences.append(m.group(0))
        return f"\x00FENCE{len(fences) - 1}\x00"

    stashed = _FENCE_RE.sub(_stash, text)

    if not _is_internal(stashed):
        return text

    # A serialised record is removed as ONE span, not sentence by sentence.
    # Splitting on "." cuts {'id': ..., 'statement': 'x.', 'scope': 'y'} in
    # half and the tail — "', 'evidence': [], 'scope': 'behaviour'}" — carries
    # no internal key and a real word, so it passed every later check and got
    # spoken. Measured on the live record from David's log.
    if _ID_RECORD_RE.search(stashed) or _RECORD_RE.search(stashed):
        first, last = stashed.find("{"), stashed.rfind("}")
        if first != -1 and last > first:
            span = stashed[first:last + 1]
            if _ID_RECORD_RE.search(span) or _RECORD_RE.search(span):
                stashed = (stashed[:first] + " " + stashed[last + 1:]).strip()

    # Lesson statements are prose and DO come one sentence at a time.
    kept = [s for s in _SENT_RE.findall(stashed) if not _is_internal(s)]
    out = "".join(kept).strip()

    # A record rarely survives sentence-splitting cleanly: splitting on "."
    # cuts {'id': 'L-...', 'statement': 'x.'} mid-structure and leaves scraps
    # like "'}" behind, which match nothing and would be spoken. If what
    # remains holds no actual word, there was no sentence here to save.
    if not re.search(r"[A-Za-z]{2,}", out):
        out = ""

    for i, block in enumerate(fences):
        out = out.replace(f"\x00FENCE{i}\x00", block)

    if out:
        _log.warning(
            "telemetry_guard: stripped an internal record from output; kept %r",
            out[:80],
        )
        return out

    _log.warning(
        "telemetry_guard: output was ENTIRELY an internal record — suppressed: %r",
        text[:120],
    )
    return ""
