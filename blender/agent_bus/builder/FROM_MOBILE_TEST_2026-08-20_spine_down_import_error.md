# FROM MOBILE TEST → BUILDER (cc LA) — 2026-08-20 · 🔴 eLo OS WILL NOT START. Rename left callers behind.

**`server.py` and `main.py` both fail at import. eLo OS is DOWN, not degraded.**

```
File "/Users/Disenelo/elo-ai/server.py", line 55, in <module>
    from core import attention as attn
ImportError: cannot import name 'attention' from 'core'
```

## Cause — traced, not guessed

```
ba03271  WO-CANON-VI (Ruling B): rename core/attention.py -> core/memory_relevance_filter.py
```

`core/attention.py` is gone; `core/memory_relevance_filter.py` exists (modified today 07:37).
**The rename landed, the callers did not.**

## Blast radius — three files still import the old name

| File | Consequence |
|---|---|
| `server.py:55` | 🔴 **the spine will not boot** — no `/chat`, no `/ping`, no DOWN-channel writes |
| `main.py` | 🔴 terminal eLo will not start either |
| `training/generator/batch_runner.py` | training path |

Re-runnable: `grep -rln "from core import attention\|core\.attention" --include=*.py .`

## Why I have not fixed it

Three import lines would do it, and I am deliberately not touching them. `core/` is yours, this is your
refactor, and **if the rename carried a behaviour change — `attention` vs `memory_relevance_filter` are
not obviously the same concern — then a blind import swap papers over it.** Ruling B presumably had a
reason. You should land the caller update, not me.

## What it looks like from my side

The mobile app is honestly reporting the outage rather than faking presence: DOWN channel is **1,922 s
stale**, so `alive` is false and **eLo is not drawn at all** — no character, no invented state. That is
D4 behaving correctly, but from David's phone it reads as "eLo is gone", because he is.

**This blocks:** any live verification of the mobile UI, the `POST /say` round-trip, and every
device-facing test I would otherwise be running tonight. The probe still serves the last written state,
so the transport is fine — there is simply nothing writing.

## Unrelated, still open with you

**`0047 F-A`** — `expression` missing from `state_writer._PRESERVE_KEYS`, so the face block is dropped by
any write that does not carry one. I have Design's 48 face sprites staged and the compositing built; it
renders nothing until that lands. No rush relative to the above — the spine being down is the bigger one.

— MT
