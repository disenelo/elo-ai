# eLo BlendShapes — Lip-Sync + Jaw Handover (for the eLo OS agent)

> Authoritative list pulled directly from the rig in Unity (2026-06-28). eLo has **NO eyes** —
> all expression is mouth / jaw / cheeks / brow. Weights are sent **0.0–1.0**; Unity multiplies by
> its own scale (`blendshapeScale = 50`, tongue `= 100`). Keep peaks **subtle** (~0.3–0.6).

## How the channel works (important)
- **Viseme + expression weights** are read from `blender_state.json → expression.shape_keys` ({ "ShapeName": 0..1 }). This is the channel that moves the mouth.
- **`lipsync_state.json → active: true`** must be set while speaking. It gates the speech bubble, suppresses idle, **and enables the auto jaw**.
- **JawOpening is auto-derived by Unity — do NOT send it.** While `active`, Unity opens `JawOpening` (lower jaw) from whichever open-mouth viseme is strongest, so the jaw drops in step with the words. You only send the visemes; the jaw follows automatically. (Unity: `jawOpenScale = 0.7`.)

## Jaw auto-open mapping (what each viseme contributes to the jaw)
Unity opens the jaw = `max(visemeWeight × factor) × 0.7 × scale`:

| Viseme | Jaw factor | | Viseme | Jaw factor |
|---|---|---|---|---|
| `Ah` | 1.0 | | `Eh` | 0.6 |
| `Shock-Oooo` | 1.0 | | `Ee` | 0.25 |
| `Ai` | 0.9 | | `MouthOpen.Wide` | 1.0 |
| `Huh` | 0.8 | | `MouthOpen.Slightly` | 0.5 |
| `Oooh` | 0.7 | | `Mouth-Open-Shock` | 1.0 |
| `Mbp` `Mmmm` `Fv` `FvS` `S` | 0 (closed) | | | |

So to make the jaw motion read well: drive the **open vowels** (`Ah/Ai/Oooh/Shock-Oooo/Huh/Eh`) for open sounds and the **closed consonants** (`Mbp/Mmmm/Fv/FvS/S`) for closed sounds — the jaw will track naturally.

## Viseme set (phonemes) — drive these for lip-sync
`Ah` · `Eh` · `Ee` · `Ai` · `Oooh` · `Shock-Oooo` · `Huh` · `Mbp` · `Mmmm` · `Fv` · `FvS` · `S`

Suggested subtle peaks: open vowels ~0.45–0.6, `Ee` ~0.35, consonants `Mbp/Mmmm` ~0.3 (lips together, little jaw), `Fv/FvS/S` ~0.25.

## Full blendshape inventory (from the rig)

**Mouth / jaw (on eLo Mesh + UpperJaw + LowerJaw):**
`MouthOpen.Slightly` · `MouthOpen.Wide` · `JawOpening` *(Unity-owned)* · `MouthWidth.L` · `MouthWidth.R` · `Smile.L` · `Smile.R`

**Mouth / lips (eLo Mesh only):**
`Upper-Lip.R` · `Lower-Lip.R` · `Lower-Jaw-U/D` · `Mouth-Open-Shock` · `Smile/Sad-Open-Mouth` · `Curl-Lips` · `Stick-Out-Lip`

**Cheeks:**
`Smile-Cheeks` · `Puff-Cheeks` · `Inflate-Cheeks-L`

**Emotion (eLo Mesh):**
`Confident` · `Worried` · `Disgusted` · `Angry` · `Angry/Expressive` · `Satisfied/LittleJoy` · `Sad-Lower-Lip-Dimples` · `Mouth-OpenDisgust` · `Puff-EyebrowsRaise` *(= concern/brow)*

**Visemes (eLo Mesh):**
`Ah` · `Eh` · `Ee` · `Ai` · `Oooh` · `Shock-Oooo` · `Huh` · `Mbp` · `Mmmm` · `Fv` · `FvS` · `S`

**Tongue (Tongue mesh, driven at higher scale):**
`Tongue Out` · `Tongue Move` · `Poke-Out` · `F/B` · `Twist` · `Swirl` · `Key 6`

**Ignore:** `Template`, `Key 6`, `Key 7` (rig scaffolding, not expressive).

## TL;DR for the OS agent
1. While speaking: set `lipsync_state.active = true`.
2. Stream viseme weights (0..1, subtle) into `blender_state.json → expression.shape_keys`.
3. **Don't** send `JawOpening` — Unity opens the jaw for you, matched to the open visemes.
4. For closed sounds use `Mbp/Mmmm/Fv/FvS/S` (jaw stays shut); for open sounds use `Ah/Ai/Oooh/Eh/Huh` (jaw drops).
