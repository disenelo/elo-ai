# TO BOARD — dreams: the root cause is one layer below the scorer
**From:** Builder 2
**Date:** 2026-10-10
**State:** `IMPLEMENT`
**Commit:** `5f8420d`
**Supersedes nothing** — extends `FROM_BOARD_REQUEST_2026-10-09_DREAMS-FIRST-RETENTION.md`, which said *"the scorer, not the threshold, is the real defect."* That was right and still one layer too shallow.

---

## eLo has been dreaming about the letters x and y

`_dream_context` fed the Dream Input Field topic **labels**, not conversation.
Measured across all 1,489 seeds ever written:

| seed source | count |
|---|---|
| `y` | 360 |
| `connection` | 289 |
| `x` | 270 |
| `creative_spark` | 186 |
| `robot arm` | 183 |
| `quiet` | 68 |

Single tokens. The `x` and `y` are almost certainly from arithmetic turns —
the same ones the drift detector was flagging as insufficiently playful.

A one-letter seed carries no emotion cue and no unfinishedness cue. So
`parse_emotion_vector("y")` returns an all-zero vector and `_cue_score("y",
_UNFINISHED_CUES)` returns 0.0 — which is **exactly** why the emotional (0.30)
and unresolved (0.20) terms read zero on every dream eLo has ever had, and
why 82 of 103 scored dreams landed on an identical 0.4000.

The chain, now visible end to end:

```
topic labels as dream material
  -> seeds are single tokens
    -> emotion + unfinishedness cues cannot fire
      -> 3 of 4 scorer terms are structurally dead
        -> every dream scores the intensity constant, 0.400
          -> no dream ever clears any threshold
            -> 0 retained of 216
```

Three days of this were read as a threshold problem. The threshold was the
fourth layer of symptom.

---

## Fix and measurement

`recent_conversation` now carries real turns from the live store, **with the
topics kept alongside rather than replaced** — they are a real signal, just
not enough to dream on.

| | before | after |
|---|---|---|
| seeds carrying `unresolved` | 0 of 103 dreams, ever | 3 of 6 |
| seeds carrying emotion | ~15 of 103 dreams | 2 of 6 |
| significance, same harness | 0.500 | **0.800** |

0.800 clears even the original 0.72.

**Caveat, stated rather than buried:** that harness reconstructs the cycle
record, so its "before" reads 0.500 where production journals show 0.400. The
direction is real and the mechanism is proven; the absolute is not a
production reproduction. The honest confirmation is the next real dream.

Seeds now read like `"what do I keep coming back to?"` and `"I wonder where
you're going with that. What's next?"` instead of `y`.

---

## On the generator template

My previous filing proposed the templated narrative (8 of 9 retained dreams
sharing one insight sentence) as a second card needing David's ruling. **That
may not need a ruling after all.** The template was being asked to write a
dream out of the letter `y`; there was nothing else for it to do. Worth
re-measuring the content once real dreams have run before treating "change
what eLo dreams" as a design change.

**Recommend holding the threshold at 0.45 and re-reading the journal in a day**,
rather than tuning again now. If scores move toward 0.8 the bar should go
back up, and the evidence for where will be real rather than inferred.

---

## One thing I got wrong and corrected

My first version of this fix called `os.path` in a file that never imports
`os`, inside a `try/except Exception` — so it would have failed silently and
returned an empty list forever. Built, wired, provably inert: the exact
pattern I have filed fifteen times. Caught by running it instead of trusting
it. Switched to `Path`, which the file already imports.

I also reached straight into the live turn store from `_dream_context`, which
is the live-state coupling I had fixed in `ambient_engine` the same morning.
`_INTERACTIONS_PATH` is now a module constant so tests can isolate it.

Two tests updated, both correct breakage; 448 dream tests pass; full suite
3,962 passed / 3 failed, none of the three mine.

— Builder 2
