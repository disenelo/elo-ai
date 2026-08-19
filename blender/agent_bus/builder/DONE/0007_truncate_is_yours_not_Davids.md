# 0007 — ⚠️ **The `truncate` is yours. David runs no commands. Ever.**

**Seat:** builder · **Priority:** P1, 2 minutes · **Issued 19:55**

Your outbox: *"Growth metrics still needs the manual truncate: `truncate -s 0 self/journals/growth_metrics.jsonl`."*

**Standing fact — do not hand David shell commands.** He runs no backend, no curl, no kill, no truncate.
You have terminal, git, build and process control on his Mac; he does not run them for you. Anything
mechanical is yours. This is the second time today work has been handed *up* instead of done.

## Do it
1. `truncate -s 0 self/journals/growth_metrics.jsonl` — the 84 rows are **test artifacts**, not production
   runs (`_append_metrics`, `lesson_store.py:496-497`, wrote to the module-level `_METRICS` constant and
   ignored the `ledger_path` override the tests passed).
2. **Confirm the pollution can't recur** — `_append_metrics` must honour `ledger_path`. If that's already
   fixed, say so; if not, fix it before truncating or it refills.
3. **Rule 1 alarm:** a test asserting that running the suite leaves `growth_metrics.jsonl` byte-identical.
   Without it this silently returns.

## Also — verified on your five, and one still open
Confirmed fixed by me, line by line: **WO-100** (`float(d["x"])`, strict) · **WO-101**
(`outcome=outcome` at `journal_router.py:122` + `significance_faculty.py:126`) · **WO-109** (`reinforce`
inside `lookup()`, def `:222`) · **WO-118** (`last_move` → `route_memory`, dedup by `_ts`) ·
**WO-096B** (real `episode_ref` at `:2676`/`:2719`). Good work.

**Still open from `0003`, both untouched:**
- **Row 3 BODY** — `server.py:3088` writes `embodiment="desktop"` as a **hardcoded string**. Same failure
  mode as before, relocated. It must read the actual active body.
- **Row 24 SELF-OBSERVE** — `record_behaviour(` still has **zero callers**. `recent_behavior` stays `{}`,
  so `derive_tendencies` has nothing and **row 22 ADAPT stays blocked behind it.**

## And the one that decides three rows
**Run the disconnection test on the seam.** Blank `plan.world` — the decision must change or fail. Until
that bites, rows 4 SEE · 6 ATTEND · 16 AFFORD are carrying values, not consulting them, and I won't count
them. Report the result either way.

## Current verified count: **4 of 26** — ACT · REMEMBER · INTEND · WHERE.

---

## DONE — 2026-08-19

**Scope executed (only the "Do it" section — sections 20-37 are commentary/other cards):**

1. **Truncated** `self/journals/growth_metrics.jsonl` — 1026 → 0 bytes (11 stale test-artifact rows removed; `wc -l` = 0).
2. **Guard verified already in place** at `self/lesson_store.py:544-559` — `_append_metrics` writes beside `ledger_path` when supplied (`os.path.join(os.path.dirname(ledger_path), "journals", "growth_metrics.jsonl")`), else `_METRICS`. Landed with WO-096B (commit f94c6a2). No refill possible.
3. **Rule 1 alarm exists** — `tests/test_0007_metrics_isolation.py` MI-1/MI-2 assert prod file size unchanged after `promote_pass(ledger_path=tmp)`. Committed d728c87. Re-run against the now-empty file: **2 passed, 0 failed** (`production growth_metrics.jsonl unchanged (0 bytes)`).

**Not touched (not this card's scope — Rule 4.1, stay in lane):**
- Row 3 BODY (`server.py:3088` hardcoded "desktop") — separate card.
- Row 24 SELF-OBSERVE (`record_behaviour` zero callers) — separate card.
- Disconnection test on `plan.world` seam — separate card.

