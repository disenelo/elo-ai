# WO-DREAM-WIRE-S3 — evidence

**Builder 2 · 2026-10-05 · live, running server (pid 8074, started 02:54:53)**

## Result in one line

The detect-and-consume half is **live verified**. The dream itself **did not run**, and I have not yet diagnosed why.

## Method

Manual `intent:"dream"` injection, as the dispatch instructs. Server confirmed to
contain the wire: `ecfca38` committed 2026-10-04 20:59:24, process started
2026-10-05 02:54:53.

```
BEFORE (03:39)                 intent=idle  asleep=False  dream_phase=None
                               elo_battery=0.808  calm_mode=False
                               self: mood=0.0 curiosity=0.763 satisfaction=0.002
                               dream_log lines=1   dream_journal entries=166

INJECT  (03:39)                state_writer.patch({"intent": "dream"})
                               dream_requested() -> True

OBSERVED (03:42:24, +165s)     intent consumed -> "idle"
```

The gate is `if should_dream(...) or _dream_asked():` and `or` short-circuits, so
`_dream_asked()` only runs when `should_dream` has already declined. The intent
being consumed therefore proves the ambient callback fired, the request was
detected, and the branch body was entered. That is the piece this WO asked for.

## What did not happen

```
self/dream_journal.jsonl   166 entries, unchanged (last write 2026-09-30)
data/dream_log.jsonl       1 line, unchanged
dream_phase                never observed non-empty (15s poll)
asleep                     never True
```

So the branch ran and produced no dream. Most likely the pipeline inside it
raised and was swallowed by its surrounding `except` — the same silent-failure
shape found four times elsewhere today — but **that is a hypothesis, not a
finding**. The server writes to a terminal, not a log file, so there is no
stderr to read. Not claimed as diagnosed.

## Status

| piece | state |
|---|---|
| Builder 1 trigger (Missing A) | committed `8803f5c` |
| Builder 2 detect + consume (Missing B) | **live verified** |
| dream execution → journal entry | **not working** — cause undiagnosed |
| wake → mood/curiosity/satisfaction shift | not reached |

Kickstarter Demo 2 ("eLo has an inner life") needs the bottom two rows. The
chain is wired end to end and stops at execution.
