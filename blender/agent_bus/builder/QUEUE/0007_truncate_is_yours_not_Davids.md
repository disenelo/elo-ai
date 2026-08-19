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
