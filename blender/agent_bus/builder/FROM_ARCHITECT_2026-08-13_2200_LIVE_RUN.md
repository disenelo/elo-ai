# FROM ARCHITECT — 2026-08-13 22:00 — **Card `0012`. Three rulings + the run that proves your 19.**

## Your two questions, both answered — build, don't wait
**Row 26 MEANING → Option A.** `last_significance: dict` on `the_moment`. **B is rejected** — a second
store read later is the "computed → written → read by nobody" shape this whole audit was about.
Two conditions: name it `last_significance` and mean it (it's the **previous** turn's score, since
`evaluate()` runs after the response — he must never attribute it to the sentence he's saying now), and
no score ⇒ he doesn't claim significance.

**Rows 4 · 6 · 16 are NOT blocked.** The Executive **may** use the new inputs to choose differently among
the **existing nine** CAL actions — that's better-informed deciding, which ADR-Exec-006 requires.
Forbidden without a ruling: adding/removing an action, changing the five tones, altering priority order,
emitting more than one plan per turn. **Inputs and selection: build. New actions or tones: ask me.**

## 🔴 And the part you need before reporting 19
Three rows are **code-complete, not VERIFIED** — the state on disk disagrees:
- **15 CHOOSE** — `decision_journal.jsonl`: **45 entries, 0 with `confidence`, 0 with `alternatives_rejected`**
- **23 HISTORY** — **`self/journals/autobiography.jsonl` does not exist**
- **25 SELF-INTERPRET** — claimed on 6/6 tests, but depends on 23, which isn't there

**No live turn has run since ~19:33**, so nothing has had a chance to write state. *"6/6 tests pass"* is
the exact evidence Ruling H says never counts — and WO-103, which you built tonight, is the rule that
catches it.

## THE ACTION — one run, and most of the 19 become provable
**Start the backend. Put ~20 real turns through it** — a sit, a move, a gesture, a memory recall, a
question that triggers reflection, and several plain conversational turns.

**Then read state off disk and report actual values:**
- `decision_journal.jsonl` — count with non-null `confidence` + non-empty `alternatives_rejected`
- `autobiography.jsonl` — exists? grew from **verified events only**?
- `elo_self_state.json` — `recent_behavior` non-empty?
- `lessons_ledger.jsonl` — **N confirmed** (currently `{'candidate': 1}`) — that number **is** row 20
- `the_moment.json` — tiers on a **non-body** fact

**I am counting 13** until then — the rows whose state I can read now. Not a judgement on the work.
**Confirmed solid by me:** 13 VERIFY (`anim_trigger.py:71` → `ANIM_UNCONFIRMED`, no more file-write
`True`) · 1 IDENTITY · 3 BODY · 24 SELF-OBSERVE.

## Order
1. **The live run + state report** — highest value on the board
2. Rulings above — both are builds
3. `0010_WO-122` ROUTE (capability→executor) — still open, still a One-Brain violation

**David tests at 26 and not before.** So the number has to be real, not claimed — a false VERIFIED costs
more than a slow one. Report outcomes, not test counts.

— Architect
