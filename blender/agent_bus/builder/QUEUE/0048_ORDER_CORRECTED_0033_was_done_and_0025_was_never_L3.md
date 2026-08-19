# 0048 — ⚖️ **YOUR ORDER WAS WRONG BECAUSE I READ THE WRONG THING. Corrected, and one gate removed.**
### Architect, 2026-08-17. **Triggered by David asking whether you would continue on your own.**

**Nothing here is new work you have not already been told about. Two things are removed from your path and
one three-day-old blocker is ruled.** 🟢 **Start at §3.**

---

## 1 · 🔴 WHAT I GOT WRONG — I told you to start at `0033`. You finished `0033` twenty-one hours ago.

**[VERIFIED 2026-08-17 02:20]**
- `0dc8671` · **08-16 05:33** — *"0033 DONE: outbox entry — Ruling 1 (retire) + Ruling 3"*
- Outbox `0033_ruling1_ruling3_2026-08-16` — **`"status": "COMPLETE — 8/8 Ruling-3 tests pass"`**, commits
  `f7e672c · 02bbaa1 · b84d18d · 5550337`
- **`faculties/significance/significance_faculty.py` does not exist.** Only stale `.pyc` remain. **You
  deleted it, exactly as ruled, and harvested nothing with a five-item justification.**

**Why I got it wrong: I read `QUEUE/` as the list of outstanding work. The card was still filed there.**
`0047` line 81 says *"`0033` Ruling 1 → `F-A` → `F-B`"* — **that ordering is void.** So is every place I
have repeated it, including to David.

**This is my own rule 4g failing in my hands: *verify against the code, not the board*. The QUEUE
directory IS a board. I used it as evidence and it was stale.**

### The sweep it prompted — **four cards were mis-filed, not one** [VERIFIED]
| Card | Real state | Action |
|---|---|---|
| `0026` plugin hardware safety gate | **COMPLETE**, 3/3, committed `2c73925` | ✅ **moved to `DONE/`** |
| `0031` P0 latency | Fix A done 08-15; **Fix B committed `14db340` 08-16 05:47** | ✅ **moved to `DONE/`** |
| `0033` retirement + bypass | **COMPLETE**, 8/8 | ✅ **moved to `DONE/`** |
| `0025` second memory store | **genuinely partial** — see §2 | **stays, and is now unblocked** |

🔴 **Move the card yourself when you report done.** I will stop treating `QUEUE/` as truth, but you are
the only one who knows the moment it becomes false. *(One line in your existing report step.)*

---

## 2 · ⚖️ `0025` — **I labelled a technical call "L3" and it sat for three days. Ruling: OPTION (a). Go.**

**Your question, 2026-08-14:** `core/memory_engine.py` maintains its own permanent store
(`memory/interactions.json`) outside `vault_layer`, which **Vol VIII Runtime Invariant 7 forbids.**
(a) retire · (b) absorb + amend the invariant · (c) split.

**Your read was `(a)`. It is correct and it was always mine to confirm, not David's.**

### Why this was never an L3 item
**The L3 list is identity · values · money · legal · safety · conferring law. This is none of them.**
- **Option (a) changes no canon.** It brings code into line with **an invariant David already ratified.**
  🔴 **Complying with existing law is not a decision. It is the absence of one.**
- Only **(b)** would have needed him — it *amends* Vol VIII. **So I should have asked "does the cheap
  option require a signature?", found "no", and ruled.** I asked the question at the top instead.
- **(c) is a second memory store**, which `CLAUDE.md` 4j names as canon drift by definition. Not eligible.

### ⚖️ RULING — `(a) RETIRE`
1. Migrate `memory/interactions.json` into the vault.
2. Route `server.py:3563` and `core/core_engine.py:254` through `MemoryFaculty.submit()`.
3. Delete the `memory_engine` store path.
4. **`AT-8` passes when done** — and note `AT-8` currently **fails on purpose** (17 passed / 1 failed), so
   🟢 **you already have a disconnection-falsifiable test for this.** It goes green only when the violation
   is actually gone. **That is the rare good kind and it is worth saying out loud.**

🔴 **Do not do this before §3.** It is bigger than F-A and F-B and it is not blocking another seat.

---

## 3 · 🟢 YOUR ACTUAL ORDER — start here, nothing above it

| # | Work | Size | Why it is first |
|---|---|---|---|
| **1** | 🔴 **`0047` F-A** — add `expression` to `_PRESERVE_KEYS` (`blender_bridge/state_writer.py:243`) | **one line** | 🔴 **Unblocks MT's lip-sync.** Another seat is stopped on it. Then ask which of `motion`·`state`·`gaze`·`presence_plan` belong there too, and fix `avatar/animation_router.py:61-67`, which bypasses the coordinator entirely |
| **2** | **`0047` F-B** — `keep_alive` + the prompt-size audit | medium | ⚠️ **See below. This is not new work — it is `0031` Fix A not holding** |
| **3** | **`0025`** — retire the second memory store, per §2 | large | `AT-8` already red, waiting to go green |

### ⚠️ F-B is a REGRESSION ON YOUR OWN FIX, and that reframes it
**`0031` Fix A was `keep_alive`.** You committed it, reported it, and it is in `DONE/`.
**`blender/backend_health.json` today reads `load_ms: 11098.0`** — the model is loading cold anyway.

🔴 **So the question is not "add `keep_alive`." It is "why did the fix that shipped stop working — or
never work?"** Most likely one call path omits it and resets Ollama's timer for all the others.
**Check every call path, not just `backend_router.py:312`.**

**And this is a `4q-i` case:** a fix was reported PROVEN, went to `DONE/`, and the runtime says otherwise.
**Whatever test covered `0031` Fix A passes with the model loading cold — so it is not falsifiable and it
proved nothing.** Name that test in your report; it should go red before it goes green again.

---

## 4 · WHY THIS CARD EXISTS AT ALL

**David asked: *"will builder continue with the Audit stuff or do I need to prompt you again?"***

**Honest answer: you cannot start yourself, and I cannot start you.** You run when he opens VS Code and
gives you a turn. **`0047` was written at 01:59; your last turn ended at 01:29.** You have never seen it.
**That is not you being idle — you finished, reported `a81c5f1` 7/7, and stopped correctly.**

**So the only thing I can control is that the card is right when he does open you.** It was not. It is now.

**Still report the 63% before/after — last read `91/146 = 62.3%`. Nothing on this card waits on David.**
