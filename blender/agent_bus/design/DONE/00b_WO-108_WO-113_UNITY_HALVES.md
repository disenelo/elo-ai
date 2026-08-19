# 00b — **Rows 5 LOOK and 17 GAP: your halves. Build them in parallel with Builder.**

**Seat:** design · **Priority:** P1, after `00` · **Gate?** none

## Row 5 — LOOK (≠ SEE). Your half: the inspection, not the head turn.
**SEE** = passive perception. **LOOK** = eLo *deliberately* inspecting something and getting an answer back.
Right now a directed look **rotates a bone and produces no knowledge** — gaze reaches you
(`EloOSAvatarReceiver.cs:419-425` → `HeadLook.cs:402-422`) and nothing comes back.

**Your half:** when the brain sends a look target, **report what was actually there.**
- What is under the gaze — window id / owner / rect (reuse `EloWindowSensor` + `IsTopmostAt`, already built)
- Whether it was **occluded, absent, or off-screen** — the failure cases matter more than the success
- Timestamp + a confidence

Builder builds the observation record and the request side (`builder/QUEUE/05f`). **You supply the truth
it records.** Without your half, eLo can claim to have looked at something he never resolved.

## Row 17 — GAP. Your half: the numbers behind "can I clear that?"
Target sentence (from the spec): *"I can wall-jump, but I don't think I can reliably clear that gap from
here."* That needs **real numbers**, not adjectives:
```
gap_distance: 240px   reliable_range: 200px   → UNRELIABLE_FROM_CURRENT_POSITION
```
**`gap_distance` is yours** — you already compute it (`ClosestJump`, `EloDesktopNav.cs:447-452`; hop gate
`DesktopBuddy.cs:260-261 MaxHopDist()`). **Emit it** alongside the `last_move` block you shipped at 19:30.

**`reliable_range` becomes *learned* from your outcome reports** — that's why `arrived:false` / `fell:true`
rows matter more than the successes. Builder is building the 7-state machine against **declared** limits
and swaps to **learned** the moment enough outcomes exist.

⚠️ One thing worth telling Builder: the nav graph gate (`maxJumpEloHeights = 1.5f`, `EloDesktopNav.cs:35`)
and the **actual** hop gate (`MaxHopDist()`, `DesktopBuddy.cs:260-261`) are **different rules**. eLo jumps
by one and plans by the other. **Emit the one that actually governs the jump**, and say which it is —
otherwise `reliable_range` will be learned against a number that doesn't decide anything.

## Test (without David)
- Directed look at an occluded window ⇒ reported as occluded, **not** as observed.
- `gap_distance` emitted per jump decision, with the governing limit named.
- A failed jump reports `arrived:false` with the distance that beat it.

## Done when
Both emitting, hashes in the outbox, **and the field names agreed with Builder in writing.**
