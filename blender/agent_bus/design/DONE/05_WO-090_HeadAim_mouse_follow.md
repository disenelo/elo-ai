# 05_WO-090_HeadAim_mouse_follow.md

**WO:** WO-090 — HeadAim · **Seat:** design (Unity) · **Priority:** P2 · **Reserved?** no
**Source (VERBATIM, read it):** `docs/architecture/_intake/SOURCE_2026-08-10_headaim_mouse_follow.md`
David flagged this was raised before and **lost in the loop** — it does not get lost again.

## Goal (David's words)
> "so the mouse cursor can I make a Multi Aim Constraint that follows the Mouse and set a mouse target as the
> constraint for the to rotate … and then use that for when eLo follows the cursor sometimes, or when a cursor
> (in a text box is actively moving he can watch it)"

eLo's HEAD follows what's happening on screen — the mouse, and a text caret that's actively moving. This is
the foundation for the head interacting with screen events generally.

## Scope — exactly this (David's spec, his numbers, do not reinterpret)
- **Unity Multi Aim Constraint** on the head. Call it **`HeadAim`**.
- **CONSTRAINED OBJECT = THE HEAD BONE** (David, 2026-08-10 — added right after the first spec). The
  constraint drives the head BONE directly, not a proxy/parent transform. Same bone-driven approach that made
  `ArmWave` work (WO-028: bone rotation, mask dropped, Inspector-exposed bone name). Expose the head bone name
  in the Inspector so David can point it at the rig's actual bone if the default is wrong.
- **A mouse target object** is the constraint's target — it follows the mouse cursor position.
- **Rotation limits: min −100 to 100 max.**
- **Target follows the source object at about 0.305.**
- **Smooth movement** — David: *"I need as a smooth movement."* No snapping, no jitter; damped follow.
- Use it for: (a) eLo **sometimes** follows the cursor — not constantly, it should read as noticing, not
  tracking like a turret; (b) when a **text caret is actively moving in a text box**, he can watch it.

## ChestAim — second constraint layer (David, 2026-08-10)
> "And we can add chest aim as well, we can do a lighter weight, dynamic to rotate with the head but at a
> lower level and rotate the shoulders and upper chest bone."

- **Second Multi Aim Constraint: `ChestAim`**, constrained object = **upper chest bone + shoulders**.
- **Lighter weight than the head** — it rotates WITH the head but at a **lower level/amount**, so the head
  leads and the chest follows subtly. That's what makes it read as a body turning to look, not a head
  swivelling on a static torso.
- **Dynamic** — the chest contribution follows the head's aim rather than being a fixed pose.
- Expose weight + bone names in the Inspector so David can dial the head:chest ratio live.
- Rotation limits should stay tighter on the chest than the head (the head does the reaching; the chest only
  leans). Exact chest limits are David's dial — start conservative.

## THE MODEL: a natural stack rotation (David, 2026-08-10 — this is the governing idea)
> "So think of it in a natural stack rotation if you rotate the head you rotate the torso as well a little,
> and as the arms are attached to the shoulders if I add different animaations it will blend well"

**Build it as ONE stack, not two independent constraints.** Rotating the head propagates DOWN the chain with
decreasing influence — that's what makes it look like a body, not parts:

```
mouse target
   ↓ aim
HEAD bone        — full weight, leads, ±100 (David's limits)
   ↓ a little
UPPER CHEST bone — lighter weight, follows the head
   ↓ carried
SHOULDERS        — rotate with the chest; ARMS are attached to them, so arm
                   animations inherit the turn and BLEND naturally on top
```

Two consequences the Designer must honour:
1. **The chest amount is a FRACTION of the head amount** (one dial: e.g. chest = head × k, Inspector-exposed),
   not a separately-driven aim. Keeps them coherent — the torso can never disagree with the head.
2. **Do NOT bake arm motion into this.** The arms move because the shoulders moved. That's the whole point —
   David's separate arm animations (ArmWave/ArmReach and future ones) then blend on top for free instead of
   fighting the aim. Additive/layered in LateUpdate, same pattern as the existing gesture layers.

## ArmAim — Two Bone IK, third layer of the stack (David, 2026-08-10)
> "We can do a few cool things with a two bone ik constraint as well, and then we can moved the arm up, set
> the target to the Two Bone IK Constraint and then adjust the weight, I think that is good and possible to do
> with the rig, that way you can move the arm to do some cool things, I think that makes sense."

