"""
runtime/silence_gate.py — IS ELO: Capable of Silence?

    "can eLo decide not to respond?"
    "can eLo recognise when adding another idea would derail the conversation?"
    "can eLo resist the pressure to always produce content?"

"silence" is one of the nine frozen CAL actions. The Executive can choose it,
and a learned preference can elect it (executive.py:443-452). Nothing
downstream ever made eLo quiet.

Traced before writing this:

  - executive.py:704 is the only consumer of action == "silence" in the turn
    path, and it returns a MOVEMENT intent — step_out or idle. A body
    decision, not a speech decision. The response generated and was spoken
    exactly as if the action had been "answer".

  - Even an empty response could not survive. The D-6 guard treats any empty
    response as a failure and substitutes "One sec — that came back empty.
    Ask me again?" So choosing silence would have produced a sentence
    apologising for having nothing to say.

D-6 already distinguishes DELIBERATE emptiness from accidental emptiness —
repetition suppression is allowed to stay quiet. Deliberate silence is the
second legitimate reason, and this module is what lets D-6 tell them apart.

HONEST LIMIT: the response is suppressed at the output boundary, so the
backend still generates text that is then discarded. Observably eLo says
nothing, which is what the list asks. Architecturally that is suppression,
not abstention — gating the generation itself needs a seam earlier in the
turn than this, and that is a larger change in a handler two seats are
editing. Recorded rather than quietly called done.
"""
from __future__ import annotations

import logging

_log = logging.getLogger(__name__)

# FREEZE_V1_LOCK §5 — the nine, verbatim. Exactly one of them is silence.
_CAL_ACTIONS = ("answer", "build", "connect", "celebrate", "reflect",
                "ground", "challenge", "witness", "silence")

SILENT_ACTION = "silence"

# Mirrors runtime.response_gate.last_was_repetition_suppression(): a flag the
# output boundary sets and D-6 reads, so "chose not to speak" is reachable
# from a place that only sees an empty string.
_last_was_deliberate_silence = False


def is_deliberate_silence(action: str) -> bool:
    """True when the Executive chose not to speak."""
    return str(action or "").strip().lower() == SILENT_ACTION


def mark_silence(active: bool = True) -> None:
    """Record that this turn's emptiness was chosen, not failed."""
    global _last_was_deliberate_silence
    _last_was_deliberate_silence = bool(active)


def last_was_deliberate_silence() -> bool:
    return _last_was_deliberate_silence


def fallback_for_empty_response(
    action: str,
    *,
    was_repetition_suppression: bool = False,
) -> str | None:
    """
    What D-6 should do with an empty response.

    None  → let it stand; the emptiness is intentional.
    str   → the honest fallback; the emptiness is a failure and must not pass
            silently, because a turn that LOOKS silent after a real question
            is the Rule 1 alarm D-6 exists for.
    """
    if was_repetition_suppression:
        return None
    if is_deliberate_silence(action):
        _log.info(
            "silence_gate: Executive chose silence — empty response stands, "
            "no fallback, nothing spoken"
        )
        return None
    return "One sec — that came back empty. Ask me again?"
