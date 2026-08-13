# ▶ DESIGNER — DISPATCH (Architect 2026-08-10 06:25): WO-074 + WO-075 active; WO-086 greenlit (supervised)

Re-relay — your prior dispatch relay had aged past your scan window. Nothing changed vs it; this just
re-triggers your 5-min scan. Build in priority order, one per run, commit + report hash to your outbox.

## ▶ BUILD NOW (non-gated, in your lane — do not wait)
1. **WO-074 — movement-feel bugs** (David live obs): (A) hide the fire-jump GUN prop on the desktop rig;
   (C) fix the edge-roam; (F) jump-too-far → PATHFIND a route, not leap and fall. Verify each by triggering it.
   Spec: `WO-074_Movement_Visual_Bugs_Live_Obs.md` + roam×OS rules in WO-049.
2. **WO-075 — desktop gravity + screen-wrap landing**: dropped eLo FLOATS; he must fall and land on a real
   surface (Embodied Truth). Spec: `WO-075_Desktop_Gravity_Screen_Wrap_Landing.md`.

## ⚠ WO-086 — GREENLIT by David, SUPERVISED (sensitive avatar file + autonomous-behaviour change)
Cleared, but per your own cron rule: surface a one-line plan to David first, then build. Honour the HARD
sequencing — emit(user_idle/user_active)+retire-of-the-local-calm-driver lands **WITH** the Builder brain-decide
half, never before. Keep idle-breathing wobble as a pure reflex. Reuse the existing presence emitter (extend,
don't add a parallel contract). See `FROM_ARCHITECT_2026-08-10_WO-086_confirms.md`.

## Reminder
Write your `outbox.json` after each commit so the Architect can reconcile your state without guessing from git.
