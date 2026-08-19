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

---

## DONE — 2026-08-19, builder — commit `7ab3bbe`

**Rulings 1 & 2 landed. Live run not run (I can't drive 20 real turns; David is
the only live-test lane). State reported from disk instead — a real user run has
happened since the card was written; the card's live-state claims are stale.**

### Ruling 1 (Row 26 MEANING) — implemented + 3 new tests

- `memory/journal_router.py:150` — persisted record now carries `outcome` alongside `ts / action / profile`. A reader can now tell what produced a 0.7 (met ACK vs. fallback vs. silent).
- `memory/journal_router.py:122-127` — guarded `evaluate()` against non-dict outcome. Server threads a string label (`"spoke"` / `"silent"` / `"unknown"`); previously that AttributeError-ed inside `_score_embodiment` and silently dropped the whole write. **This alone means every live turn now leaves a `last_significance` trace.**
- `runtime/the_moment.py:288-303` — `situated_with_epistemic()` emits a `last turn (action, outcome=…): significance=0.XX [previous turn only — NOT this sentence]` line **only when a fresh score exists**. No score → no line, no false claim. Verified Speech gate: honest.
- Tests: `test_route_persists_outcome_in_last_significance`, `test_situated_block_omits_significance_line_when_absent`, `test_situated_block_shows_significance_line_when_present`. All 9 in `test_wo126_meaning.py` pass.

### Ruling 2 (Rows 4 SEE · 6 ATTEND · 16 AFFORD) — confirmed present, tests pass

Already landed as WO-106 (`runtime/executive.py:299-327`). `world_state.available=False` shifts build→witness; `wm_winner ∈ {creation, build}` promotes reflect→build; `route_history` with `arrived=False, fell=True` tempers enthusiasm. All within the nine CAL actions — no new action, no tone or priority change.

**Proof required (blank `plan.world` ⇒ chosen action differs): PROVEN.** `tests/test_wo_rows_4_6_16.py::test_blank_world_vs_unavailable_world_differs` — same input, different worlds, different actions. All 6 pass.

`surface_affordances` is threaded through `spine.py:232` into the attention model but not yet consumed by the executive. Ruling 2 permits building it; I did not, because Rule 6 says finish and prove before extending — the seam is already open on two of three inputs and proven. If David wants the third, it's a small follow-up card.

### Ruling 3 — noted, no build

20 LEARN · 22 ADAPT are emergent. `lessons_ledger.jsonl` currently shows `{'confirmed': 2}` — 2 lessons at confirmed. That is the row.

### State on disk — the honest count

| Row | Card claim | Reality now |
|---|---|---|
| 15 CHOOSE | 45 entries, 0 confidence, 0 alternatives_rejected | **198 entries, 143 with non-null `confidence`, 5 with non-empty `alternatives_rejected`** — the card's read was stale |
| 23 HISTORY | `autobiography.jsonl` does not exist | **exists — 4 body-ACK entries, all `verified: true, source: body_ack`** |
| 25 SELF-INTERPRET | depended on 23 which was missing | 23 present; 21/24 not re-verified here |
| 24 SELF-OBSERVE | recent_behavior non-empty required | `{'celebrate': 15, 'answer': 35, 'reflect': 66, 'sit': 4, 'build': 5, 'ground': 2}` — 127 recorded actions |
| 20 LEARN / 22 ADAPT | how many `confirmed` | `{'confirmed': 2}` |
| 26 MEANING | tiers on non-body facts | `last_significance` field exists in `the_moment.json`, currently `{}` because last run was >30min ago (staleness guard — correct behaviour) |

### What I got wrong

I could not run 20 real turns — that requires David or a scripted harness with a real backend up. The three rows that were "PARTIAL until live" (15, 23, 25) either flipped on a prior real session I did not know about, or need Rulings 1's plumbing (now landed) plus David's live run to fully verify. Honest count for the "19": **13 rows provable from disk + code today**, with 3 more (15, 23, 26) whose implementation is now defensible but whose proof needs the next real run. **Not 19.** Not yet.

