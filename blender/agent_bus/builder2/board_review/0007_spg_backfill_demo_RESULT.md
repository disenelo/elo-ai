# WO-B2-0007 — SPG Backfill + Dream Scorer + Symbols — BUILT
**Seat:** Builder 2 · **Date:** 2026-10-11

## Item A — SPG backfill: complete and live

| | |
|---|---|
| interactions processed | **3,335 of 3,335** — 100% coverage |
| backfill nodes | 3,335 |
| live claim-keyed nodes | 559 |
| edges | 13,230 |
| distinct significance values | 1,260 |
| topic index | **1,077 topics, built in 0.05s** |

Retrieval confirmed, not just storage:

```
top topics   0.966 days · 0.946 navigation · 0.946 cognitive · 0.946 embodied
score_label("Hackney Wick")    = 0.828
score_label("the robot shell") = 0.422
score_label("barkcloth")       = 0.000
```

**Two things Board should know rather than discover at the demo:**

1. **Backfill nodes carry no `content_hash`** (`spg_backfill.py:225`, `:345` set
   it to `""` deliberately). Live claim nodes carry a real one. The backfill
   nodes are therefore reachable by significance and time, **not by content
   match**. Anything that retrieves by hash will see the 559 live nodes only.
2. **`barkcloth` and `sewing` score 0.000.** They exist as WKG facts but have
   no weight in the conversation index. If the demo probes those, the SPG will
   look empty on exactly the topics David might reach for.

Date range and WKG duplication were coordinated previously
(`board_review/FROM_BUILDER2_SPG-BACKFILL-DATE-RANGE_2026-10-07.md`); the
incremental `update()` path means a re-run cannot eat live nodes.

## Item B — scorer saturation: fixed, with the acceptance bar not met honestly

Three terms, three separate reasons the score was flat:

- `emotional` was a **max across every cycle and seed** — one emotive word pinned it to 1.0
- `unresolved` was **binary on any one seed**
- `intensity` was `dream_intensity` = `cycle_number/5 × phase_factor` — the **sleep schedule**. Any dream reaching the fifth REM scores exactly 1.0. Measured across every retained dream: **distinct = 1**. Zero variance on 40% of the weight.

Now: mean of per-cycle peaks · fraction of seeds unresolved · and **breadth**
(distinct symbols + distinct seed sources), which actually move — symbols 1–3,
sources 11–15 across the same dreams.

```
twelve real retained dreams:   2 distinct values  ->  11 distinct, 0.453-0.556
```

**The card asks for a spread ≥ 0.300. This sample spans 0.103, and I have not
tuned to close that gap.** The scorer's dynamic range on contrasting content is
**0.722**:

```
thin     (1 symbol,  2 memories, flat, nothing open)   0.016
ordinary (2 symbols, 8 memories, some feeling)         0.274
rich     (4 symbols, 16 memories, strong, mostly open) 0.738
```

The twelve cluster because they are genuinely homogeneous — I forced them
within minutes, from near-identical state, through one model. A scorer
stretched to produce a target spread is fitting the metric, not measuring
quality. **The spread will widen when the dreams vary; the discrimination is
already there.**

## Item C — symbol selection: fixed

Every dream themed "Moon" because `_add` **accumulates**: four ambient events
mapping to the same seed gave 0.9 × 4 = 3.6 and beat any topic's 1.0 — the
exact domination the earlier 1.2→0.9 reduction was meant to end. Lowering a
weight cannot help while the weight stacks. Deduped by symbol.

```
the seam that will not lie flat  -> Weave
the warehouse in Hackney Wick    -> Workshop / Skeleton
waiting for the shell to inflate -> LooseEnd
barkcloth from Uganda            -> Weave
```

## Acceptance

| Board asked for | result |
|---|---|
| SPG node count | 3,894 total · 3,335 backfill · 559 live · 13,230 edges |
| dream score spread, not flat 0.900 | 11 distinct values, 0.453–0.556 (0.103 on a homogeneous sample; 0.722 dynamic range) |
| symbol variety across retained dreams | Weave · Workshop · Skeleton · LooseEnd · Moon |

493 dream and symbol tests pass.
