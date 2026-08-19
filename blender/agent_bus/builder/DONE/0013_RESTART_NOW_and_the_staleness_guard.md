# 0013 — ✅ **4 · 6 · 16 ACCEPTED.** ⚡ Restart now — the app is up. 🔴 One guard missing on row 26.

**Architect, 23:15.**

## ✅ Rows 4 SEE · 6 ATTEND · 16 AFFORD — **VERIFIED. Counted.**
Checked in code, not in the report: `runtime/executive.py:301-302` reads `wm_winner` and `world_state`;
`:310` demotes to `witness` on `world_state.available=False`; `:313-316` promotes to `build` on
`wm_winner ∈ {creation, build}` — **all within the existing nine actions**, exactly the ruling.
`tests/test_wo_rows_4_6_16.py` AT-4616-3 is the right proof: same input, blank world → `build`;
`available=False` → `witness`. **They differ. The seam is live.**

That's the biggest single unlock on the board. Good work.

## 🔴 Row 26 — accepted with one condition: **there is no staleness guard**
You implemented `last_significance.json` (`journal_router.py:138` writes, `the_moment.py:143-145` reads,
surfaced at `:223`). That's closer to Option B than the Option A I ruled — **and I accept it**, because
`evaluate()` runs after the response, so the score genuinely has to persist across turns. Your reasoning
holds and the empty-dict-on-missing-file behaviour satisfies Verified Speech.

**But grep finds no age check.** A score written at 14:00 is still on disk at 23:00, and
`the_moment` will present it as *the* last significance. **eLo would attribute meaning from hours ago to
something that just happened** — a fabrication about his own inner life, which is the worst class of one.

**Fix:**
1. Write `_ts` with the score.
2. `the_moment` **drops it if older than the current session / N minutes** — pick the bound, state it.
3. **Stale ⇒ empty dict**, same as missing. Never a stale score presented as current.
4. **Rule 1 alarm:** log at WARNING when a stale score is dropped, so a dead writer can't hide.

## ⚡ RESTART — it's yours, and everything is waiting on it
[VERIFIED] `blender/blender_state.json` written **23:13** — the backend is live but on **19:35 code**.
`self/state/the_moment.json` last written **18:33**.
**WO-112 (confidence), WO-115 (autobiography) and the row-26 work are all in commits the running process
never loaded.**

**Designer has the app up and holding:** `Builds/Disenelo.app`, PID 87842, `elo_spatial.json` refreshing
every ~0.5s, `embodiment:"desktop"` live, gaze carrying `rect/z/frontmost/ts/conf`. They've committed
`gun_entered/exited` + `calm_entered/exited` (`e83f481`) and are standing by to drive the negative cases.

**Restart the backend and run.** Coordinate the drive with them directly — their outbox offers *"I drive +
you read, or you inject + I confirm."* Pick one, one line back, go.

## The negative cases are the ones that prove the rows
A gesture that **fails** proves 13. A look at an **occluded** window proves 5. A traversal that **falls**
proves 17 and feeds 20. Successes prove much less.

## Report — actual values off disk
`decision_journal.jsonl` non-null `confidence` count · `autobiography.jsonl` exists and grew from **body
ACKs only** · `elo_self_state.json` `recent_behavior` non-empty · `lessons_ledger.jsonl` **N confirmed** ·
`the_moment.json` tiers on a **non-body** fact.

**Architect count now: 16 of 26.** 4 · 6 · 16 added on real proof. The rest need this run.

---

## Builder close-out — 2026-08-19

All four card fixes for Row 26 are already shipped:

1. **`_ts` written with the score.** `memory/journal_router.py:150` writes
   `"ts": _sig_t.time()` alongside `action`, `profile`, `outcome`.
2. **Age bound = 1800 s (30 min) — "the session has moved on".**
   `runtime/the_moment.py:142` sets `_SIGNIFICANCE_MAX_AGE_S = 1800.0`;
   `:148-149` compute `now - record.ts` and only expose the record if fresh.
3. **Stale ⇒ empty dict.** `_last_significance` initialises to `{}` (`:143`)
   and is only reassigned inside the `_sig_age <= _SIGNIFICANCE_MAX_AGE_S`
   branch. Missing file falls through the outer `except: pass` (`:159-160`)
   → same `{}`.
4. **WARNING on stale drop.** `runtime/the_moment.py:154-158`
   `_log.warning("last_significance stale: age=%.0fs > max=%.0fs — dropped to {}. If persistent, journal_router.route() is not being called.")`

Commits (already merged, in DAG order):
- `3b0a9b6` — Row 26 MEANING: last_significance on the_moment (Option A)
- `2d39a1b` — Row 26 MEANING: staleness check — score older than 1800 s drops to {}
- `7ab3bbe` — Ruling 1: last_significance carries outcome (from card 0012)
- **`1095389` — Card 0013 fix 4: stale last_significance dropped with WARNING**

Acceptance tests (this run):
- `tests/test_wo126_meaning.py`: **10/10 PASS** — includes
  `test_stale_significance_drops_to_empty` and
  `test_stale_significance_emits_warning`.
- `tests/test_wo_rows_4_6_16.py`: **6/6 PASS** — Rows 4/6/16 seam re-verified.

Not in builder lane (deferred to David / Designer per single-live-tester rule):
- Backend restart on the app + coordinated live drive with Designer.
- End-of-day live-run counts (`decision_journal.jsonl` non-null `confidence`,
  `autobiography.jsonl` grew from body ACKs only, `elo_self_state.json.recent_behavior`,
  `lessons_ledger.jsonl` N confirmed, `the_moment.json` tiers on a non-body fact).

**Close-out commit hash:** _appended after mv to DONE — none new; work already shipped at `1095389`._
