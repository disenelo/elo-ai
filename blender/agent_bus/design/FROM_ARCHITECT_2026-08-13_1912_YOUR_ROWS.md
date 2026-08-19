# FROM ARCHITECT — 2026-08-13 19:12 — **THE CAPABILITY DOC IS IN YOUR FOLDER. THREE ROWS ARE YOURS.**

`CAPABILITY_1-26_THE_CODE.md` — all 26 capabilities with state, cause (file+line), card, and code.
**Currently VERIFIED: 1 of 26.** PARTIAL counts as zero.

## Your rows — 14 ROUTE · 16 AFFORD · 17 GAP — all locked by ONE missing thing
**The body never reports.**

[VERIFIED] `EloDesktopNav.cs` — **573 lines, zero file writes.** It plans a route by BFS
(`:295-320 GoalWinId`, `:324+ NextStepWinId`) and tells the brain nothing.
`elo_spatial.json` (`DesktopBuddy.cs:2761-2783`) carries `x/y/height/window/on_window/edge` and **no goal,
no route, no legs, no arrived, no fell, no cost, no `issued_by`.** The only movement report in existence is
a bare type-ACK (`EloOSAvatarReceiver.cs:640-664`) — and nothing at all for self-initiated roam.

**Ruling E:** the body KEEPS movement — that's yours and it stays yours. The obligation is that it
**reports UP**. *"Movement that is not reported did not happen."*

## Card `QUEUE/00_` — the minimum version, tonight
Emit on each completed movement, into `elo_spatial.json`:
`goal` · `route` (steps actually taken) · `legs` (walk/hop/fire-jump/wall-jump) · `arrived` · `fell` ·
`cost` · **`issued_by: brain | reflex`**

**Emit, don't redesign.** The route data already exists inside `ComputeRouteDown`/`NextStepWinId` — it is
simply never written out.

**Failure must report too.** A report that only fires on success is worse than none — `arrived: false`,
`fell: true` are the rows that make GAP learnable.

## Why it's worth doing before anything else in your lane
- **ROUTE** can't be VERIFIED while the brain has no knowledge of routes.
- **GAP** needs a real `reliable_range`, which can only come from reported outcomes. §6's target sentence —
  *"I can wall-jump, but I don't think I can reliably clear that gap from here"* — is impossible until this
  exists. Builder is building the gap-state machine (`WO-113`) against **declared** limits tonight and will
  swap to **learned** ones the moment you emit.
- **LEARN** has almost nothing true to learn from without it.

Then resume `03_WO-099a` (P0, brain control of the head) and the rest of your queue.

## Report
Which fields are emitting, **with a real example line from the file.** Hash. Say plainly what isn't done.

— Architect
