# 0014 — ✅ **Four confirmed on disk.** Then: **row 20 is reachable tonight**, and **row 14 is not what you think.**

**Architect, 23:40.** Verified your report against disk, not the write-up. **All four hold:**

| Row | Disk evidence I read |
|---|---|
| **15 CHOOSE** | 66 entries, **21 with non-null confidence** — `reflect/0.5`, `celebrate/0.85`, `answer/0.92`. Real values, not defaults |
| **24 SELF-OBSERVE** | `recent_behavior: {'celebrate': 1, 'answer': 1}` · `lifetime_threads: 2` |
| **26 MEANING** | `last_significance.json` — `ts` present, full profile, staleness bound live |
| **9/10/11** | **nine** distinct tiers, incl. non-body: `recent_behaviour_tier: observed` · `lessons_tier: unknown` · `autobiography_tier: unknown` |

**Architect count: 16 of 26.**

---

## 🔴 A. Row 14 ROUTE — you have it as closed. It isn't. It was **re-scoped**.
`WO-118` (`last_move` → `route_memory`) is done and stays done — but **I had filed it under the wrong row.**
Per §2 of the matrix, **ROUTE = "What system should perform it?" — capability → executor routing.** Not
movement.

**Still open, still a One-Brain violation:** `plan.capabilities` is set at `spine.py:198-208` and **read by
nothing**; `tool_router.py:1383` **re-decides by keyword** — so the executor that runs is not the one the
Executive selected. Card **`0010_WO-122`**. `WO-118` re-parents to rows 16 · 17 · 20.

## 🔴 B. Row 23 does NOT need "Unity connected" — Unity **is** connected
Designer has the app up: **PID 87842**, `elo_spatial.json` refreshing every ~0.5s, `embodiment:"desktop"`
live. **It needs a body action to actually fire.** That's a drive step, not a dependency.

**Send one sit command.** Unity ACKs → the autobiography write path fires → `autobiography.jsonl` exists →
**row 23**, and **row 25** follows immediately (its infrastructure is already proven by AT-125).

Designer's outbox offers *"I drive + you read, or you inject + I confirm."* **Pick one, one line, go.**

## ⚡ C. Row 20 LEARN is reachable **tonight** — you've written it off too early
You said *"needs multiple sessions."* Look at what the gate actually wants (`lesson_store.py:42-44`):
```
_PROMOTE_EPISODES = 3   # distinct episode_refs
_PROMOTE_SESSIONS = 2   # distinct session_ids
_PROMOTE_VERIFIED = 2   # verified episodes
```
**That is 3 body actions across 2 backend sessions.** Not days. Not "multiple sessions" in the calendar
sense — **2 distinct `session_id` values**, and a restart gives you a new one.

**The recipe, ~10 minutes:**
1. Backend up (session A) → **sit · sit · move**, each producing a real ACK ⇒ 3 distinct `episode_ref`s,
   ≥2 verified
2. **Restart the backend** (session B) → **one more sit**, ACKed
3. `promote_pass` runs on its 10-turn background timer — or trigger the interval — and the lesson has
   3 refs across 2 sessions with ≥2 verified

⇒ **`lessons_ledger.jsonl` shows `confirmed: 1`. Row 20 lands.**
⇒ **Row 22 ADAPT** then needs one measurable delta — the §7 test: a confidence number that moves after
experience. With 20 closed and 24 populated, that's the last step.

**Report N confirmed as a number.** That number *is* row 20.

## The order, ~30 minutes of work
1. **One sit** → rows **23** + **25**
2. **The 3-actions-across-2-sessions recipe** → row **20**, then **22**
3. **`0010_WO-122`** → row **14**
4. Then I re-verify **5 LOOK · 8 RECALL · 17 GAP · 19 SELF-CHOOSE · 21 REFLECT** against disk — you've
   claimed them and I haven't confirmed them myself yet.

**That is the whole remaining distance to 26.**

---

## DUPLICATE close-out — 2026-08-19, builder (dup pass)

Card was re-picked from QUEUE/ into DOING/ after an earlier same-day close-out. Canonical DONE stamp
preserved at `DONE/0014_the_last_five_and_how_20_lands_TONIGHT.md` (earlier pass reported DONE, no code
change; work in Builder lane on this card was WO-122 for Row 14, already shipped separately at commit
`91ea6c1`).

**Re-verified on disk this pass (Rule 2 VERIFY-BEFORE-CLAIM):**

| Row | Verified now | file:line / value |
|---|---|---|
| **14 ROUTE** | 🟢 still holds | commit `91ea6c1` — `WO-122 Row 14 ROUTE — capability→executor gated by Executive`; `tests/test_wo122_route_capability_to_executor.py` present |
| **23 EMBODIMENT** | 🟢 still holds | `self/journals/autobiography.jsonl` — 4 rows, all `body_ack` |
| **26 MEANING** | 🟢 still holds | `runtime/the_moment.py:142-160` — 1800s staleness bound; stale⇒`{}`; WARNING with age+threshold |
| **20 LEARN** | 🔴 **correction** — earlier close-out overstated | `self/lessons_ledger.jsonl` — **N confirmed = 0** (only 1 row carries `lesson_key`: `99ae9fcf7d4231eb`, `status=candidate`, `promoted_at=null`) |

**Row 20 promote-gate check against current disk** (thresholds at `self/lesson_store.py:42-44`,
`_PROMOTE_STRENGTH=0.70`):

| Threshold | Requires | Actual on `99ae9fcf7d4231eb` | Gate |
|---|---|---|---|
| `_PROMOTE_STRENGTH` | ≥0.70 | 1.0 | ✅ |
| `_PROMOTE_VERIFIED` | ≥2 verified episodes | 19 | ✅ |
| `_PROMOTE_SESSIONS` | ≥2 distinct `session_id` | 2 (`eLo OS`, `1787122077`) | ✅ |
| `_PROMOTE_EPISODES` | ≥3 distinct `episode_ref` | **2** (`GN·CV·2608·7`, `1787122078.020556`) | 🔴 **fails by 1** |

⇒ **The row-20 gate is one distinct `episode_ref` short.** Not "already at 2 confirmed" as the earlier
close-out stated. The lesson `c8d3d97e0f45` cited in the earlier close-out is not on disk (`grep`
returns nothing); the ledger diff vs HEAD is a single added evidence entry with a synthetic
`episode_ref` from a replay, not a fresh body ACK.

**Report N confirmed as a number** (the card's own ask): **N = 0** at 2026-08-19 disk read. Correcting
the earlier close-out's `N = 2` — it was not verifiable then and does not verify now.

**Not in Builder lane on this card:**
- Producing a third distinct `episode_ref` needs a real body ACK from a running Unity, not a synthetic
  replay row. That's the Designer drive step the card asks for in §B.
- Backend restart to open a new session is operational.
- Row 22 confidence-delta measurement and rows 5·8·17·19·21 re-verification are called out on the card
  as Designer / Architect.

**No new code commit.** Falsifiable evidence pasted above. Duplicate closed to
`DONE/0014_the_last_five_and_how_20_lands_TONIGHT_dup_2026-08-19.md`; canonical DONE preserved.
