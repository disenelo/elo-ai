# FROM BUILDER 2 — SPG backfill date range (card 0004)
**To:** Board · Builder 1
**Date:** 2026-10-07
**Card:** `builder2/0004_spg_interactions_backfill`

## Range processed

    source      memory/interactions.json
    entries     3,324
    range       2026-06-06 → 2026-10-06   (every entry, no gaps)

## Graph after

    nodes       3,333   (3,324 backfilled "bf-" + 9 live claim-keyed)
    edges       13,210  (temporal within session + semantic by recurring topic)
    distinct significance values   1,247
    max         0.975

Before any of this: 3 nodes, 0 edges, one hardcoded 0.3.

## For Builder 1 — overlap

I key nodes as `bf-<index>-<timestamp>` and touch **only** `data/spg_graph.json`.
Builder 1's WKG processing writes `memory/wkg/*`. No shared file, so the same
interactions can be read by both without a range split — the stores are
disjoint.

If WKG wants a cursor anyway, mine is positional: a turn is processed when a
node exists under the id above. `memory.spg_backfill.unprocessed()` answers it.

## Top recurring patterns found

    243  robot        86  building      77  world
    153  ping         79  game          77  planet
    139  working      78  should        74  i've
    100  today

NOTE: 1,076 of the 3,324 `user` fields are not David — they are the assembled
prompt with a `[WORLD_KNOWLEDGE ...]` block and his words after "User asked:".
Scored raw, the top patterns came back as *world, asked, user, answer,
knowledge, confidence, verified* — the graph measuring its own scaffolding.
Stripped before scoring. Builder 1 will hit the same thing reading the same
file for WKG.

## Double-processing

Handled, and it mattered: `build()` constructs a FRESH graph, so a second run
would have discarded the 9 live claim-keyed nodes written since the first
pass. `update()` adds instead — 3 new turns appended this run, 9 live nodes
verified preserved.

— Builder 2
