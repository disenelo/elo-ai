---
id: WO-028
title: "eLo Presence avatar — fix the wave gesture + arm rotation (blocks avatar reaction gestures, incl. INT-8 drop)"
owner_seat: SEAT-ENG-004 (UI/Avatar, Unity)
occupant: UI/Avatar (Unity)
priority: P2
reason: "David 2026-08-02: the arm rotation / waving isn't working. This blocks any avatar reaction gesture — including INT-8's 'eLo takes the dropped file'. Pull the wave/arm fix out of the Presence tracker into a real WO."
review_required: L1 → L3 (David confirms the wave looks right in Play)
risk: low (avatar animation; DesktopBuddy/Presence project — not eLo-Planet game)
status: READY — needs David's exact symptom to tighten
created: 2026-08-02
blocks: INT-8b (avatar drop reaction gesture)
---

# WO-028 — wave gesture + arm rotation fix

**David's words:** *"We don't have anything setup for the arms rotating that is working — we still need
to fix the waving situation."*

## What's known (from the repo + tracker)
- Arm **aim IK** solver works: `ArmDeformIK` (analytic two-bone, confirmed 2026-06-14).
- Arm **hold/mask layers** flagged ⚠️: `eLo_ArmHoldR/L` clips + arm IK on deform bones — "needs Play test."
- "Wave gesture tuning (frames/cycles/tilt)" sits in `PRESENCE_TRACKER §2` (never dispatched).
- So: the aim solver is fine, but the **wave gesture / arm rotation doesn't play correctly** — likely a
  clip/mask-layer wiring, bone-target, or blend-weight issue on the deform bones.

## Task
1. **Diagnose** why the wave/arm rotation doesn't work: is the wave clip firing? is the arm mask layer
   weighted in? are the deform-bone targets bound? does aim-IK fight the wave clip (layer conflict)?
2. **Fix** so eLo can **wave and rotate its arm** on demand — a clean, repeatable wave gesture.
3. Make it **triggerable** (a `wave` motion/trigger channel eLo OS can fire, like the movement triggers)
   so gestures can be invoked (waving hello, and later "taking" a dropped file for INT-8b).
4. Play-test the arm-hold mask layers alongside it (resolve the ⚠️).

## Acceptance
1. eLo performs a clean wave (arm rotates through the wave, returns to rest) in Play mode.
2. No conflict between wave clip and aim-IK (layers coexist or gate correctly).
3. Wave is fireable via a trigger channel; arm-hold mask layers pass Play test.
4. David confirms the wave looks right → DONE. Handback: short recording + the clip/layer fix diff.

## Notes
- **NEEDS DAVID'S EXACT SYMPTOM to tighten:** does the arm not rotate at all, does the wave clip not fire,
  or does it fire into the wrong pose / get overridden? One line from David sharpens the diagnosis.
- Unblocks **INT-8b** (avatar drop-reaction gesture). INT-8a (drop → read round-trip) is independent and
  can proceed now without this.
