# ▶ DESIGNER — dispatch (David live obs 2026-08-07) — WO-074 A + C

Two Designer-lane bugs David saw live. Full spec: `../../engineering/work_orders/WO-074_Movement_Visual_Bugs_Live_Obs.md`.
Sequenced behind the brain fix (WO-073) but they're yours to build.

## A. Fire-jump shows the GUN — must be HIDDEN
`fire_jump` on the DESKTOP eLo renders a visible gun/weapon prop (from the eLo-Planet rig's clip). It must NOT
show a weapon on the desktop embodiment. David flagged this to you before and was told it wouldn't happen — it
IS happening, so that needs a real fix, not a re-confirm.
- Disable/strip the weapon GameObject on the desktop rig so NO move renders it (default-off across all moves,
  not a one-clip patch). Verify: trigger fire_jump → no weapon visible.

## B (context — Builder's question, not yours to answer)
Whether fire_jump self-triggers from idle is being clarified with the Builder (does eLo OS emit it
autonomously?). If it turns out to be Unity-autonomous, you'll gate it so it only plays during a real
window-to-window traversal, never from a standing idle. Hold until the Builder answers.

## C. eLo parks in the MIDDLE of the window — should use the full edge
On a window eLo tends to stand centre instead of roaming the full length of the window edge. Fix the desktop
nav (WindowRoamStep / edge-attach, EloDesktopNav) so he traverses the actual edge extent, not a centre bias.

Report to outbox as usual; David's check is visual (no gun on fire_jump; eLo roams the full edge).

## ▶ UPDATE 2026-08-07 (Architect): A/D/E done + committed (fa009bc · a4c62a7 · 51094f1) — awaiting David's eyeball. **C: GO NOW.**
Take C (window-edge roam — WindowRoamStep/edge-attach) immediately — it's independent nav, doesn't need
David's eyeball to start, no reason to wait on the A/D/E visual confirm. Ship + commit + outbox as usual.
While you're in the desktop-nav code: **WO-075 (gravity/drop-to-nearest-window, same drop-line + screen-wrap)**
is the next desktop-world item after C — same `EloDesktopNav`/`EloWindowSensor` area, so keep it in mind.
