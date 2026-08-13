# 01_WO-075_gravity_landing.md

**WO:** WO-075 · **Seat:** design · **Priority:** P1 · **Reserved?** no

## Goal
eLo always lands on a real surface. Dropped on empty desktop he currently FLOATS where placed — he must fall
and land on a window/ledge (Embodied Truth: his position is always real and on a surface).

## Scope — exactly this
- Add gravity/fall to the drag-drop placement path: on release with no surface under him → fall.
- Land on the nearest valid surface below (reuse `EloWindowSensor` + `EloDesktopNav` surface graph).
- Screen-wrap / off-screen edge: he reappears and lands on a surface, never lost in empty space.
- Reuse the existing `drop` move — do NOT build a parallel movement driver.

## Files likely touched
DesktopBuddy: the drag-drop/placement handler + the existing drop/land path. Do not touch the sensitive
avatar file beyond what the WO needs.

## Test (without David)
Inject a drop on empty desktop → log/verify he falls and ends ON a surface (not floating). Confirm no
regression: perch · roam · drag · click-through · gun-runoff still work.

## Done when
implemented + verified + committed → append hash, move to DONE/, line in outbox.json, take next card.
Spec: `engineering/work_orders/WO-075_Desktop_Gravity_Screen_Wrap_Landing.md`

## Result
- commit:
- test:

## Result
- commit: 0b44a8c (+ prior 4a5109f)
- test: build clean; live-tuned with David (fall/land/wrap/teleport-fix, whole-window walkable)
