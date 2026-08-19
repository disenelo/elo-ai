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
