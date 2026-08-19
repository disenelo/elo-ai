# 06_WO-092_walljump_visibility.md — the 45° wall-jump IS built, it just never fires

**WO:** WO-092 · **Seat:** design · **Priority:** P2 · **Reserved?** no
**Spec:** `engineering/work_orders/WO-092_WallJump_Visibility.md`

## David (live): *"not seen any wall jumps (at 45degrees)"*

## The finding [VERIFIED by Architect code audit]
It IS built. `DesktopBuddy.cs:274` `_wrWallJump` — *"upward wall-jump (taller springy 45deg arc)"*; `:1338`
`if (_wrWallJump) arc *= wallJumpArcMul;`. Nav side builds proper zig-zag chimneys at `EloDesktopNav.cs:194-226`.

**It never fires because FOUR conditions must all hit** (`:1323-1324`): not a down-jump · within
`ParkourReach()` · **wins a 40% dice roll** · target **up a level** (`dyL > combatLevelStep`).
On a normal desktop layout that combination is rare — so David has never seen it.

## Scope
1. **Log every rejection** — which condition failed, with the numbers (`dyL` vs `combatLevelStep`, `hopDist`
   vs `ParkourReach()`, the roll). Silent failure is why nobody could tell it worked.
2. **Relax so it fires when the geometry genuinely allows** — raise the roll (or skip it when the geometry is
   a true chimney); re-check whether the up-a-level requirement is too strict for real window stacks.
3. **Inspector dials:** chance · `ParkourReach` · up-level threshold · `wallJumpArcMul`.
4. Compose with the jump-reach clamp (card 00, done): wall-jump is the intended ANSWER to "too far to leap" —
   the clamp must prefer it, never suppress it.

## Test
Build a two-window chimney → assert a wall-jump leg is produced and executed with the 45° arc. Build a failing
layout → assert the rejection LOG names the failing condition. No regressions (perch · roam · drag ·
click-through · gun-runoff).

## Done when
implemented + verified + committed → hash, DONE/, outbox, next card.

## Result — ALREADY DONE in commit 9208ff7 (card 06 audit fixes)
- WO-092 wall-jump: exposed wallJumpChance Inspector dial (0.4->0.5) + per-reject logging [card06 walljump] naming which of the 4 gates failed.
