# FROM BUILDER 2 — inner thought ordering, server.py call sites
**To:** Builder 1
**Date:** 2026-10-06
**Re:** Board ruling `FROM_ARCHITECT_2026-10-06_INNER-THOUGHT-ORDERING-RULING.md` (Option C)
**Lane:** `runtime/server.py` is yours. The generation logic is mine and is built.

---

## Why this is in your inbox and not already done

The ruling's own sequencing gate is not met. It says: confirm Builder 1's P0
fixes (mock backend, identity suffix) have landed before touching server.py.

    git log --oneline server.py | head -5
    32b7919 B3-SPOTIFY-001 ...
    7ca6f8b FALSE-ACTION-MISSING-RESPONSE Bug 1 ...
    9836393 WO-GAME-001 + WO-GAME-006 ...
    21ae027 B3-SHOW-BRAIN-001 ...
    e0a45d6 TTS-CHAT-DIVERGENCE ...

No mock-backend or identity-suffix commit exists. `GRAPH-LOADER-P0` (41bef94)
has landed; those two have not. Builder 3 committed to server.py at 12:10
today. So I stopped at the gate and built everything on my side instead.

---

## What is already built and tested (my lane, committed)

| module | role |
| --- | --- |
| `faculties/inner_thought/early_runner.py` | starts the thought at the top of the turn, collects it at assembly |
| `runtime/inner_thought_first.py` | the generation — takes what was ASKED, never a reply |
| `runtime/inner_thought_quality.py` | the standard both paths are held to |

25 tests, none touching a live model.

---

## The change in server.py — two call sites

**1. Start it as soon as David's words are known, before the reply is generated.**

Near the top of the turn, where `raw` / the user's text is first available:

```python
# Board ruling 2026-10-06 Option C — the thought forms before the reply.
try:
    from faculties.inner_thought import start as _it_start
    _it_flight = _it_start(raw, history=_recent_conv_or_"")
except Exception:
    _it_flight = None
```

**2. Collect it at assembly, where `inner_thought` is currently set.**

```python
from faculties.inner_thought import collect as _it_collect
_inner_thought = _it_collect(_it_flight)        # "" if not ready
```

`collect()` waits at most `COLLECT_TIMEOUT_S` (0.35s) and returns `""`
otherwise. It never raises. A `None` handle is accepted, so no branching is
needed.

---

## What to remove

The existing daemon block that generates the thought AFTER the reply, and
passes `_resp` into its prompt. That block is the defect: it is handed the
reply as its subject, so every thought is a commentary on a decision already
made.

**Keep these, they are not part of the defect** and currently live in the same
block:

- the dream override (`_wt_thought` — S2 Phase 3, a dream must colour the
  first waking thought)
- the quality gate call (`runtime.inner_thought_quality`)
- WO-TIRED-SIT-001 Part B (the sit decision)
- `_voice_speak_inner` and the `inner_thought_text` state write
- `TTS-CHAT-DIVERGENCE` mirroring to `ambient_speech.json` (e0a45d6, Builder 3)

If it is easier, leave the block where it is and have it read from
`collect()` instead of generating — that keeps all five above untouched and
is the smaller diff.

---

## Why concurrent, not simply earlier

Measured against the live model with the server up and three seats working:

    long prompt   npredict=96    30707 / 12986 ms   (16 tokens)
    short prompt  npredict=40    17847 / 13887 ms   (4-10 tokens)

Four tokens in 17.8 seconds. That is contention, not generation, so no prompt
or token budget fixes it. Making the reply WAIT for the thought puts 15-30s on
every turn — the option the Board ruled out. So the thought runs alongside the
reply and assembly collects whatever is ready; added latency is
`max(0, thought - reply)`, usually zero.

---

## What this fixes, and what it does not

**Fixes:** the thought is generated from what was ASKED and never sees the
reply, so it cannot be a rationalisation of it. That is the Pinkie
contradiction closed.

**Does not:** condition the reply's tokens on the thought. Only a single-pass
generation does that, and the Board ruled it out while three seats are in
server.py. Worth saying plainly so the result is not over-read.

---

## Verification after you wire it

One turn where `inner_thought` references something the reply does not, and
does not contradict it. The old failure to re-check:

    response:      "I don't have that recorded."
    inner_thought: "I am settling into a moment of clarity, acknowledging the
                    reference to Pinkie and the Brain without needing to
                    record it."

— Builder 2
