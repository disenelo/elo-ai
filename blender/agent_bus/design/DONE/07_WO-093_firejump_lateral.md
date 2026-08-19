# 07_WO-093_firejump_lateral.md — fire-jump fires on the WRONG axis

**WO:** WO-093 · **Seat:** design · **Priority:** P2 · **Reserved?** no
**Spec:** `engineering/work_orders/WO-093_FireJump_Lateral_Only.md`

## David (live)
> "only to use it when jumping from left or to the right, **not forward or down**" — and *"if it's at the
> correct size to use it"*.

## The finding [VERIFIED by Architect code audit]
**The no-visible-gun half is ALREADY DONE** (WO-074-A): `DesktopBuddy.cs:1328`/`:1471`
`if (_fireJumpNext) { SuppressGun = true; receiver.PlayGunJumpFire(); }` — the arm animation plays with no
gun prop on desktop roam. `EloGunVisibility.cs` gates the prop to the gun states. **That part is right.**

**But the axis is backwards.** `:124` — *"chance a **DOWN-jump** off a window is the muted-gun FIRE-JUMP"*,
and `:1628` `_fireJumpNext = wrParkourLeft == 0 && Random.value < freeroamFireJumpChance;`
→ **it currently fires on DOWN-jumps. David wants lateral only.**

## Scope
1. **Re-gate to LATERAL hops only** (left/right). **Never a down/drop. Never forward.** Rename the field +
   comment (e.g. `lateralFireJumpChance`) so it can't drift back.
2. Keep the chance as a dial (0.35 default), applied to lateral hops.
3. **Minimum lateral distance** before it's allowed — David's "correct size" point; a stylised gun-leap
   shouldn't fire on a tiny hop. Inspector-exposed.
4. **Keep `SuppressGun = true`** — that behaviour is correct, don't touch it.
5. Keep the existing `wrParkourLeft == 0` guard (never mid-parkour-chain).

## Test
Assert a DOWN-jump never produces a fire-jump · a FORWARD jump never does · a lateral hop above the minimum
can · below the minimum never does · `SuppressGun` set whenever it fires. No regressions.

## Done when
implemented + verified + committed → hash, DONE/, outbox, next card.

## Result — ALREADY DONE in commit 9208ff7 (card 06 audit fixes)
- WO-093 fire-jump: re-gated to LATERAL-only (horiz dominates 1.5x, roughly flat) past fireJumpMinLateral 0.18vp; never drop/forward; faces jump dir (DirectionalYaw); gun prop hidden (SuppressGun).