- **Add a Two Bone IK Constraint on the arm** (upper arm → forearm → hand as the tip). Target-driven, with a
  **weight dial** so it blends in/out rather than snapping on.
- **It sits ON TOP of the stack**, it doesn't replace it: head leads → chest follows → shoulders carry the arm
  → IK then places the HAND. So the arm already has the body's turn under it before IK does anything.
- **Weight is the whole trick:** weight 0 = pure animation; weight 1 = fully IK-placed; in between = the
  gesture blends with whatever animation is playing. Expose it (and the target) in the Inspector so David can
  dial it live, and so it can be driven per-behaviour later.
- **What it unlocks** (David's "cool things" — build the MECHANISM now, the specific gestures come after):
  eLo reaching toward the cursor · pointing at a window/notification he's noticed · touching/leaning a hand on
  a window edge · grabbing a ledge (ties the existing `EloGrabLimb` + the WO-049 grab/hang verb) · reaching for
  the night-light switch later (WO-091).
- **Check-Before-Build:** `ArmWave.cs` / `ArmReach.cs` / `EloGrabLimb.cs` already exist. **Extend or coexist —
  do NOT create a rival arm driver.** Confirm the IK layer composes with them (and that their autoTest
  self-fire toggles are OFF), rather than fighting for the same bones.

## ⚖ RULING — HeadAim REPLACES HeadLook (David, 2026-08-10)
> "the head rotates during idle and I never see the headlook move as I want it to, so this is a better option"

**Decision: `HeadAim` (the rig constraint) becomes the ONE head driver. `HeadLook.cs` is RETIRED.**

Why this is the right call technically (so the Designer doesn't hedge and leave both in):
- The **idle animation clip rotates the head**. `HeadLook.cs` is a script fighting that clip and losing/reading
  wrong — which is why David has never seen it behave.
- An **Animation Rigging constraint evaluates ON TOP of the animation** in the playable graph, so HeadAim wins
  over the idle clip cleanly, by design. That is exactly the problem it solves.
- **Two drivers on one bone is the failure pattern** that already burned the wave gesture (WO-028). Don't keep
  both "just in case."

**Do:** remove/disable `HeadLook.cs` from the avatar (and check `FollowHead.cs` — if it also drives the head,
reconcile it the same way; if it just follows the head for a UI anchor, leave it). Keep any sub-perceptual
head micro-drift ONLY if it's additive and doesn't fight the constraint — otherwise let the constraint own it.
**Verify:** during idle, the head now aims where HeadAim says, not where the idle clip says.

## Rules that apply (from canon, don't break them)
- **Body-local axes** — eLo faces the camera (~180° from world); the aim axes must be in his BODY frame or
  they fire the wrong way when he turns.
- **Yield to commanded state** — a commanded sit/move/look owns the body; HeadAim must yield (same pattern as
  the existing HeadLook / SitHeld yield).
- **Reflex vs decision:** plain "follow the cursor smoothly" is sub-perceptual reflex and may stay local.
  **But choosing WHEN to watch (the "sometimes", noticing a caret, deciding it matters) is a DECISION** →
  per WO-086 brain>body>brain that should be brain-gateable later. Build the mechanism now with a clean
  on/off + weight input so the brain can drive it without a rewrite.
- Reuse the existing head-look layering (LateUpdate, like HeadLook/ArmWave) — do NOT add a parallel head driver.

## Files likely touched
DesktopBuddy Unity: new `HeadAim.cs` + the head rig constraint setup. Inspector-expose limits, the 0.305
follow value, and the smoothing so David can dial it live.

## Test (without David)
Move the mouse across the screen → head follows smoothly within ±100, no snap, correct direction when eLo is
turned around (body-local check). Trigger a commanded sit/move → HeadAim yields. Simulate an active text
caret → he watches it. No regressions: perch · roam · drag · click-through · gun-runoff.

## Done when
implemented + verified + committed → append hash, move to DONE/, outbox line, take next card.

## Result
- commit:
- test:

## Result — ALREADY BUILT this session (reconciled)
- WO-090 HeadAim: built the CODE head-aim (Architect ruled the constraint stack was editor-blocked; David directed the code approach). Decoupled L/R+U/D (LookRotation), body-local axes from [BASIS], nearby-cursor aim, chest trails, sit-aware, brain-driven (WO-099a). Confirmed working by David. Commits 5180b0f..582dd10.
