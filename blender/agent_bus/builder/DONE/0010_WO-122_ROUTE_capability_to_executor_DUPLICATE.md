# 0010_WO-122 — **ROUTE (row 14), correctly defined this time.** The Executive picks a capability and the router ignores it.

**Seat:** builder · **Priority:** P1 · **Gate?** none
**Correction issued 20:20 — my misreading, owned below.**

## 🔴 ARCHITECT ERROR — I mapped this row to the wrong thing
The source (§2, `_intake/SOURCE_2026-08-13_capability_truth_matrix.md:77`) defines ROUTE as:

> **ROUTE | What system should perform it? | capability → executor routing | `executor` | 🟡**

**That is capability → executor routing.** I read "route" as **movement pathfinding** and pointed the row
at `EloDesktopNav` and Ruling E. Wrong row, wrong lane, wrong WO.

*(The movement work still stands and is not wasted — `last_move` → `route_memory` is what **AFFORD (16)**,
**GAP (17)** and **LEARN (20)** need for a learned `reliable_range`. It was mis-filed, not misspent.
`WO-118` stays, re-parented under 16/17/20.)*

## The actual gap [VERIFIED — and I had already found it, under the seam]
- `spine.py:198-208` sets **`plan.capabilities`** — the Executive's decision about what capability applies.
- **Nothing reads it.** Grep: `plan.capabilities` appears only in `spine.py` itself.
- `tools/tool_router.py:1383` / `:1232` **re-decides by keyword** and dispatches from `_AGENTS` (`:827`),
  gated by the registry at `:1065-1068`.

**So the Executive chooses, the router ignores the choice and picks again from the raw text.** Row 12 ACT
is VERIFIED because the chain *executes* — but **the executor is not the one the Executive selected.**
That is a One-Brain violation hiding inside a passing row.

## Build — §9 step 4, "identify the executor"
1. **`plan.capabilities` gates dispatch.** A capability the Executive did not select **cannot** run.
2. **The routing decision is recorded** — which capability, which executor, why that one. Pairs with
   **row 15 CHOOSE** (`WO-112`): the executor choice is part of the decision record, not a side effect.
3. **Keyword re-decision is removed**, or demoted to a *proposal* the Executive confirms. If you find a case
   where keyword routing catches something the Executive misses, **report it — don't keep both silently.**
   Two deciders is the fault, not the fallback.
4. **Unknown capability ⇒ loud.** No silent fallback to a default executor (Rule 1).

## Test (without David)
- **Disconnection test:** blank `plan.capabilities` ⇒ dispatch **fails or changes.** If the router behaves
  identically, the Executive's choice still isn't being used and this card is not done.
- A capability the Executive rejected **cannot** be executed by keyword match.
- The decision record names the executor and the reason.
- Unknown capability raises/logs — never silently defaults.

## Done when
Committed. **Outbox: proof that a keyword-matched executor no longer runs when the Executive didn't select
it.** That single test is the row.

## Board corrections I'm making alongside this
- **Row 14 ROUTE** re-scoped to capability→executor. **WO-118 re-parented to rows 16 · 17 · 20.**
- Row 14 is **not** VERIFIED and was never close — I had it one step away for the wrong reason.

---

## DUPLICATE CLOSE-OUT — 2026-08-19 · builder

**This card is a duplicate re-queue of work already shipped at `91ea6c1` (2026-08-19 06:57).**
The canonical DONE stamp lives at `DONE/0010_WO-122_ROUTE_capability_to_executor.md`
(recorded in commit `15224af`). Nothing new to build.

### Verification this pass (VERIFY-BEFORE-CLAIM, Rule 2)
- Re-ran `python3 tests/test_wo122_route_capability_to_executor.py` — **5/5 pass**.
  - RT-1 (disconnection) ✅ blank `plan.capabilities` → weather agent did NOT fire.
  - RT-2 ✅ Executive-selected `weather` ran.
  - RT-3 ✅ Executive-selected `time` on weather-worded query — weather did NOT fire.
  - RT-4 ✅ Unknown capability → loud WARN log, no dispatch, no keyword fallback.
  - RT-5 ✅ Direct intercepts (lore) still fire without plan capabilities.
- Confirmed `tools/tool_router.py::enrich_from_plan()` (line 1425) still gates
  dispatch by `plan.capabilities`; no keyword fallback path present.
- Confirmed `server.py:3534-3536` still passes `plan.capabilities` into
  `enrich_from_plan()` (the reader that was missing before the fix).

### Action
Closed as duplicate. Moved to `DONE/0010_WO-122_ROUTE_capability_to_executor_DUPLICATE.md`
to avoid clobbering the canonical DONE stamp.

**Original commit that landed the work:** `91ea6c1`
**Original DONE-move commit:** `15224af`
