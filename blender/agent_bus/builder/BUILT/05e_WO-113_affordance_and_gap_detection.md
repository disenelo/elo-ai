# 05e_WO-113 — **AFFORD + GAP (rows 16, 17).** Affordances are computed every turn and thrown away.

**Seat:** builder · **Priority:** P1 · **Gate?** none · **Rows:** 16, 17 → VERIFIED
**Depends:** Ruling E (Designer `00_`) for real `reliable_range`. **Build the rest now — don't wait.**

## Finding [VERIFIED]
`runtime/affordances.py:17-57` **is computed on the live path** — `cognitive_snapshot.py:175-176`, stored
`:252`, pinned into the plan `spine.py:427-428, :463`.
**Nothing reads it.** `affordances.prompt_block` (`affordances.py:60-71`) has **zero non-test callers**.
It is also surface-keyed only: **no join with body capability** (`state.size`, `elo_self_model.py:157`),
and `reachable_areas` (`:160`) is `[]` in live state.

## Build
1. **Affordance = world geometry ∩ body capability ∩ confidence.** Not a surface lookup.
2. Route it to the **Executive**, not the prompt (pairs with `WO-106`).
3. **GAP as a first-class answer (§6)** — seven states, never yes/no:
   `CAN · CANNOT · CAN-BUT-DEGRADED · CAN-BUT-LOW-CONFIDENCE · CAN-IF-CONDITION · UNKNOWN · BLOCKED`
4. Each carries the numbers behind it:
   ```
   WALL_JUMP  status: AVAILABLE  confidence: 0.87
   gap_distance: 240px   reliable_range: 200px
   → UNRELIABLE_FROM_CURRENT_POSITION
   ```

**Until Ruling E lands**, `reliable_range` has no learned value. **Use the declared limit from the
navigator** (`EloDesktopNav.cs:35 maxJumpEloHeights = 1.5f`; real hop gate `DesktopBuddy.cs:260-261
MaxHopDist()`) and mark it `source: declared` not `source: learned`. **Say which it is in the state** —
do not let a declared constant masquerade as experience.

## Test (without David) — §6's own example
eLo says: *"I can wall-jump, but I don't think I can reliably clear that gap from here"* — **and the
`gap_distance` / `reliable_range` behind it are real numbers from state**, not adjectives.
- All seven gap states are reachable; assert at least four on real scenarios.
- Change the body size ⇒ the affordance changes (proves the capability join is real).

## Done when
Committed. **Outbox: the seven states with a real example of each you could trigger, and one gap answer
with its numbers.**
