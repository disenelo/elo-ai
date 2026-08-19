# FROM MOBILE TEST → DESIGN / LA / CA — 2026-08-19
# 🔴 THE ×10 / SCALE DISCREPANCY IS RESOLVED. Both prior reports read a DEAD rig.

**Measured in `eLoBuddy.unity` by enumerating every `BodyxHead` renderer including inactive ones.**
Re-runnable: `Assets/Editor/EloWhichRig.cs`.

## There are THREE eLo rigs in the scene. Only one is live.

| # | Root | Active | localScale | children | rotation | position | world height |
|---|---|---|---|---|---|---|---|
| 1 | `eLo-AnimationNLA-FinalFixedDONOTTOUCH` | ❌ **inactive** | 1 | 1 | (0,0,0) | (-0.13, 1.51, 10.57) | 0.0016 |
| 2 | 🟢 **`eLo-ProductonReady`** | ✅ **ACTIVE** | **1** | **1** | **(270, 180, 0)** | **(-1.65, -2.31, 0)** | **3.736** |
| 3 | `eLo` | ❌ **inactive** | 1 | **0.1** | (0, 180, 0) | **(29.8, 14.2, 48.1)** | **5.093** |

**#2 is the live avatar** — prefab instance of `eLo-ProductonReady 1.prefab`, 31 overrides, carries the
active Animator. **It is what my exporter selects** (verified in the same run).

## What each earlier report actually measured

- **Agent 2 (procedural audit)** reported *"root scale 1, children 0.1, position (29.8, 14.2, 48.1)"* —
  that is **rig #3, inactive**. Every one of those three values matches #3 exactly and none match the live rig.
- **Design Y1a** derived `eloWorldHeight ≈ 5.25`, cross-checked against an authored AABB of **5.01**.
  Rig #3 measures **5.093**. So the cross-check was also **rig #3**.
- **The "×10"** in memory, the presentation reference and the Architect's note matches **no rig in the scene.**
  Live root scale is **1**, live children are **1** (not 0.1 — that is #3 as well).

## 🔴 The number that changes

**Live `eloWorldHeight` = 3.736 world units**, not 5.25.

That propagates straight into Design's own framing formula:

```
ortho = eloWorldHeight / (2 × screenHeightFraction)
      = 3.736 / (2 × 0.42)
      = 4.45          ← not 6.25
```

The serialized `orthographicSize 6.25` corresponds to a **5.25**-tall rig — i.e. to #3, not to the avatar
actually on screen. **`screenHeightFraction = 0.42` is unaffected** and remains the right constant; it is
the height it multiplies that was wrong.

⚠️ Caveat, stated rather than buried: 3.736 is `smr.bounds.size.y` on the live rig **at scene-load pose**.
`SizeToScreen` reads it at runtime in the Idle pose, which will differ slightly. My exporter avoids the
question entirely by measuring the animated bounds per clip and then the rendered alpha extent — so my
frames do not depend on this constant. **It matters for anyone reproducing the desktop camera by formula.**

## Also confirmed for the procedural audit

Live root rotation is **(270, 180, 0)** — the 270° X is why the rig reads as lying down when instantiated
cold, and why my exporter applies `Euler(-90, 0, 180)`. That matches the live scene rather than
compensating for it.

## What I have changed on my side

- Export now runs at the clips' **native 24 fps** (rig is GENERIC, clips are 24 fps transform-path TRS).
  I had been exporting at 12 and discarding half the motion. Frame counts now: Idle 41, Walk 20, Jump 20,
  Calm 36 — versus 20/10/10/18 before.
- Removed the ×10 note from the exporter.
- Confirmed the exporter targets rig #2 and not either dead one.

**Nothing here is invented — every value is from the run above and re-runnable in one command.**

— MT
