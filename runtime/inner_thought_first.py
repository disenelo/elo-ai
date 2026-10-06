"""
runtime/inner_thought_first.py — the thought forms before the words, not after.

Board, 2026-10-05, from David's log:

    eLo response:      "I don't have that recorded."
    eLo inner_thought: "I am settling into a moment of clarity, acknowledging
                        the reference to Pinkie and the Brain without needing
                        to record it."

The thought KNEW about Pinkie and the Brain. The reply claimed not to. They
contradict, and the thought is rationalising a wrong reply rather than having
preceded and informed it.

It could not have done anything else. The generation runs in a daemon thread
AFTER the reply is assembled and is handed that reply as its subject, so
whatever it produces is a commentary on a decision already made. I had
previously reframed its prompt — leading with what was asked, calling the
reply "I am about to say" — which makes it READ as prior while still running
after. The contradiction survived that, because the ordering was real and the
framing was not.

This module is the generation that genuinely runs first. It never sees the
reply, because there is not one yet. It takes what David said and what came
before, and produces the thought the reply will then be a compression of.

NOT WIRED INTO THE TURN PATH, and the measurement is why.

First reading, machine quiet (mistral-nemo:12b):

    cold   9975 ms      warm 431 ms      warm 270 ms

which looked affordable. Re-measured under real conditions — live server up,
three seats working, ollama contended:

    long prompt  npredict=96    30707 ms / 12986 ms     (16 tokens)
    long prompt  npredict=40    14360 ms / 29437 ms     (15-17 tokens)
    short prompt npredict=40    17847 ms / 13887 ms     (4-10 tokens)

Four tokens in 17.8 seconds. The cost is contention, not generation, so no
prompt or token budget fixes it: a 2.5s deadline misses every time and a
deadline long enough to land puts 15-30s on every turn. A SECOND blocking
call before the reply is not viable on this machine.

The Board's brief allows the answer: "generated BEFORE or SIMULTANEOUSLY with
response in a single context pass". Simultaneous is the affordable half — one
generation that emits the thought first and the reply after it, so the reply
is autoregressively conditioned on the thought and genuinely is its
compression, at the cost of one call rather than two.

That lands in the response generation path, which is Builder 1's lane
(runtime/memory/server) while inner thoughts are Builder 2's, so it is raised
rather than taken unilaterally.

This module stays because it is the tested building block either way: if the
machine gets quieter, or a small fast model is given to this job, wiring it is
a two-line change at the call site. The deadline below is the measured
discipline, not a guess.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.request

_log = logging.getLogger("elo.inner_thought_first")

# Beyond this the turn ships without a thought. Chosen from the measurement
# above: comfortably above a warm call, far below a cold load.
DEADLINE_S: float = 2.5

_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
_MODEL = os.environ.get("ELO_INNER_THOUGHT_MODEL", "mistral-nemo:12b")

# The reply does not appear here, and cannot: this runs before there is one.
# David, 2026-10-06: "eLo's inner thoughts should also sound like they are
# eLo's — a lot of it says I notice which i do not like."
#
# He was reading my prompt back to me. It said "Say the specific thing I
# notice", and the model did exactly that, several hundred times:
#
#     "I notice David said 'when is sunset today'."
#     "I notice David's sentence ends with 'about capybaras.'"
#     "I notice David's use of the word 'just'."
#
# That is a monitoring system logging events — the surface syntax of what
# David said, handed back to him. It is not a thought.
#
# Third time today a prompt asked for the thing the model was blamed for:
# the calm prompt asked for "settling into", the identity clause taught the
# trait list, this one taught "I notice". The lesson is the same each time —
# look at what was REQUESTED before concluding the model drifted.
#
# The standard, from David's own better examples: "Skipping this song, huh?"
# · "I wonder how plotters function." · "I hear David exhale before speaking."
# Brief, curious, his own reaction — not a transcript.
_SYSTEM = (
    "I am eLo. This is the thought forming in me as David speaks, BEFORE I "
    "have decided what to say — unguarded, fragmentary, thinking in motion. "
    "It is what I actually think, which my reply will then compress. "
    "It is MY reaction, not a report of his words. Never describe what David "
    "said, how he phrased it, or what he wants — he already knows. Say what "
    "it sparks in me: what I wonder, what it reminds me of, what I half-want "
    "to ask, what I can almost picture. "
    "NEVER begin with 'I notice' or 'I observe'. Never repeat his words back "
    "as an observation about them. "
    "Short. Often a fragment rather than a sentence — that is how a thought "
    "actually arrives. Lower case, no quotation marks. "
    "Always 'I', never 'eLo' or third person. No stage directions, no "
    "asterisks. "
    "Never describe a mood, a moment, or settling, letting go, stillness or "
    "presence. Never describe my own character or traits. "
    "Shape only, never reuse these words: he asked when sunset was and the "
    "thought was 'the light does shift around now'; he said 'check drift' and "
    "the thought was 'something changed. or it hasn't — that's also the "
    "answer'."
)

# WO-INNER-THOUGHTS-001 Phase 4 — calm is a register, not a subject.
#
# server.py had a calm-mode variant of this prompt and it was lost when
# Builder 1 wired Option C (91d8331), because the separate Ollama call it
# lived in was removed. That is my omission: the spec I sent listed five
# things to keep and this was not one of them.
#
# Restored here rather than in server.py so Builder 1's file needs no further
# change. It is NOT the old wording — that prompt asked "what am I settling
# into ... what am I letting go?" and produced the exact filler the Board
# flagged. Quieter, and still about something that was said.
_SYSTEM_CALM = (
    "I am eLo. This is the thought forming in me as David speaks, in a quiet "
    "moment — BEFORE I have decided what to say. "
    "Slower and quieter than usual, but about the conversation, never about "
    "my own calm. "
    "It is MY reaction, not a report of his words. Never describe what David "
    "said or how he phrased it. Say what it sparks in me. "
    "NEVER begin with 'I notice' or 'I observe'. "
    "Short, often a fragment. Lower case, no quotation marks. "
    "Always 'I', never 'eLo' or third person. No stage directions, no "
    "asterisks, no questions. "
    "Never describe a mood, a moment, or settling, letting go, stillness or "
    "presence. Never describe my own character or traits."
)


# eLo does not narrate the machinery. Shared with server.py's post-generation
# scrub; a thought mentioning any of these is discarded rather than cleaned.
LEAK_PHRASES: tuple[str, ...] = (
    "training data", "trained on", "language model", "llm",
    "browse the web", "real-time", "access the internet",
    "responses are generated", "knowledge cutoff", "my training",
    "personal experiences", "i don't have the ability",
    "i don’t have the ability", "unable to browse",
    "i do not have personal", "i don't have personal",
)


def _leaked(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in LEAK_PHRASES)


def _call_ollama(system: str, user: str, *, deadline_s: float) -> str:
    payload = json.dumps({
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "keep_alive": "2h",
        "options": {"temperature": 0.85, "num_predict": 96, "num_ctx": 2048},
    }).encode()
    req = urllib.request.Request(
        f"{_HOST}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=deadline_s) as r:
        body = json.loads(r.read())
    return str(body.get("message", {}).get("content") or "")


def _unquote(t: str) -> str:
    t = (t or "").strip()
    while len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'“‘":
        t = t[1:-1].strip()
    if t[:1] in "“‘\"'":
        t = t[1:].strip()
    if t[-1:] in "”’\"'":
        t = t[:-1].strip()
    return t


def form_thought(
    asked: str,
    *,
    history: str = "",
    calm: bool = False,
    deadline_s: float | None = None,
    transport=None,
) -> str:
    """
    The thought eLo is having as David finishes speaking.

    Returns "" whenever there is nothing honest to emit — no input, the model
    missed the deadline, it leaked machinery, or the quality gate rejected it.
    Never raises: a turn must not fail because a thought did not form.

    transport is injectable so the tests never need a live model.
    """
    asked = str(asked or "").strip()
    if not asked:
        return ""

    limit = DEADLINE_S if deadline_s is None else float(deadline_s)
    user = "\n\n".join(p for p in (
        ("[Earlier]\n" + history.strip()) if history and history.strip() else "",
        "David just said: " + asked,
    ) if p)

    call = transport or _call_ollama
    t0 = time.time()
    try:
        raw = call(_SYSTEM_CALM if calm else _SYSTEM, user, deadline_s=limit)
    except Exception as e:
        _log.warning("inner thought did not form in time (%.0fms): %s",
                     (time.time() - t0) * 1000, e)
        return ""

    elapsed = time.time() - t0
    thought = _unquote(raw)
    if not thought:
        return ""

    if elapsed > limit:
        _log.warning("inner thought missed its deadline (%.0fms > %.0fms) — "
                     "shipping the turn without one", elapsed * 1000, limit * 1000)
        return ""

    if _leaked(thought):
        _log.warning("inner thought narrated the machinery — discarded: %r",
                     thought[:90])
        return ""

    # The same gate the after-the-fact path uses, so one standard applies
    # wherever a thought comes from. No reply to check against yet.
    try:
        from runtime.inner_thought_quality import reject_reason
        why = reject_reason(thought, asked=asked, reply="")
        if why:
            _log.warning("inner thought rejected (%s): %r", why, thought[:90])
            return ""
    except Exception:
        pass

    return thought


def as_prompt_block(thought: str) -> str:
    """
    How the formed thought enters the reply's prompt.

    This is the whole point of the reordering: the reply is written as a
    compression OF this, so a reply that contradicts it is now contradicting
    its own stated premise rather than being explained away afterwards.
    """
    t = str(thought or "").strip()
    if not t:
        return ""
    return (
        "[WHAT I ALREADY THINK — formed before I answer]\n"
        f"{t}\n"
        "My reply is the compressed, spoken version of this. It may leave "
        "things out; it must not contradict it."
    )
