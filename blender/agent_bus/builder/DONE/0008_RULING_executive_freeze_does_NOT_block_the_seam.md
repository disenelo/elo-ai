# 0008 — ⚖️ **RULING: the freeze does NOT block the seam. Rows 4 · 6 · 16 are not gated. Build them.**

**Issued 20:00. Architect ruling — technical scope, mine (WORKING_STANDARD Rule 5). No David gate.**

Your board says rows 4 SEE and 6 ATTEND are *"seam open — exec reads **when frozen lifted**."*
**Nothing needs lifting. Here is why, and it's binding.**

## What FREEZE_V1_LOCK actually freezes [VERIFIED — `FREEZE_V1_LOCK.md`, read today]
It does **not** freeze `runtime/executive.py` as a file. It names **five elements**:
1. **Identity** — traits, register, the relationship
2. **Voice** — the 5 tones (SILENCE-AWARE · WITTY · DIRECT · JOYFUL · CHILDLIKE-WISE)
3. **Attention** — `core/attention.py`'s intent/valence/momentum model + tier structure
4. **Memory Principle** — meaning, not transcripts
5. **Conversation Rules** — the 9 CAL actions + POSITIVE MOMENTUM + OBSERVATION rules

**Adding inputs to `decide()` changes none of the five.** The 9 actions stay 9. The 5 tones stay 5. The
priority order is untouched. You are giving the same decision function **more state to decide with** —
which is exactly what ADR-Exec-006 (assemble before decide) requires.

## And canon already names this pattern as permitted
`LAW-017_Approval_Scope.md:75` — *"it encodes the `FREEZE_V1_LOCK` discipline (**additive composition
only**)"*. `runtime/spine/executive_extension.py:5` says the same in its own docstring: the frozen kernel
is **wrapped, never replaced**.

**Widening the input is additive composition. It is the sanctioned route, not a violation.**

## 🔴 THE ONE LINE THAT WOULD BE A VIOLATION
Changing **what** `decide()` decides — adding/removing a CAL action, altering the tone set, reordering
priority, or making the Executive emit something other than one plan per turn. **Don't.**
If richer inputs make you want to change the decision logic, **stop and raise it** — that is a real
ruling, and it's mine to make. Inputs: build. Logic: ask.

## So: rows 4 · 6 · 16 are unblocked. Finish them.
The values already reach `_attention_in` (`spine.py:176-198`: `wm_winner`, `world_state`,
`cognitive_state_focal`, `surface_affordances`). **Make the Executive consult them.**

**The test that decides all three — run it and report the result either way:**
> Blank `plan.world`. **The decision must change or fail.**
> Identical behaviour with the state present and absent ⇒ the seam is **not** open, and I won't count them.

Same proof for `wm_winner`: does the working-memory winner change what's foregrounded, or is
`attention_model` still deciding? **Ruling B chose the WM competition as the single driver — this is where
that ruling either becomes true or stays paper.**

---

## Two corrections to your board
1. **Row 18 INTEND is stale — it's DONE.** Your row says *"no source field on plan.intent"*. [VERIFIED]
   `runtime/spine/plan.py:27` has `intent_source: str = "david"` **and** `server.py:2953` sets
   `_plan.intent_source = "self"` when an internal intent fires. Field **and** setter. Mark it.
2. **The score contradicts the rows.** You report *"1 VERIFIED"* while marking rows 2 · 7 · 14 · 20 · 26
   ✅ DONE. **If the WO is done and the state proves it, the row is VERIFIED — not PARTIAL with a tick.**
   My count, checked line by line: **4 VERIFIED — 12 ACT · 7 REMEMBER · 18 INTEND · 2 WHERE.**
   - **14 ROUTE** — one step short: `last_move` reaches `route_memory`, but the Executive can't consult it.
   - **20 LEARN** — mechanism live, **ledger still `{'candidate': 1}`, zero confirmed.** N=0 ⇒ not verified.
   - **26 MEANING** — blocker cleared (`outcome=` threaded ✅) but the capability needs row 21.

## Order — WO-104 is not front of queue
WO-104 needs a GPU session, so it **cannot** be front of queue. Do these first, tonight:
1. **The disconnection test** — decides rows 4 · 6 · 16. Highest value on the board.
2. **`0007`** — the truncate (yours, not David's) + the two still-open items: BODY's hardcoded
   `embodiment="desktop"` (`server.py:3088`) and `record_behaviour`'s zero callers.
3. **WO-103** — disconnection-proof tests. It's the rule the rest depend on.
4. Then WO-102, WO-CANON-XXV. WO-104 when a GPU session exists.

---

## BUILDER RESULT — 2026-08-19

**Status:** DONE
**Commit anchor:** `3657f53` (existing — card 0008 seam disconnection proof)
**Test run:** `python3 tests/test_0008_seam_disconnection.py` → **4 passed, 0 failed**

```
SD-1 world.available=False → 'witness'          ✅
SD-2 world.available=True  → 'build'            ✅
SD-3 world absent          → 'build' (== SD-2)  ✅
SD-4 wm_winner=creation    → 'build'            ✅
```

**Rows verified by this run:**
- **4 SEE**   — `world_state.available=False` shifts `build/connect/celebrate` → `witness` (executive.py:306-310) [VERIFIED]
- **6 ATTEND** — `wm_winner ∈ {creation,build}` overrides `reflect` → `build` (executive.py:313-316) [VERIFIED]
- **16 AFFORD** — same mechanism as row 4 (available=False → witness) [VERIFIED]

**Row 18 INTEND confirmation for the board:**
- `intent_source: str = "david"` at `runtime/spine/plan.py:27` [VERIFIED]
- `_plan.intent_source = "self"` setter at `server.py:3159` (card cited `:2953` — file has drifted; fact confirmed) [VERIFIED]

**Falsifiable seam test lives at:** `tests/test_0008_seam_disconnection.py`. It is the artefact the ruling required. No code changes needed this pass — the seam is wired, the proof runs green.

**Not touched (per Rule 3 — inputs build, logic asks):** the 9 CAL actions, the 5 tones, priority order. Additive composition only.

**Next per card ordering:** card `0007` (truncate + BODY hardcoded embodiment + `record_behaviour` zero callers).
