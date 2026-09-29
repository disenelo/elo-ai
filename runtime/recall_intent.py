"""
runtime/recall_intent.py — does this input ask about earlier conversation?

Lives here rather than in server.py so it can be unit-tested without importing
the server, which is run as __main__.
"""
from __future__ import annotations

import re

# The [SESSION LOG] block below is gated on recognising "is this a question
# about what we already said?". That gate was an exact-substring allowlist,
# and a live 5-turn conversation walked straight through the gap in it:
#
#   turn 1  "I'm working on the Chunk assembly sequence for Act 3 today."
#   turn 4  "So what was I working on before that?"
#           -> "I don't have that from this session."
#
# The window held all five turns (confirmed live: /grounding reported
# turns_in_window 5). The list carried "what am i working on" and "what were
# we working on" but not "what WAS i working on", so the log was withheld and
# the model then reported -- honestly and blindly -- that it had nothing.
#
# The allowlist is kept whole; these patterns cover the same intent in the
# forms it missed. Withholding true context the server is already holding is
# the failure mode worth guarding against, and the block ships with its own
# "if it is not in the log, say so honestly" instruction, so a wider trigger
# cannot license invention.

_RECALL_INTENT_PATTERNS = tuple(re.compile(p) for p in (
    r"\bwhat (was|were) (i|we|you)\b",              # what was I working on
    r"\bwhat (did|do|have) (i|we|you) (say|said|tell|mention|talk|discuss)",
    r"\b(before that|earlier|a moment ago|just now|previously|back there)\b",
    r"\blast (time|session|thing|message)\b",
    r"\bwe (were|was) (talking|discussing|working|saying)\b",
    r"\bgo(ing)? wrong with (it|that|them|this)\b",  # anaphoric follow-up
    r"^(and|so|but)\b.{0,60}\b(it|that|them|those)\b.*\?$",
))


def is_recall_query(text: str, phrase_list) -> bool:
    """
    True when the input asks about earlier conversation.

    Substring list first (unchanged, authoritative), then the intent patterns
    for phrasings it does not enumerate.
    """
    low = (text or "").lower()
    if any(p in low for p in phrase_list):
        return True
    return any(rx.search(low) for rx in _RECALL_INTENT_PATTERNS)



