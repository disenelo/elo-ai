# 06_AUDIT_peek_walljump_firejump.md — why David never sees peek / wall-jump / fire-jump

David (2026-08-10): *"haven't seen the peek down on a window yet, when he walks to the end of the window, and
also not seen any wall jumps (at 45degrees), I haven't seen the way the parkour gun run jump (no visible gun)
happens and if it's at the correct size to use it, and only to use it when jumping from left or to the right,
not forward or down."*

**Architect audit — read-only, facts from code. All three ARE built. Each fails for a DIFFERENT reason.**

---

## 1. PEEK — ✅ BUILT + WIRED, but INVISIBLE (same root cause as the HeadLook bug)
- `DesktopBuddy.cs:198` declares `public static float PeekPitch` — *"read by HeadLook: look toward the jump
  target during the aim beat (peek)"*.
- It IS set in the real flow: `:1275` `PeekPitch = basePeek + Mathf.Sin(Time.time*6f)*3f` — *"gentle 'sizing
  it up' scan"*; `:1300`/`:1302` basePeek; **`:1459` `PeekPitch = _wdHop ? (dy>0 ? -12f : dy<0 ? 18f : 10f) : 18f`
  — "hop: look toward target; drop: look down."** So the peek-down-before-a-drop exists.
- `HeadLook.cs:378` consumes it → `_peekTilt`.
- **WHY DAVID DOESN'T SEE IT:** `_peekTilt` is summed into the SAME additive line
  (`headBone.localRotation * Quaternion.Euler(...)`) that rides on top of the idle animation, and the peek is
  only **10–18°** while the always-on `explore` wander is **±8 yaw / ±12 pitch**. The peek is the same size as
  the random drift and is riding on the idle swing → reads as nothing.
- **FIX: none needed here — it's fixed by `HeadAim`** (card 05/05a). Once the head has an absolute constraint
  aim, re-home `PeekPitch` as an offset on top and it becomes visible. **Do not rebuild peek.**

## 2. WALL-JUMP — ✅ BUILT (45° arc is real), but gated behind a rare combination
- Nav side: `EloDesktopNav.cs:39,83-91,194-226` — wall-jump **zig-zag chimney between two windows' facing
  walls**, with a guard that it must land on a real ledge.
- Avatar side: `DesktopBuddy.cs:274` `_wrWallJump` = *"upward wall-jump (taller springy 45deg arc)"*;
  `:1338` `if (_wrWallJump) arc *= wallJumpArcMul;` → **the 45° springy arc David remembers IS implemented.**
- **WHY DAVID DOESN'T SEE IT — three conditions must ALL hit** (`:1323-1324`):
  ```csharp
  bool parkour = !downL && hopDist <= ParkourReach() && (_forceWallJump || wrParkourLeft > 0 || Random.value < 0.4f);
  _wrWallJump  = parkour && dyL > combatLevelStep;   // must be going UP a level
  ```
  1. **not a down-jump**, 2. within `ParkourReach()`, 3. **wins a 40% dice roll**, AND 4. the target must be
  **UP a level** (`dyL > combatLevelStep`). That needs vertically-stacked windows at the right spacing AND a
  coin-flip. On a normal desktop layout that combination is rare → he almost never sees it.
- **FIX (Designer):** (a) **log every rejection** — which of the four conditions failed (`dyL`, `hopDist` vs
  `ParkourReach()`, the roll) so it's diagnosable instead of invisible; (b) raise the roll / relax the
  up-level requirement so it fires when the geometry genuinely allows; (c) expose the chance + reach in the
  Inspector for David to dial. Compose with the WO-074-F height clamp (card 00) — wall-jump is the intended
  answer to "too far to leap," so the clamp should PREFER it, not suppress it.

## 3. FIRE-JUMP — ✅ BUILT, gun-hiding ALREADY DONE, but firing on the WRONG axis
- **WO-074-A is COMPLETE:** `:1328` and `:1471` — `if (_fireJumpNext) { SuppressGun = true; receiver.PlayGunJumpFire(); }`
  with the comment *"WO-074 A: roam FIRE-JUMP HIDES the weapon on the desktop (gun shows ONLY on the exit run
  + combat); the Gun-Jump-Fire arm still plays, no gun prop."* → **the arm animation plays with NO visible
  gun on desktop roam. That's what David asked for and it's built.**
- `EloGunVisibility.cs` gates the prop to the gun states (`Gun-Check`, `GunFire-Run`, `Gun-Jump-Fire`) and
  handles the muzzle flash — so the gun only appears in combat/exit-run.
- **THE MISMATCH David just found:** `:124` `freeroamFireJumpChance = 0.35f` — *"chance a **DOWN-jump** off a
  window is the muted-gun FIRE-JUMP"*, and `:1628` `_fireJumpNext = wrParkourLeft == 0 && Random.value < 0.35f`.
  **So it currently fires on DOWN-jumps.** David wants the **OPPOSITE**:
  > "only to use it when jumping from left or to the right, **not forward or down**."
- **FIX (Designer) — this is a real behaviour change, do it:**
  1. **Gate fire-jump to LATERAL hops only** — jumping left or right. **Never on a down/drop, never forward.**
  2. Keep the 35% chance as a dial, but apply it to lateral hops.
  3. **"Correct size to use it"** — David is questioning the scale: add a **minimum lateral distance** before a
     fire-jump is allowed (a stylised gun-leap shouldn't fire on a tiny hop) and expose it in the Inspector.
  4. Keep `SuppressGun = true` on desktop roam — that part is right.

---

## Summary for the board
| Behaviour | Built? | Why not seen | Owner fix |
|---|---|---|---|
| Peek before jump/drop | ✅ yes, wired | swamped: additive on idle + only 10–18° vs ±12° wander | fixed by **HeadAim** (card 05) — don't rebuild |
| Wall-jump 45° | ✅ yes, arc real | needs up-level + in-reach + **40% dice roll** → rare | log rejections · relax/raise · Inspector dials |
| Fire-jump, no gun | ✅ yes, **WO-074-A done** | fires on **DOWN-jumps**; David wants **lateral only** | re-gate to left/right + min distance |

**Nothing here needs rebuilding from scratch. Two small gates and one head-aim fix.**

## Result
- commit: 9208ff7
- fire-jump: re-gated to lateral-only + min 0.18vp (never drop/forward); faces jump dir; gun hidden
- wall-jump: wallJumpChance Inspector dial (0.5) + per-reject logging [card06 walljump]
- peek: deferred to HeadAim (card 05) per audit — not rebuilt
