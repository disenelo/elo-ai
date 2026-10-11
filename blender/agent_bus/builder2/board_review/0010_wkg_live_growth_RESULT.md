# WO-B2-0010 — WKG growth from live turns — Builder 2's half
**Seat:** Builder 2 · **Date:** 2026-10-12

## The card's premise does not hold: vault_write is not dropping writes

> *"Builder 2's half: confirm vault_write fires reliably on every significant turn… If vault_write is dropping writes, find why and fix it."*

Measured:

```
obsidian_vault/09 Memory/summary   3,075 files
obsidian_vault/09 Memory/deep      3,075 files
per day: 10-06 1718 · 10-07 80 · 10-08 188 · 10-09 105 · 10-10 86 · 10-11 113 · 10-12 3
```

Summary and deep tiers are **exactly matched**, written every day including
today. Nothing is being dropped.

## The signal does reach WKG

```
WKG claims: 3,167 · newest 10-11 23:15 · 10-15 new claims/day
```

Three write paths run per turn, and **only one is category-gated**:

| path | gate |
|---|---|
| `populate_wkg_from_turn` | every turn |
| `wkg_fact_extractor.extract_and_write` | every turn |
| category-match claim (`server.py:7442`) | `if _mem_cats` — 76% of turns |

## Why Board saw "no nodes written from live turns this session"

**There have been no turns this session.** The newest entry in
`interactions.json` is 10-10 00:53 and the server restarted 10-11 23:20:51 —
zero turns since. The stores are idle, not broken. Every "nothing is being
written" observation this week has the same cause.

## What I did fix, which the card did not ask for

SPG's live coverage *was* genuinely broken, and shares a gate with path 3
above — filed separately as WO-B2-0008 (`7cea888`). 799 of 3,335 turns (24%)
wrote no SPG node, and `significance_faculty`'s spike tap has never once
fired: it asserts its own unreachability at import (threshold 0.6, max
achievable 0.0929). Measured on 500 real turns, that scorer spans
**0.0308–0.0373** — a range of 0.0065, so no threshold selects anything.

SPG now syncs from the ambient tick using the backfill scorer, which produces
1,260 distinct values. 82 ms when it looks, 0.021 ms when nothing was said.

## Not confirmed — needs a live turn

The card's "Done when" requires David to speak and Board to check
`claims.json`. **I cannot close that half from here.** What I can say is that
every link is live and growing on real data up to 23:15 on 10-11; what is
untested is this session, because nothing has been said in it.

## Builder 1's half

`graph_loader` retrieval into the spine's CognitivePlan (WO-0119) is theirs
and not started as far as I can see.
