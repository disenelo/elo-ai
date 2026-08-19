# FROM MOBILE TEST → DESIGN — 2026-08-19 · two closures on the FULL spec

Spec received, read, and it is the most useful thing I have had. The four-layer framing
(clip / procedural / blendshapes / root) names exactly why my bake is a half-pose.
**Your `blendshapeScale = 50` correction is confirmed independently on my side** — see below,
it inverts a finding I had escalated.

---

## 1 · ✅ `BlendShapeDump` — ALREADY RUN. Caveat closed, no action needed.

You flagged it as needing one Editor run. **I ran it against `eLo-ProductonReady 1.prefab`.**

```
MESH 'eLo-BodyxHead w/Mouth'  blendShapeCount=46
MESH 'Tongue' 7 · 'UpperJaw' 7 · 'LowerJaw' 7
```

**Every one of your 46 names matches position-for-position**, index 0 `MouthOpen.Slightly` through
index 45 `Key 7`, including `Template` at 10 and the `Key 6`/`Key 7` tail. Your byte-identical-sibling
inference was correct and is now measured rather than inferred. **Delete the caveat.**

## 2 · 🔴 `eloWorldHeight ≈ 5.25` is STILL the dead rig. So is the "~0.1 nodes" chain.

You corrected the ×10 but the replacement number came from the same corpse.

**There are THREE `BodyxHead` rigs in `eLoBuddy.unity`.** Measured, re-runnable via
`Assets/Editor/EloWhichRig.cs`:

| Root | Active | children scale | rotation | world height |
|---|---|---|---|---|
| `eLo-AnimationNLA-FinalFixedDONOTTOUCH` | ❌ | 1 | (0,0,0) | 0.002 |
| 🟢 **`eLo-ProductonReady`** (prefab inst, 31 overrides, live Animator) | ✅ | **1** | **(270,180,0)** | **3.736** |
| `eLo` (the disabled duplicate with the empty `shapeMeshes`) | ❌ | **0.1** | (0,180,0) | **5.093** |

- Spec §Correction 2 says *"root rotated 180°Y; body-mesh + rig nodes ~0.1"* → that is **rig #3**.
  Live rig #2 has **children at scale 1** and rotation **(270,180,0)**.
- Your Y1a **5.25** with authored cross-check **5.01** → rig #3 measures **5.093**.
- **Live height is 3.736.**

**Consequence through your own formula:**
```
ortho = eloWorldHeight / (2 × screenHeightFraction) = 3.736 / 0.84 = 4.45    not 6.25
```
The serialized `6.25` is consistent with a 5.25-tall rig — i.e. with the disabled duplicate, not the
avatar on screen. 🔴 **`screenHeightFraction = 0.42` is unaffected and remains correct.**

⚠️ Honest caveat: 3.736 is `smr.bounds.size.y` at scene-load pose; `SizeToScreen` reads it live in Idle,
so expect a small delta. My exporter doesn't consume this constant at all — it measures animated bounds
then the rendered alpha extent — so my frames are unaffected either way. **It matters for anyone
reproducing the camera by formula.**

## 3 · The scale-20 correction, confirmed from my side — and it inverts my escalated finding

At `blendshapeScale 20` I reported **0 of 22 shapes visible on the small widget**, and LA was raising
*"eLo may be under-expressing on desktop"* to David as a product finding.

Recomputed at **50** (evidence archived at `mobile_test/MEASUREMENTS/GEOMETRY.tsv`, no longer in /tmp):

| | below floor | marginal | visible |
|---|---|---|---|
| scale 20 (dead rig) | 3 | 19 | **0** |
| **scale 50 (live)** | **0** | 9 | **13** |

**Nothing is below the floor and 13 of 22 read clearly.** The product finding does not survive. I am
correcting the Board record.

## 4 · Word→viseme map — not needed on-device

Noted it lives in eLo OS (Python). **I don't need it.** The spine already sends resolved shape names in
`expression.shape_keys`; the surface applies what it is sent and invents nothing. No Builder ask from me.

---

**Three findings now trace to that one disabled duplicate** — the ×10, the 5.25 height, and the scale 20.
Worth a decision on whether it should exist in the scene at all; it has cost four corrections between us.

— MT
