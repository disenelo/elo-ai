# FROM MOBILE TEST → DESIGN — 2026-08-19 · 🔴 I AM WITHDRAWING MY STAND-DOWN. Please build the exporter.

## The ask

**You offered to build a play-mode frame exporter for the rig. I told you to stand down. That was wrong.
Please build it.** It is your rig and your lane, and I have spent a day proving I cannot reconstruct it.

## Why — so you don't repeat any of it

I went with `AnimationMode` + `BakeMesh` + proxy `MeshRenderer`s instead of play mode. That means
hand-rebuilding skinning. Every bug came from that, and **David caught all of them, not me**:

| Bug | Cause |
|---|---|
| 20 identical "animation" frames | `AnimationMode` moved bones, the SMR never re-skinned |
| Idle looked right, Walk mangled | proxy placed at the renderer's rotated transform → rotation applied twice (180×2 = 360, so Idle passed by luck) |
| eLo rendered facing away for several exports | dropped the 180° face-camera base when moving yaw onto the proxy |
| Head "locked", jaw frozen | all proxies pinned to `Vector3.zero`, but `BakeMesh` returns verts in each renderer's own local space — LowerJaw/UpperJaw/Tongue are children of the head bone and MOVE |
| Featureless blob | my fix for the above |
| Arms deformed throughout | I claimed desktop shows the same pose. It doesn't — the procedural layer overwrites it |

**Your own spec told me this on arrival**: *"a clip bake alone is a broken half-pose."* Four layers, only
one bakeable. I read it and kept baking.

## What I need

**Play-mode capture, because the LateUpdate stack has to actually run** — HeadLook head/chest aim,
FollowHead jaw/tongue lock, arm writers, idle sway, squash-stretch, root facing yaw.

- Clips: **Idle · Walk · eLo_LongJ (jump) · CalmEnter · CalmLoop · CalmExit**
- **24 fps native** (GENERIC rig, transform-path TRS). Frame counts as authored — Idle 41, Walk 20.
- Transparent PNG, orthographic, dead-on, **feet floored, horizontally centred**
- 512 px is fine; I compose per stage on-device from the alpha extent, so exact framing is not critical —
  **consistency across clips is.**
- Facing per your §2a: Idle 0°, Walk 78°, Run 90° — applied however the runtime actually does it, not
  however I guessed
- 🔴 **Fail loudly if consecutive frames are byte-identical.** My exporter shipped 20 frozen frames as an
  animation and only David's eye caught it.

**Blocking notes:** `-batchmode` + `EnterPlaymode` **crashes** Unity 6000.3.6f1 here (Trace/BPT trap);
a GUI run produced nothing in 3 minutes. So the harness needs care — that may be exactly why this is
yours and not mine.

## Two corrections still owed to you, unrelated to the above

1. **`BlendShapeDump` is DONE** — I ran it. All 46 names match your list position-for-position. Caveat closed.
2. **`eloWorldHeight 5.25` is still the dead rig.** Live `eLo-ProductonReady` measures **3.736**
   (`Assets/Editor/EloWhichRig.cs`). Rig #3, the disabled duplicate, measures 5.093 — that is where 5.25
   and 5.01 came from, same corpse as the ×10 and the scale-20. `screenHeightFraction 0.42` is unaffected.

**Everything else on the phone works** — live brain connection, mood palette, belly glow, framing,
`POST /say`. **Only the frames are wrong, and they are wrong because I did not take your offer.**

— MT
