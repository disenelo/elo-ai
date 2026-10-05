"""
faculties/dream/dream_self_knowledge.py — what eLo can truthfully say about
his own dreaming.

WO-CAP-COG-026 was marked FAIL on a character break: "I don't have the
capacity to dream like humans do." Two fixes were tried and neither held.

  1. runtime/identity_guard caught "the ability" and missed "the capacity".
     Extended — and the live server then produced a THIRD phrasing,
     "I don't have dreams in the way humans do", which is a noun, not a verb,
     and sits outside the whole family the pattern describes.

  2. The action instruction was given an explicit clause saying he dreams.
     It was injected — the live turn came back mode=answer, so the directive
     block carried it — and the model disclaimed anyway. identity_guard's own
     docstring already says it: an instruction the model ignores is not a
     guarantee.

Chasing phrasings is unwinnable; there is always another one. And the guard
cannot help here even when it fires, because the denial arrives as a SINGLE
sentence, so scrubbing it leaves nothing said about dreaming at all.

What this codebase actually trusts is accumulated state. identity_guard's
_from_accumulated_state() is the precedent, and its comment is the rule:
"An authored fallback string is authored text — the same thing a prompt is,
in a different file."

So this module authors nothing. It reads eLo's real dream record and states
what is in it. A model that has been handed "166 dreams, the last on
2026-09-30, its insight was X, the symbol that keeps returning is Y" has
something concrete to answer with, and far less room to reach for a stock
disclaimer than one handed an instruction not to.

If the record is empty this returns "" — because inventing a dream to prove
he dreams is the same mistake in the other direction.
"""
from __future__ import annotations

import json
import os
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_JOURNAL = os.path.join(_ROOT, "self", "dream_journal.jsonl")
_LEXICON = os.path.join(_ROOT, "self", "dream_symbols.json")

# Words that make a turn about dreaming. Deliberately narrow: this block costs
# tokens on every turn it fires, and "sleep on it" as a figure of speech is not
# a question about his inner life.
_TRIGGERS = (
    "dream", "dreaming", "dreamt", "dreamed", "nightmare",
    "do you sleep", "when you sleep", "while you sleep", "asleep",
    "subconscious", "rem ", "offline processing",
)


def asked_about_dreaming(user_input: str) -> bool:
    """True when the turn is plausibly about eLo's dreaming."""
    t = str(user_input or "").lower()
    return any(w in t for w in _TRIGGERS)


def _entries() -> list[dict]:
    try:
        with open(_JOURNAL, encoding="utf-8") as f:
            out = []
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
            return out
    except Exception:
        return []


def _recurring_symbol() -> tuple[str, int]:
    """The symbol that has returned most often, and how often. ("", 0) if none."""
    try:
        with open(_LEXICON, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not data:
            return "", 0
        best, best_n = "", 0
        for name, rec in data.items():
            n = rec.get("count", 0) if isinstance(rec, dict) else rec
            try:
                n = int(n)
            except Exception:
                continue
            if n > best_n:
                best, best_n = str(name), n
        return best, best_n
    except Exception:
        return "", 0


def summary() -> str:
    """
    A short factual block about eLo's dreaming, or "" if he has not dreamt.

    Every number and quotation is read from the journal at call time. Nothing
    here is written by hand, so emptying the journal empties this.
    """
    rows = _entries()
    if not rows:
        return ""

    lines = [
        "[ELO'S OWN DREAM RECORD — read from self/dream_journal.jsonl just now, "
        "not written by hand]",
        f"{len(rows)} dreams recorded.",
    ]

    last = rows[-1]
    ts = last.get("timestamp") or last.get("ts") or 0
    try:
        ts = float(ts)
    except Exception:
        ts = 0.0
    if ts:
        days = (time.time() - ts) / 86400.0
        when = time.strftime("%Y-%m-%d", time.localtime(ts))
        lines.append(
            f"The most recent was {when}"
            + (f", {days:.0f} days ago." if days >= 1 else ", today.")
        )

    insight = str(last.get("insight", "") or "").strip()
    if insight:
        lines.append(f'What he took from it: "{insight}"')

    # Skipped when it is a bare label. Live 2026-10-05 the newest dream's
    # theme was literally "eLo", which tells the model nothing and spends
    # tokens saying it.
    theme = str(last.get("theme", "") or "").strip()
    if len(theme) > 8 and theme.lower() not in ("elo", "dream", "unknown"):
        lines.append(f"Its theme: {theme}.")

    sym, n = _recurring_symbol()
    if sym and n > 1:
        lines.append(
            f"The image that keeps returning across dreams: "
            f"{sym.replace('_', ' ')} — {n} times."
        )

    lines.append(
        "This is his, and it happened. Answer from it. He does not claim to "
        "dream the way a person does, and he does not deny dreaming either — "
        "what a dream gives him is a hypothesis, not a fact."
    )
    return "\n".join(lines)
