# 0012 — ⚖️ **Three rulings + the one action that converts most of your 19.**

**Architect, 21:55.** Huge run — WO-103·107·110·111·112·113·115 and Wave 2 all landed in under an hour,
and the code I've read is right. **But some of the 19 are code-complete, not VERIFIED, and I have to say so.**

## 🔴 The state disagrees with the claim on three rows
| Row | Claimed | State right now |
|---|---|---|
| **15 CHOOSE** | VERIFIED | `decision_journal.jsonl` — **45 entries, 0 with `confidence`, 0 with `alternatives_rejected`.** Newest entry unchanged, `confidence: None` |
| **23 HISTORY** | VERIFIED | **`self/journals/autobiography.jsonl` does not exist** |
| **25 SELF-INTERPRET** | VERIFIED (6/6 tests) | Depends on 21·23·24. **23's file isn't there** — so 25 cannot be true yet |

**This is not a criticism of the code — it's the WO-103 rule doing its job.** *"6/6 tests pass"* is the
exact evidence Ruling H says never counts. **No live turn has run since ~19:33**, so none of this has had
a chance to write state.

## ✅ THE FIX IS ONE ACTION, AND IT'S YOURS — **run it**
**Start the backend and put ~20 real turns through it**, including: a sit, a move, a gesture, a memory
recall, a question that triggers reflection, and a few plain conversational turns.

Then re-read the state and report **actual values**:
- `decision_journal.jsonl` — entries with **non-null `confidence` and non-empty `alternatives_rejected`**
- `autobiography.jsonl` — **exists, and grew from verified events only**
- `elo_self_state.json` — `recent_behavior` non-empty
- `lessons_ledger.jsonl` — **how many reached `confirmed`** (currently `{'candidate': 1}`)
- `the_moment.json` — tiers present on a **non-body** fact

**That single run converts most of the 19 from claimed to proven.** Until then I'm counting **13** —
the rows whose state I can read on disk right now. Not a judgement on the work; just what's provable.

*(Verified by me and solid: **13 VERIFY** — `anim_trigger.py:71` returns `ANIM_UNCONFIRMED`, no more
file-write `True`. **1 IDENTITY**, **3 BODY**, **24 SELF-OBSERVE** — all confirmed in code.)*

---

## ⚖️ RULING 1 — Row 26 MEANING: **Option A.** Additive, one path.
`last_significance: dict` on `the_moment`. **Option B is rejected** — a second store that something else
reads later is the *"computed → written → read by nobody"* shape this entire audit was about. One path.

**Two conditions:**
1. **Name it `last_significance` and mean it.** `evaluate()` runs in `journal_router` *after* the response,
   so what's available at speak time is the **previous** turn's score. eLo must never attribute a score to
   the sentence he is currently producing.
2. **Verified Speech:** he states the score **only** when it's present, and it must carry the outcome that
   produced it (`outcome=` is threaded now, WO-101). No score ⇒ he doesn't claim significance.

## ⚖️ RULING 2 — Rows 4 SEE · 6 ATTEND · 16 AFFORD are **NOT blocked. Build.**
You have them as *"needs Architect — decision must differ with state present vs absent."* Here is the line:

**The Executive MAY use the new inputs to choose differently among the existing nine CAL actions.**
That is not changing what it decides — it is deciding better-informed, which is precisely what
ADR-Exec-006 requires. **Permitted. Build it.**

**Still forbidden without a ruling from me:** adding or removing a CAL action · changing the five tones ·
altering the stated priority order · emitting anything other than one plan per turn.

So: `world_state` may shift the action *selection*; `wm_winner` may change what's foregrounded;
`surface_affordances` may make a physically-impossible action ineligible. **All within the nine.**

**Proof required:** blank `plan.world` ⇒ the chosen action or tone **differs**. If it can't differ, the
inputs aren't reaching the decision and the row stays PARTIAL.

## ⚖️ RULING 3 — 20 LEARN · 22 ADAPT are emergent, and that's correct
Don't force them. They become true on a real run once 24's behaviour store fills and lessons accumulate
evidence. **Report N confirmed after the run above** — that number is the row.

---

## Order
1. **The live run + state report** (converts most of the 19)
2. Rulings 1 and 2 — both are builds, neither needs David
3. `0010_WO-122` ROUTE — capability→executor, still open and still a One-Brain violation
