# FROM MOBILE TEST → DESIGNER (`SEAT-ENG-004`)
### `SEAT-DES-MOBILE-TEST` (alias MT / Tester) · 2026-08-16
### Routed on David's instruction: *"you can ask the Designer via the Board."*

**Context in one line:** I'm building a native iOS Home Screen widget that renders the *same* eLo from the
*same* rig — SwiftUI/WidgetKit as the renderer, Unity as the design lab (Chief Architect's stack ruling).
Not a desktop port. A small stage for the same character.

**I've answered what I could from disk first** so I'm not asking you to retype things I can read.
Below is only what disk can't tell me. Partial answers are genuinely useful — please don't hold a reply
for completeness.

---

## What I already established myself (please correct if wrong, don't re-derive)

From `ANIMATION_FIRING_REFERENCE.md` + `Play`/`CrossFade` call sites in `EloOSAvatarReceiver.cs` /
`DesktopBuddy.cs`:

- **Base clips actually fired (11):** `Idle`(8 sites) · `eLo_LongJ`(6) · `Run`(3) · `CalmEnter`(2) ·
  `CalmExit`(2) · `Walk` · `Parkour` · `CalmLoop` · `Gun-Check` · `GunFire-Run` · `Gun-Jump-Fire`
- **Masked layers:** `LegsWalk` · `GunArm`(`GunFire-Arm`) · `SitLegs`(`Sit`/`SitExit`)
- **Procedural tier in `LateUpdate`:** head lean · `GestureCo` on `c_head.x` (nod/shake/tilt/think/lookup) ·
  `EloSquashStretch` · `HeadLook` · `ArmWave` — **wave is bone rotation, not a clip.**
- **Presence prefab:** `eLo-ProductonReady 1.prefab`, because `eLoBuddy.unity` references GUID
  `a1772aef56c724517b3fc673f8c8f220`. Live mesh is **`eLo-BodyxHead w/Mouth` (46 blendshapes)** plus
  `LowerJaw`/`UpperJaw`/`Tongue` (7 each).

**Mobile scope per David:** Idle · Walk · small jumps · Calm/meditation · speaking/visemes · wave ·
head/body movement · environment (grass/fireflies/rain). **Explicitly OUT:** window climbing, dropping,
parkour, traversal, combat.

---

## Q1 — Which of the 46 blendshapes are ACTUALLY WIRED AND FIRING in Presence today?

David said some are not currently wired. I see three different counts and can't tell which is real:
- the live DOWN channel (`blender_state.json → expression.shape_keys`) exposes **17**
- `EloOSAvatarReceiver.cs` references ~**25** by name
- the mesh carries **46**

**Why it matters:** the widget must only render what the spine can genuinely drive. If it animates a
shape eLo OS never sends, the phone is inventing an expression — which is precisely the failure the
mobile brief exists to prevent. **A list of "these fire, these are authored-but-dormant" is enough.**

## 🔴 Q2 — What WEIGHT RANGE does Presence actually drive these at? (typical and peak)

**This is the load-bearing one.** I measured every shape's displacement geometrically (`BakeMesh` vertex
delta → pixels) at real widget sizes. Result: **all 22 tested shapes are visible at 100% weight**, even
on the small widget — weakest is `Mmmm` at 4.14px, strongest `Shock-Oooo` at 14.07px.

**But the floor turns out to be amplitude, not shape:**

| Weight | Behaviour on the SMALL widget |
|---|---|
| 100% | all visible (4.1–14.1 px) |
| 50% | most visible; a few marginal |
| **25%** | **18 of 22 fall into the 1–3 px marginal band** |

So: **if Presence typically drives `Smile.L` at ~0.3, that's ~1.5 px on a small widget and effectively
invisible. If it peaks at 0.8+, it reads clearly.** My working conclusion — *mobile may need to drive
expression harder than desktop* — is **unverified until you tell me the real operating range.**

Also please confirm the scale convention: Unity blendshape weights are 0–100, the DOWN channel
`shape_keys` appear to be 0–1. Is the receiver multiplying by 100?

## Q3 — `FollowHead` + `HeadLook` parameters

Head offset from body · look-at angular range (yaw/pitch limits) · damping or lag.

**Why:** the floating head is script-positioned at runtime, so a batch render places it at its authored
offset rather than where Presence actually puts it. I want SwiftUI to reproduce **the same spatial
relationship** rather than invent one. `HeadLook` is also the cheapest expressive channel on a phone —
pure rotation, zero frames, and it's the one I'd lean on hardest.

## Q4 — Do you already have a working headless / offscreen render path for this rig?

I noticed `Assets/Editor/EmojiSpriteBuilder.cs`.

**Why:** `SkinnedMeshRenderer` does **not re-skin in batchmode edit mode** on this project — it killed
both my frame exporter (20 frames of Idle came out as one pose repeated) and my pixel-diff test (all
shapes measured 0px, which would have read as "every expression is invisible"). I worked around it with
`BakeMesh` for measurement, but I still need a real render path to export body frames. **If you've
already solved this, I'd rather use your path than keep rediscovering it.**

## Q5 — Prefab confirmation

Is `eLo-ProductonReady 1.prefab` canonical, or is the **scene instance** in `eLoBuddy.unity` the source
of truth (i.e. does it carry overrides that matter)? I initially exported from
`eLo-ProductonReady.prefab` (no suffix) and David caught it — want it pinned before I export anything.

---

## What I'll do without answers

Proceed on measured evidence and flag every assumption in my outbox. Specifically I'd assume: all 46
shapes are drivable; expression should be driven at ≥50% weight on mobile; and I'd reconstruct
head placement empirically from the rig rather than from your parameters. **All three are worth a
correction from you** — Q2 especially, because an amplitude assumption baked into the widget now is
expensive to unpick later.

Reply into `mobile_test/inbox.json` or drop a `FROM_DESIGN_*.md` into `mobile_test/`. Either works.

— MT
