# Board review — SPG backfill caught up to the live journal

**From:** Builder 2 · **Date:** 2026-10-11
**Follows:** `FROM_BOARD_2026-10-11_FULL-DEMO-SPRINT-B2.md` item 3 (SPG — demo-ready)
**Scripts run:** `scripts/spg_backfill_update.py`

## What I did

Ran the incremental backfill. The build already caught the four months of
history in `efe3cd3` + `d5aab22`; this pass picked up the four turns that had
landed since the last update. The script writes to the on-disk live graph —
same convention the earlier passes used (data file isn't carried in the
commit; code and reports are).

```
BEFORE : 3888 nodes, 13220 edges, sha f615612edd53
source : 3335 interactions, 4 unprocessed
backup : spg_graph.json.before_update_20261011_024932
AFTER  : 3892 nodes, 13230 edges, sha cf10635410d9
verify : 4 added, 557 live-written nodes preserved
```

557 live claim-keyed nodes survived the update — `update()` adds instead of
rebuilding, so none of what `record_claim` has written since the last
backfill was discarded. The archive copy of the pre-update graph is at
`.memory-archive/spg_graph.json.before_update_20261011_024932`.

## Verified

- `pytest -k spg` — **159 passed · 0 failed**
- `memory/interactions.json` — 3,335 turns · 2026-06-06 → 2026-10-10
- `memory.spg_backfill.unprocessed()` — 0 remaining

## Top recurring topics (raw counts, from `recurring_topics(top=15)`)

| topic     | count |
|-----------|------:|
| robot     | 244   |
| ping      | 153   |
| working   | 139   |
| today     | 100   |
| building  | 86    |
| game      | 79    |
| should    | 78    |
| world     | 77    |
| planet    | 77    |
| test      | 72    |
| tell      | 70    |
| servo     | 57    |
| printer   | 56    |
| build     | 51    |

The raw recurrence over the four-month history still points at David's real
threads — robot, the game, eLo-Planet, building, testing, servos, printers.

## Flag — not fixed in this card

`topic_significance()` (`memory/spg_topic_index.py:51`) applies an IDF-style
discount so a word in 1,000 turns doesn't carry an entity on recurrence alone
("Hello, World!" vs. eLo robot design constraints — the comment at line 83
spells out the reason it exists). On the live graph the discount is now
dominating the signal:

| topic       | edges | max_sig | discounted |
|-------------|------:|--------:|-----------:|
| days        | 5     | 0.9750  | 0.9659     |
| navigation  | 10    | 0.9700  | 0.9459     |
| transition  | 10    | 0.9700  | 0.9459     |
| embodied    | 10    | 0.9700  | 0.9459     |
| robot       | 243   | 0.9750  | **0.2437** |
| game        | 78    | 0.9700  | 0.7101     |
| world       | 76    | 0.9700  | 0.7154     |

Robot — David's single most recurring topic — gets pushed near the bottom of
the index because the discount factor is `(1 - 0.75 * share)` and robot's
`share` is ~1.0. 14 rare topics tie at 0.9459 at the top because they all have
`freq ≈ 10` and inherit `max_sig = 0.97` from the same high-significance
cluster of turns.

This matters for the "what do I keep coming back to?" live turn gate on the
0004 card: `recurring_topics()` (raw count) still answers it correctly, but
anything downstream that reads `topic_significance()` will rank rare words
above robot/game/world.

Not retuning in this card — the discount shape is already called out as
`[BUILDER CHOICE]` (`spg_topic_index.py:149`) and the fix is a judgement
about the magnitude of the discount, not a bug. Flagging for Board decision:
soften from `0.75` to something smaller, or move to a frequency-floor
(top-N by recurrence, THEN sort by significance within that set), or keep as
is. I can do any of the three in a follow-up card.

## Live turn gate (from 0004)

**"what do I keep coming back to?"** — the raw recurrence index still names
his threads. The reranker that reads `topic_significance()` currently will
not; see flag above.

## Scope kept narrow — what I did NOT touch

- `topic_significance` discount — flagged, not fixed. One card, one decision.
- Significance scorer. Separately desaturated in a8d6a77 earlier today.
- Symbol selection. Separately fixed in 57770a7 earlier today.
- Random-fact raise-hand. Separately verified in b19423a / c7a7a6f.

— Builder 2
