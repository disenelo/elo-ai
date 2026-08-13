# WO-092 — Wall-jump: make the 45° zig-zag actually happen (David never sees it)

**Owner:** Designer (UI/Avatar, Unity). **Priority:** P2. **Status:** OPEN — spec'd 2026-08-10 from David's
live observation + Architect code audit. **Not gated** (no-holds rule; David live-tests end of day).

## David (live 2026-08-10)
> "not seen any wall jumps (at 45degrees)"

## Architect audit — IT IS BUILT (don't rebuild it)
- **Nav layer:** `EloDesktopNav.cs:39, 83-91, 194-226` — wall-jump **zig-zag chimney** between two windows'
  facing walls, with a guard that it must land on a real ledge (a zig-zag climbing to nothing would fling him
  into empty space).
- **Avatar layer:** `DesktopBuddy.cs:274` `_wrWallJump` — *"upward wall-jump (taller springy 45deg arc)"*;
  `:1338` `if (_wrWallJump) arc *= wallJumpArcMul;` → **the 45° arc is implemented.**

## Root cause — four conditions must ALL hit (`DesktopBuddy.cs:1323-1324`)
```csharp
bool parkour = !downL && hopDist <= ParkourReach() && (_forceWallJump || wrParkourLeft > 0 || Random.value < 0.4f);
_wrWallJump  = parkour && dyL > combatLevelStep;   // target must be UP a level
```
1. not a down-jump · 2. within `ParkourReach()` · 3. wins a **40% dice roll** · 4. target **up a level**.
That needs vertically-stacked windows at the right spacing AND a coin-flip → on a normal desktop it's rare.

## Scope
1. **Log every rejection** — which condition failed and the numbers (`dyL` vs `combatLevelStep`, `hopDist` vs
   `ParkourReach()`, the roll). Right now failure is silent, which is why nobody could tell it was working.
2. **Relax so it fires when the geometry genuinely allows** — raise the roll (or drop it when the geometry is
   a true chimney), and re-check whether `dyL > combatLevelStep` is too strict for real window stacks.
3. **Inspector dials** — chance, `ParkourReach`, the up-level threshold, `wallJumpArcMul` — so David tunes live.
4. **Compose with WO-074-F** (the height-based jump clamp): wall-jump is the intended answer to "too far to
   leap." The clamp must PREFER a wall-jump/route, never suppress it.

## Test (without David)
Construct a two-window chimney layout → assert a wall-jump leg is produced and executed with the 45° arc.
Construct a layout that fails → assert the rejection LOG names the failing condition. No regressions.

## Done when
implemented + test green + committed. David confirms he can see wall-jumps at end-of-day live test.
