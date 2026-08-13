# WO-090 — HeadAim · ChestAim · ArmAim: the natural rotation stack (eLo looks at what's happening)

**Owner:** Designer (UI/Avatar, Unity). **Priority:** P2. **Status:** OPEN — spec'd 2026-08-10 from David's
live direction. **Not gated.** **Source (VERBATIM):**
`docs/architecture/_intake/SOURCE_2026-08-10_headaim_mouse_follow.md` — David flagged this was raised before
and **lost in the loop**; it does not get lost again.

## Goal
eLo's head follows what's happening on screen — the mouse, an actively-moving text caret, and later any
active object — and his body follows naturally with it. Foundation for the head interacting with screen events.

## Why a rig constraint (the audit that decided it)
`HeadLook.cs` writes `headBone.localRotation * Quaternion.Euler(...)` — **additive on top of the animated
pose**, so it never overrides the idle clip. Effective look ≈ **13°** (30° max × 0.44 strength × 30% duty)
against an always-on random wander of **±8 yaw / ±12 pitch** → the deliberate look reads as drift.
**An Animation Rigging constraint evaluates in the animation graph and produces an ABSOLUTE aim, so it beats
the idle clip.** Package `com.unity.animation.rigging` **1.4.1 is already installed**; no RigBuilder exists
yet, so this is the project's first rig setup (touches the avatar prefab).

## Scope
### 1. Split HeadLook (do NOT delete it — 474 lines, only ~¼ is rotation)
Move everything EXCEPT rotation into **`HeadExpression.cs`**, unchanged in behaviour: cursor smile/worried,
micro-expressions (Ekman flashes, bored holds), mood baseline, **WO-062 brain `FlashMicro`**, agreement `Nod()`,
drag/peek/belly/observe/sit tilts. **Retire only the rotation half.**

### 2. HeadAim — Multi Aim Constraint
- **Constrained object = the HEAD BONE** (`c_head.x`), bone-driven like `ArmWave` (WO-028). Bone name
  Inspector-exposed.
- Target = a **mouse target object** following the cursor. **Rotation limits ±100** (David). Target follows
  the source object at **~0.305** (David's value — Designer confirm what it maps to before assuming).
- **Smooth** — damped, no snap.
- Uses: (a) eLo **sometimes** follows the cursor (noticing, not turret-tracking); (b) watches an **actively-
  moving text caret**; (c) later, any active object.
- **Must consume the existing brain cue** — `receiver.HeadCueActive` / `HeadYawCue` / `HeadPitchCue` already
  let eLo OS drive the head in degrees. Reuse it; don't rebuild One-Brain gating.
- **Re-home the additive beats ON TOP of the constraint result:** `PeekPitch` (WO-049 peek-before-jump),
  drag tilt, `ObservePitch/Roll`, `SitTilt`, `Nod()`, belly-glow look-down, `Calm` rest. These must survive.

### 3. ChestAim — second Multi Aim Constraint
Upper chest bone + shoulders, **lighter weight**, rotating WITH the head at a **fraction of the head amount**
(`chest = head × k`, one Inspector dial) — so the torso can never disagree with the head. Tighter limits than
the head: the head reaches, the chest leans.

### 4. ArmAim — Two Bone IK Constraint
Upper arm → forearm → hand, target-driven, **weight dial** (0 = pure animation, 1 = fully IK, between =
blend). Sits ON TOP of the stack. **Check-Before-Build:** `ArmWave.cs` / `ArmReach.cs` / `EloGrabLimb.cs`
already exist — extend or coexist, **never a rival arm driver**; confirm their autoTest self-fire toggles are OFF.

## The governing model — a natural stack (David)
> "if you rotate the head you rotate the torso as well a little, and as the arms are attached to the shoulders
> if I add different animations it will blend well"
```
mouse/active target → HEAD (full, leads, ±100) → UPPER CHEST (fraction, follows)
                    → SHOULDERS (carry the arms — arm animations inherit the turn and blend on top)
                    → ARM Two Bone IK places the hand
```
**Do NOT bake arm motion into the aim** — the arms move because the shoulders moved. That's what lets David's
separate animations blend for free instead of fighting the constraint.

## Rules
Body-local axes (eLo faces the camera ~180°) · yield to a commanded state · layer in LateUpdate like the
existing gesture layers · one driver per bone · no regressions (perch · roam · drag · click-through · gun-runoff).

## Test (without David)
Idle running → head aims where HeadAim says, **not** where the idle clip says (the acceptance David cares
about) · cursor look clearly visible, not masked by wander · brain cue still wins · peek/drag/observe/sit/nod
still fire · chest follows at the set fraction · arm IK blends by weight without fighting ArmWave/ArmReach.

## Done when
implemented + verified + committed. Suggested split: **05** head+chest stack, **05b** arm IK, so each lands
and is tested separately rather than one big change to the avatar prefab.
