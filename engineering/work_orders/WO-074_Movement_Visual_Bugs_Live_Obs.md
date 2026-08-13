# WO-074 — Movement / visual bugs (David live observation 2026-08-07)

**Status:** OPEN — spec'd 2026-08-07. **Priority:** P2 (visible "feels wrong", not a finish-line-6 blocker;
behind WO-073 mute-brain). Three distinct issues, routed to the owning seat.

## A. Fire-jump shows the GUN — it must be HIDDEN (▶ DESIGNER)
The `fire_jump` move renders with a visible gun/weapon prop on the DESKTOP eLo. It should NOT — the desktop
avatar is reusing the eLo-Planet rig's fire_jump clip, which carries the weapon. David flagged this to the
Designer before and was told it wouldn't happen — but it IS happening, so that confirmation was wrong.
▶ **Designer:** hide/strip the weapon prop on the desktop embodiment's fire_jump (disable the gun GameObject
in the desktop rig / clip). Confirm it's off by default across ALL moves, not just patched on one. Verify by
triggering fire_jump and checking no weapon renders.

## B. Fire-jump TRIGGERS on the wrong condition (▶ BUILDER question first, then gate)
David sees `fire_jump` fire (1) **while standing still** (no movement, no command — a self-trigger), and (2)
during window-to-window running jumps. (2) may be legitimate traversal; (1) is a misfire.
▶ **BUILDER — the question David asked me to put to you:** does eLo OS ever EMIT `fire_jump` / a `move_command`
**autonomously** (when David isn't commanding, eLo standing still), or are autonomous moves purely
Designer/Unity-driven? This decides the owner:
  - If eLo OS emits it → Builder: gate autonomous fire_jump on actual movement/context (don't fire from idle);
    same presence-gating principle as the earlier autonomous-warp/wave-mid-conversation fix.
  - If it's Unity-autonomous → Designer: gate the autonomous fire_jump so it only plays during a real
    window-to-window traversal, never from a standing idle.

## C. eLo parks in the MIDDLE of the window — doesn't use the full edge (▶ DESIGNER)
On a window, eLo tends to stand centre rather than roaming the full length of the window edge. He should
traverse/attach along the actual edge extent, not sit mid-window.
▶ **Designer:** window-edge nav — eLo roams to the full edge length (WindowRoamStep / edge-attach), not a
centre bias. Ties the desktop-world nav (049-A / EloDesktopNav).

## D. Peek up / peek down not showing (▶ DESIGNER — David live 2026-08-07)
The pre-jump PEEK (head-look toward the target — down before a drop, up before a wall-jump/leap) is not
rendering. `PeekPitch` is set in the roam/jump aim but the head isn't visibly looking. ▶ **Designer:** confirm
`PeekPitch` is actually driving the head (HeadLook / the peek during the jump-aim window) and restore the
visible look-toward-target before a leap. Verify: a window-to-window jump shows a clear look down/up first.

## E. Emotion glow shows THROUGH the window when he's behind it (▶ DESIGNER — David live 2026-08-07)
When eLo is behind a window (occluded / warped out), his belly/emotion glow still renders over the window.
▶ **Designer:** gate the glow (EloBodyGlow / emotion glow) on the SAME occlusion state as the body — HIDE it
while he's behind a window / warped out, and SHOW it the moment he reappears (David: "show it when he
appears"). Tie into `EloWindowOcclusion`. Verify: behind a window = no glow; steps out = glow returns.

## F. Jumps too FAR — should PATHFIND a route, not leap (▶ DESIGNER — David live 2026-08-08)
To reach a window, eLo LEAPS directly (and overshoots / jumps too far) instead of finding a ROUTE across
available surfaces to get there. He should prefer a traversable path (walk/step/short-hop along reachable
surfaces) and only leap when there's no route. ▶ **Designer:** route-finding in the desktop nav — evaluate
reachable surfaces and pick a PATH to the target window; leap only as the last option; tune jump distance so
he doesn't overshoot. Ties WO-074-C (edge roam) + the earlier "not looking for downward routes" gap + the
Affordance/Body-Map work (jump range vs reach). Verify: given a window a route away, eLo traverses to it
rather than a single over-long leap.

## Notes
Sequenced behind WO-073 (the mute brain — can't fairly judge behaviour while eLo's on the mock). A/C/D/E are
Designer; B is a Builder clarification → then whichever seat owns the trigger gates it. Verify each visually
(David L3) + a log/inject check where possible.
**A DONE (Designer `fa009bc`, 2026-08-07 — corrects `d7d47c6`):** the ROAM fire-jump now suppresses the gun (`SuppressGun=true` at the two launch sites) so no weapon renders on it; the **EXIT run (shoot-and-run-off) + combat KEEP the gun** (David L3 clarification: exit should show it). Combat + exit reuse the same Gun-Jump-Fire/GunFire-Run clips, so it's context-gated, not clip/global. (`d7d47c6`'s showWeapon master was too broad — killed the exit gun — reverted.)
