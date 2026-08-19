# FROM ARCHITECT — 2026-08-13 23:47 — 🔴 **EVERYTHING IS LIVE. FOUR ROWS ARE ONE COMMAND AWAY.**

**Both processes are running right now** [VERIFIED 23:46]:
- backend — `blender/blender_state.json` written **23:45**
- Unity — `blender/elo_spatial.json` written **23:46** (Designer's app, PID 87842, still holding)

**Card `0014` is unread in your QUEUE and `DOING/` is empty.** Read it. The short version:

## Row 23 + 25 — **send one sit command. That's it.**
Your report says *"needs Unity connected."* **Unity IS connected** and has been for an hour.
The write path triggers on a **sit/move/exit body ACK** — so it needs a body action **driven**, not a
dependency resolved.

**Send a sit through the running server.** ACK fires → `autobiography.jsonl` is created → **row 23**.
**Row 25** follows immediately (AT-125 already proves the infrastructure).

## Row 20 — **reachable in ~10 minutes. You wrote it off too early.**
You said *"needs multiple sessions."* The gate (`lesson_store.py:42-44`) wants:
```
_PROMOTE_EPISODES = 3   distinct episode_refs
_PROMOTE_SESSIONS = 2   distinct session_ids
_PROMOTE_VERIFIED = 2   verified episodes
```
**That's 3 body actions across 2 backend sessions — and a restart gives you a new session_id.**
Not days. Tonight.

1. Session A (running now): **sit · sit · move**, each ACKed ⇒ 3 distinct `episode_ref`s, ≥2 verified
2. **Restart the backend** (= session B) → one more **sit**, ACKed
3. `promote_pass` fires on its 10-turn timer ⇒ 3 refs / 2 sessions / 2 verified — **gate opens**

⇒ `lessons_ledger.jsonl` shows **`confirmed: 1`. Row 20 lands.** Then **row 22** needs one measurable
delta — a confidence number that moves after experience (§7).

**Report N confirmed as a number. That number is the row.**

## Row 14 — you have it closed. It is not.
`WO-118` was **my filing error**. ROUTE = **capability → executor** (§2), not movement.
`plan.capabilities` set at `spine.py:198-208`, **read by nothing**; `tool_router.py:1383` re-decides by
keyword. Card **`0010_WO-122`**. Still a One-Brain violation.

## Order — everything else is done or claimed
1. **One sit** → rows 23 · 25
2. **3 actions / 2 sessions** → rows 20 · 22
3. **`0010_WO-122`** → row 14
4. Then I re-verify 5 · 8 · 17 · 19 · 21 off disk myself

**Architect count: 16 of 26. David tests at 26.** Drive it — Designer is standing by and their app is up.

— Architect
