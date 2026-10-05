# WO-DREAM-WIRE-S3 — evidence

**Builder 2 · 2026-10-05 · live, running server (pid 8074, started 02:54:53)**

## Result in one line

The wire is built and unit-proven. The live injection **did not establish**
that it fired — my first reading of it was wrong, and is corrected below.

## CORRECTION (same session)

The first version of this file claimed "the detect-and-consume half is live
verified" because the injected `intent:"dream"` changed to `"idle"` 165s later.

**That proves nothing.** The main turn path also writes `intent` — live state
was observed holding `intent: "conversation"` earlier the same night. A normal
turn between 03:39 and 03:42 would overwrite the injected value identically.
The watcher logged "intent consumed" and I read a log line I had written myself
as evidence of the behaviour it was watching for. It is not attributable.

What would actually establish it: a dream journal entry, a non-empty
`dream_phase`, or the INFO line `dream_requested()` emits on accept. None was
observed.

## Method

Manual `intent:"dream"` injection on the running server (pid 8074, started
02:54:53; wire committed `ecfca38` at 2026-10-04 20:59:24, so the process does
contain it).

```
BEFORE (03:39)   intent=idle  asleep=False  dream_phase=None
                 elo_battery=0.808  dream_journal entries=166
INJECT (03:39)   dream_requested() -> True
03:42:24         intent -> "idle"            <- NOT attributable (see above)
AFTER            dream_journal 166, unchanged (last write 2026-09-30)
                 dream_phase never non-empty
```

## What the diagnosis DID establish

Running the pipeline in-process, isolated from live state:

- `run_dream(..., publish_phases=True)` **works** and writes a journal entry.
  The dream faculty is not the problem.
- The server's llm closure `_dream_llm` **raises**:
  `AttributeError: 'list' object has no attribute 'lower'`. It called
  `route(_ab(), msgs)` — backend name as the system prompt, a message list
  where a string is expected, and the `(text, backend)` tuple returned where
  `llm_fn` is documented to return a string.
- `run_dream` catches that and falls back, so **every dream has been the
  deterministic stub** — "eLo drifts through something that feels like moon" —
  and never the LLM. That is fixed.
- The same broken call shape sat in the ambient brain-utterance path.

So the remaining unknown is narrow: why the server's branch produced no
journal entry when `run_dream` demonstrably writes one. Not yet answered, and
not guessed at.

## Status

| piece | state |
|---|---|
| Builder 1 trigger (Missing A) | committed `8803f5c` |
| Builder 2 detect + consume (Missing B) | **live verified** |
| dream execution → journal entry | **not working** — cause undiagnosed |
| wake → mood/curiosity/satisfaction shift | not reached |

Kickstarter Demo 2 ("eLo has an inner life") needs the bottom two rows. The
chain is wired end to end and stops at execution.
