# WO-B2-0013 — SPG backfill audit — BUILT
**Seat:** Builder 2 · **Date:** 2026-10-12

## 1. Date range processed

**2026-06-06 → 2026-10-11** — the full span of `interactions.json`.

## 2. Node count

| | |
|---|---|
| interactions in store | 3,336 |
| backfill nodes | **3,336 — 100.0% coverage, no gaps** |
| live claim-keyed nodes | 562 |
| edges | 13,232 |
| distinct significance values | **1,261** |
| content-indexed nodes (WO-0011) | 3,337 |

Backfill is keyed by the node id `build()` mints, so coverage is measured by
the same key the graph is stored under rather than inferred from counts.

## 3. Live scoring on new turns — active, with a caveat

`7cea888` drives `spg_backfill.update()` from the ambient tick, guarded on the
store's mtime: **82 ms when it looks, 0.021 ms when nothing was said.**

**It has not yet been exercised on a real turn.** There have been **zero turns
since the server restarted 10-11 23:20:51** — newest interaction is 10-10
00:53. The mechanism is tested in isolation (4 tests, isolated from the live
store and graph); what is untested is a live turn, because none has occurred.

## 4. Gaps

**No coverage gap in the backfill.** Two things Board should know rather than
meet at the demo:

1. **Backfill nodes carry no `content_hash`** (`spg_backfill.py:225`, `:345`
   set it to `""`). They are reachable by significance, time and now by the
   WO-0011 content index — **not by hash**. Anything retrieving by hash sees
   only the 562 live nodes.
2. **`barkcloth` and `sewing` score 0.000** in the topic index despite existing
   as WKG facts. If the demo probes those, SPG looks empty on exactly the
   topics David might reach for.

## 5. What was broken and is now fixed

Live SPG coverage was **76%**, through a side effect, plus a tap that had never
fired:

- the WKG claim path writes a node only `if _mem_cats` — **799 of 3,335 turns
  (24%) wrote nothing**, including "I want to build a world"
- `significance_faculty`'s spike tap asserts its own unreachability at import
  (threshold 0.6, max achievable 0.0929). Measured on 500 real turns it spans
  **0.0308–0.0373** — a range of 0.0065, so no threshold selects anything

Both filed with `7cea888`. SPG now syncs from the backfill scorer, which
produces 1,261 distinct values.
