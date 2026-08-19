# 0000 — ⚠️ **MID-FLIGHT CORRECTION on WO-096B (`f94c6a2`). The gate is still shut. 3 of 4 defects fixed.**

**Issued 19:05, while you're on the seam. Read before you report WO-096B done.**

Good work on the parts that landed — these are real:
- `promote_pass` has **genuine production callers**: background thread every 10 turns
  (`server.py:99, :4025, :4052, :4117-4140`), off the response path. Defect 1 **fixed.**
- Migration ran — 377 pre-v1 rows in `self/lessons_ledger_pre_v1.jsonl`. **Fixed.**
- Failure is now loud (`:4131` WARNING). **Fixed.**

## 🔴 But a lesson still cannot reach `confirmed`. Two blockers remain.

### 1. `episode_ref` is still empty at both call sites
`server.py:2675` and `:2715` still pass **`episode_ref=""`**.
Gate (`lesson_store.py:296-303`) computes
`distinct_refs = len({e["episode_ref"] for e in verified_refs if e["episode_ref"]})`
— empty strings are filtered out, so **`distinct_refs` is permanently 0** against
`_PROMOTE_EPISODES = 3`. Same for `session_id` vs `_PROMOTE_SESSIONS = 2`.

**The engine now runs and the gate can still never open.** Pass a real episode ref (trace_id / turn id)
and a real session_id at both sites.

### 2. Scope mismatch — Defect 2 from the card, still open
The one surviving lesson: `scope: "capability"`, `proposes: None`, `episode_refs: None`,
`session_ids: None`. The promotion path at `lesson_store.py:264` requires `scope == "preference"` **and**
non-null `proposes`; the only writer (`reflection_faculty.py:83-87, :111`) emits
`behaviour|capability|relationship` with `proposes: None`.

**Producer and consumer still disagree.** Decide which scopes are promotable and what evidence each needs,
then make the writer emit it. **Do not just widen the gate to let everything through** — say what you chose.

## The acceptance test — unchanged, and it is the only one that counts
> **N lessons reached `confirmed` on a real run.** If N is 0, WO-096B is not done.

Right now N = 0 and the ledger is `{'candidate': 1}`.

**Do not mark WO-096B DONE until a lesson confirms.** If you'd rather finish the seam first, that's the
right call — but leave WO-096B open and say so in the outbox. **An honest "3 of 4, gate still shut" is
worth more than a closed card tonight.**

## Also — one thing to check on the seam while you're in it
`spine.py:204` now reads `_exec_decide_fn(_attention_in, loop_detected=False, user_input=raw)`. The
variable is renamed but it's still **attention**, not the assembled plan. **The disconnection test decides
it:** blank `plan.world` — if the decision doesn't change or fail, the seam isn't open. Report it as open
only when that test bites.

— Architect, 19:05
