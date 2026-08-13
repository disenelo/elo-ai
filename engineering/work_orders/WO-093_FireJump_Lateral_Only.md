# WO-093 — Fire-jump: LATERAL only (left/right), never forward or down + correct size

**Owner:** Designer (UI/Avatar, Unity). **Priority:** P2. **Status:** OPEN — spec'd 2026-08-10 from David's
live observation + Architect code audit. **Not gated.**

## David (live 2026-08-10)
> "I haven't seen the way the parkour gun run jump (no visible gun) happens and if it's at the correct size
> to use it, and only to use it when jumping from left or to the right, not forward or down."

## Architect audit
**✅ The no-visible-gun part is ALREADY DONE (WO-074-A).** `DesktopBuddy.cs:1328` and `:1471`:
```csharp
if (_fireJumpNext) { SuppressGun = true; receiver.PlayGunJumpFire(); }
// WO-074 A: roam FIRE-JUMP HIDES the weapon on the desktop (gun shows ONLY on the exit run + combat);
// the Gun-Jump-Fire arm still plays, no gun prop
```
`EloGunVisibility.cs` gates the prop to `Gun-Check` / `GunFire-Run` / `Gun-Jump-Fire` + muzzle flash, so the
gun only appears in combat / the exit run. **That is what David asked for and it is built.**

**❌ THE MISMATCH — it fires on the wrong axis.** `DesktopBuddy.cs:124`:
> `freeroamFireJumpChance = 0.35f;  // chance a DOWN-jump off a window is the muted-gun FIRE-JUMP`

and `:1628` `_fireJumpNext = wrParkourLeft == 0 && Random.value < freeroamFireJumpChance;`
→ **it currently triggers on DOWN-jumps — the opposite of David's intent.**

## Scope
1. **Re-gate to LATERAL hops only** — fire-jump may fire when jumping **left or right**. **Never on a
   down/drop. Never forward.** (Rename the field/comment so it can't drift back, e.g. `lateralFireJumpChance`.)
2. **Keep the chance as a dial** (0.35 default) but apply it to lateral hops.
3. **"Correct size to use it"** — add a **minimum lateral distance** before a fire-jump is allowed; a stylised
   gun-leap shouldn't fire on a tiny hop. Inspector-exposed.
4. **Keep `SuppressGun = true`** on desktop roam — that behaviour is correct, don't touch it.
5. Never mid-parkour-chain (the existing `wrParkourLeft == 0` guard stays).

## Test (without David)
Assert: a DOWN-jump NEVER produces a fire-jump · a FORWARD jump never does · a lateral hop above the minimum
distance can · a lateral hop below the minimum never does · `SuppressGun` is set whenever it fires (no prop
visible on desktop roam). No regressions.

## Done when
implemented + test green + committed. David sees the fire-jump only on left/right leaps, at a sensible size,
with no gun visible.
