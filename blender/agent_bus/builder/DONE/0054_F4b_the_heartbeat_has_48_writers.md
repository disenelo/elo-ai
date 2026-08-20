# 0054 — 🔴 **F4-b · THE HEARTBEAT RE-CREATES THE DEFECT IT WAS BUILT TO FIX**
### **LAYER:** `[IMPLEMENTATION]` — defect in F4 as shipped (`026b2ab`). **Reconciling open work, not a new investigation.**
### **STATE: AUTHORISED** · Lead Architect 2026-08-17 · **P1 — before the baseline freeze**

🟢 **F4 is right in mechanism.** `patch({})` advancing only `_ts` is exactly the correct shape, and
`_PRESERVE_KEYS` from F-A is what makes it safe. **The problem is who runs it.**

---

## 1 · THE DEFECT — [VERIFIED 2026-08-17 22:20]

**`blender_bridge/state_writer.py:326`** — `_start_heartbeat()` is called **at module level, unconditionally,
with no guard.**

**And `state_writer` is imported by at least twelve processes** *(48 files reference it)*:
```
server.py · tools/vision_loop.py · tools/computer_control_agent.py · tools/image_gen_agent.py
tools/model_gen_agent.py · faculties/perception/perception_faculty.py
runtime/spine/presence_faculty.py · runtime/cognitive_snapshot.py · desktop/file_drop_handler.py
tests/test_fa_preserve_keys.py · tests/test_f4_heartbeat.py · tests/test_wo030b_weather_publish.py
```

### 🔴 Three consequences, and the third is the serious one

**1 · Every one of those becomes a writer to the live channel.** `_STATE_LOCK` is an **in-process** lock.
It gives no protection between `server.py` and `vision_loop.py` — **separate processes, separate locks, same
file, every 30 seconds.**

**2 · Test runs now write to the live channel.** Importing `state_writer` in a test spawns a thread that
patches `blender/blender_state.json`. **A test can leak into the running system, and a heartbeat can fire
mid-assertion.**

**3 · 🔴 THE HEARTBEAT NO LONGER MEANS WHAT IT WAS CREATED TO MEAN.**
> **The contract says:** `_ts` advancing is how a surface distinguishes *"eLo is here and quiet"* from
> *"eLo is gone."*
>
> **As shipped:** `image_gen_agent.py` running alone will advance `_ts` **with no spine, no Executive and no
> eLo.** MT's widget would read "present."

**That is the same false-presence defect in a new form — and it is worse than the original**, because the
original was a *silence* we could not interpret and this is a *signal* that is wrong.

---

## 2 · ⚖️ THE FIX — one heartbeat, one owner

| # | Change |
|---|---|
| **1** | 🔴 **Remove the module-level `_start_heartbeat()` call.** Import must have no side effects |
| **2** | **The spine starts it explicitly** — one call from `server.py` at startup, and nowhere else. **`server.py` is the only process entitled to assert eLo's presence** |
| **3** | **Guard it anyway** — a module-level flag so a second call in the same process is a no-op, and an env opt-out for tests |
| **4** | **A test that FAILS if a non-spine import advances `_ts`.** 🔴 **That is the falsifiable one** — import `state_writer` in a bare process, wait past the interval, assert `_ts` did **not** move |

**✅ PROVEN when:** `_ts` advances with `server.py` running, **and does not advance** when only a tool or a
test imports the module.

---

## 3 · WHY THIS IS IN SCOPE THIS PHASE
**F4 was authorised on `0053`. This is a defect in the thing just built — David's own step 3,
*"reconcile skipped/withdrawn changes."*** 🔴 **It is not a new investigation and it introduces nothing.**
**It must land before the runtime baseline is frozen, or we freeze a channel that lies about presence.**

---

## 4 · WHAT I GOT WRONG ON `0053`
**I wrote F4 as *"done when `_ts` advances while no other field changes"* and never asked *"advanced by
whom."*** **Same shape as asking for a falsifiable test without naming the proposition.** You built exactly
what the card specified. **The card was underspecified in the one dimension that mattered.**

---

## 5 · CLOSE-OUT — Builder seat 2026-08-20

**Reconciliation card.** The four required changes already landed in commit **`a59ab1b`**
(`0054: heartbeat one owner — remove module-level call, wire to server.py only`).

**Verified 2026-08-20 by Builder seat (Rule 2 — Independent Runtime Verification):**

| # | Change | State |
|---|---|---|
| 1 | Module-level `_start_heartbeat()` removed | `blender_bridge/state_writer.py:322` — `start_heartbeat()` is a function, never called at import |
| 2 | Spine starts it explicitly | `server.py:76-77` — `start_heartbeat as _sw_start_heartbeat` + `_sw_start_heartbeat()` at startup |
| 3 | Module-level guard + env opt-out | `state_writer.py:313` `_heartbeat_started` flag; `state_writer.py:328` `ELO_STATE_HEARTBEAT=0` opt-out |
| 4 | Falsifiable test | `tests/test_0054_heartbeat_owner.py` — T1 (no thread on bare import), T2 (`_ts` does not advance without start), T3 (second call is no-op), T4 (env opt-out honoured) |

**Test evidence re-run 2026-08-20:**
- `python3 tests/test_0054_heartbeat_owner.py` → **4/4 PASS** (T1–T4)
- `python3 tests/test_f4_heartbeat.py` → **3/3 PASS** (T1, T2, T3) — F4 mechanism intact

**✅ PROVEN.** `_ts` advances only when `server.py` calls `start_heartbeat()`. Bare imports (tools, tests)
do not spawn the thread. Falsifiable test T2 goes RED if the module-level call is ever put back.

**Result:** DONE via reconciliation. No new commit — code already correct in `a59ab1b`.
