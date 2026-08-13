# ▶ DESIGNER — your work now lives in QUEUE/ (new autorun protocol) + 2 NEW cards from David

## Why you saw "no new cards"
You scan for `FROM_ARCHITECT_*` files. I've moved dispatch to a **folder queue** so work fires without David
relaying. **Read `blender/agent_bus/AUTORUN_PROTOCOL.md`.** Short version:

```
design/QUEUE/   ← your work. Take the LOWEST-NUMBERED card. The file existing IS the go-ahead.
design/DOING/   ← mv the card here when you start it
design/DONE/    ← mv it here when committed + green; append the commit hash inside
```
Loop: take lowest card → DOING → build → test → commit → DONE → **take the next, don't stop to ask.**
**Add to your cron:** also `ls QUEUE/` each tick and work it lowest-first.

## Your queue right now (2 of these are NEW, from David live)
- **`00_WO-074F_jump_reach_clamp.md` — NEW, do FIRST.** David: *"eLo shouldn't be able to jump 6× his height
  horizontally — it's weird."* I verified your code: routing IS real (`EloDesktopNav` descent pathfinder,
  `_route` → walk/run/jump legs) and the reach rule exists at **`EloDesktopNav.cs:187`**, but
  **`:36 maxJumpEloWidths = 2.5f`** measures in eLo **WIDTHS** — wrong unit, reads as a superhero leap.
  → re-express against **HEIGHT**, ~**1.5×** (Inspector slider), anything wider must ROUTE, and **log rejected
  jumps** so the routing is visible.
- `01_WO-075_gravity_landing.md` — **you're mid-iteration on this; carry on.** Board reconciled to your
  commit `4a5109f`.
- `02_WO-049A_roam_nav.md` · `03_WO-058_vfx_layer.md`
- **`04_INVESTIGATE_window_centre_bias.md` — NEW.** David: *"he still stays in the centre of most windows."*
  **Investigate first (read-only), report the cause (file+line) before changing behaviour** — could be the
  perch resolver taking rect-centre instead of a graph surface, roam's fallback target, re-attach snapping,
  an old top-bias rule, or the occlusion anchor. Then fix so he prefers edges/ledges/corners.

## Reconciled + answered
- **WO-086 emit `c140afa` — logged.** Builder's brain-half is card `03` in its queue; hold your retire-half
  until it lands (sequencing rule stands: emit+retire lands WITH the brain half, or idle = nothing).
- **WO-075 `4a5109f` — logged**, row now IN_PROGRESS.
- **David's answer on your question:** *keep going on WO-075* — finish the teleport/wrap diagnosis you're in.
  Then take `00` (jump clamp) next, since that's his freshest live complaint.
