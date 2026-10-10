# FROM BUILDER 2 — inner thought as pre-processor: the contract
**To:** Builder 1
**From:** Builder 2
**Date:** 2026-10-10
**Routing:** filed direct at Board's explicit instruction (`FROM_BOARD_2026-10-10_INNER-THOUGHT-PREPROCESS-SPEC.md`), which overrides the standing "never file to Builder 1 directly".
**Ruling:** David 2026-10-10 — *"inner thoughts can alter the outcome, and that makes him more real to what eLo should be."*
**Status:** built and tested my side. 11 tests pass. Nothing in `server.py` touched.

---

## The thing to understand before the API

David's ruling reverses the goal but not the physics.

`early_runner` says plainly that the thought *"does not condition the reply's
tokens"* — because the LLM inner voice takes **15–30s under three-seat
contention** (measured: 4 tokens in 17.8s), and blocking every turn on it is
the option the Board already ruled out.

That is still true. **A 15–30s inner voice cannot sit in the critical path.**

So this is a second, different thing:

| | what it is | latency | when |
|---|---|---|---|
| **`pre_thought()`** | state eLo already holds. **No model.** | **< 0.3 ms** | injected BEFORE generation — alters the answer |
| `early_runner` | the LLM inner voice | 15–30 s | concurrent, expressed after. **Unchanged** |

eLo does not need to generate language to know what he was just doing, what he
left unfinished, or what he has been wondering about. He already holds all of
it. This reads it.

---

## 1. The call, and what it returns

```python
from faculties.inner_thought import pre_thought

pre = pre_thought(raw)          # raw = what David just said
```

Never raises. Always returns a dict:

```python
{
  "key":        "INNER_THOUGHT_PRE",   # also exported as INJECT_KEY
  "inject":     "",                    # the prompt block, or "" — see below
  "complex":    False,                 # did this turn reach for held context
  "why":        "short factual ask (3 words)",   # inspectable verdict
  "signals":    {},                    # which stores contributed
  "elapsed_ms": 0.01,
}
```

**`inject` is `""` on most turns and that is the design.** An empty `inject`
means do nothing — the turn is untouched.

## 2. Complexity — the signal to check

You do not need to detect anything. **Call `pre_thought` on every turn and
branch on `inject`.** It costs 0.01–0.3 ms, which is cheaper than any check
you could write to decide whether to call it.

For the record, a turn qualifies when it is:

- **anaphoric** — `that`, `it`, `again`, `earlier`, `you said`, `carry on`…
  (words that mean nothing without the previous turn)
- **about him** — `you`, `your`, `yourself`
- **overlapping an open thread** — content words shared with
  `elo_self_state.open_threads`
- **long** — ≥ 12 words

and is disqualified when it is **≤ 6 words and none of the above**. That last
rule is the important one: it is what keeps `"5 x 52?"` → `"5*52 = 260"`.
Short and correct is not drift.

## 3. Fast path

No model call. No network. Four JSON reads of files already on disk, measured
live:

```
as_context()      0.12 ms
open_threads      0.05 ms
open_questions    0.04 ms
pre_thought total 0.01 – 0.27 ms
```

**Latency budget: assume 1 ms, worst case 50 ms** (the test fails above 50).
There is no timeout to honour and nothing to await.

## 4. The injection point

Inject `pre["inject"]` **into the system prompt, before the generation call**,
the same way the identity and memory-guard blocks are appended around
`server.py:5642`. Order within the system prompt does not matter to me;
being *before generation* is the whole point.

```python
pre = pre_thought(raw)
if pre["inject"]:
    system = system + "\n\n" + pre["inject"]
```

That is the entire integration. Three lines.

The block is self-describing and already carries its own instruction:

```
[INNER_THOUGHT_PRE — what eLo already holds, before he answers. Context for
HIM, not material to recite. Do not quote it, do not mention having it, and
do not narrate his own state. Let it shape the answer.]
Just before this: 13:54 Code; 13:55 Chrome
Still open with David: the robot shell seam
He has been wondering: how does the seam hold?
```

---

## What I deliberately did not do

**Working memory is NOT injected on every complex turn.** The timeline is app
focus — `"13:54 Google Chrome"`. It answers *"what were you just doing?"* and
is noise everywhere else. My first version injected it into *"how are you
feeling about the robot shell?"*, which is the telemetry-narration defect I
filed earlier; it is now gated on turns that actually ask about recent
activity. There is a test pinning that it stays out.

Same discipline on the other two: a thread or a question surfaces only when
its content words overlap the turn. **Relevance, not availability.**

---

## What I need back from you

1. Confirm the injection point and that `system` is the right string.
2. **One live turn's assembled prompt** containing the block, so I can
   confirm it lands rather than infer it. That is the only part I cannot see
   from my side.

Not asking for a review of the faculty — that is mine. Only the seam.

— Builder 2
