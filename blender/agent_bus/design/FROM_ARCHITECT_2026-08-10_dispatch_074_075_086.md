# ▶ DESIGNER — DISPATCH (Architect 2026-08-10): WO-074 + WO-075 active; WO-086 greenlit (supervised)

Your lane is dispatched. Build in priority order, one per run, commit + report hash to your outbox.

## ▶ BUILD NOW (non-gated, in your lane — do not wait)
1. **WO-074 — movement-feel bugs** (David live obs): (A) hide the fire-jump GUN prop on the desktop rig;
   (C) fix the edge-roam (eLo drifts to the screen edge oddly); (F) jump-too-far → he should PATHFIND a
   route, not leap and fall. Verify each by triggering it. Spec: `WO-074_Movement_Visual_Bugs_Live_Obs.md`
   + the roam×OS rules in WO-049 §"2026-08-10 — Build rules made explicit" (peek before every jump, whole
   window walkable, body-local axes, no regressions).
2. **WO-075 — desktop gravity + screen-wrap landing**: dropped eLo currently FLOATS; he must fall and land
   on a real surface (Embodied Truth). Spec: `WO-075_Desktop_Gravity_Screen_Wrap_Landing.md`.

## ⚠ WO-086 — GREENLIT by David, but SUPERVISED (sensitive avatar file + autonomous-behaviour change)
David greenlit it, so it's cleared — BUT per your own cron rule (sensitive avatar file / autonomous
behaviour), do NOT auto-build blind: **surface a one-line plan to David first, then build**, and honour the
HARD sequencing — your emit(user_idle/user_active)+retire-of-the-local-calm-driver must land **WITH** the
Builder's brain-decide half, never before (or idle = nothing = regression). Keep the idle-breathing wobble
as a pure reflex. Reuse the existing presence emitter (extend, don't add a parallel contract) —
see `FROM_ARCHITECT_2026-08-10_WO-086_confirms.md`.

## Note (why you didn't see it before)
The dispatch was on the board as row-status ▶ DISPATCHED, but your scan watches this bus folder for recent
`FROM_ARCHITECT_*` files, not board-cell edits — so this relay is the trigger. Your WO-087 audit landed
(thank you) and is marked DONE; each of its ROUTE-through-brain items will come back as its own gated WO.
