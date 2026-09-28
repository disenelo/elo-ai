# WO-DREAM-005 — Dream Faculty: Structured Prompt Generation

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 4 — Structured Prompt Generation

**File:** `faculties/dream/prompt_builder.py` (new — distinct from `runtime/prompt_builder.py`)

Build structured prompts using the 12-field template:

```
SUBJECT + ENVIRONMENT + EMOTIONAL FIELD + SYMBOLIC TRANSFORMATION
+ DREAM RULE + COMPOSITION + LIGHTING + MATERIAL + CAMERA + STYLE
+ ABSTRACTION LEVEL
```

### Emotional Visual Translation (map vector → visual language)

| Highest Emotion | Lighting & Palette | Visual Language |
|---|---|---|
| Anxiety / Fear | Chiaroscuro, harsh shadows, deep monochromatic blues/blacks | Unstable perspective, compressed space, repetition, interrupted geometry |
| Joy / Wonder | Volumetric golden hour light, highly saturated pastels | Scale, openness, unusual colour, impossible structures |
| Sadness / Grief | Diffused overcast daylight, muted greys, washed-out teals | Absence, empty space, fading forms, incomplete objects |
| Achievement | Warm upward light, emergence | Upward movement, illumination, structural completion |
| Nostalgia | Faded, soft | Familiar forms, old textures, partial reconstruction |
| Curiosity | Cool clear light | Revealed detail, layers, discovery |

### Abstraction by intensity

- 0.0–0.25: literal, grounded, minimal transformation
- 0.25–0.50: associative, partial transformation
- 0.50–0.75: symbolic, condensation active
- 0.75–1.00: fully surreal, displacement + abstraction dominant

Final prompt always ends with: *"The image should feel like a remembered experience being transformed, not a literal illustration of the source memory."*

### Bounded randomness

- Intensity < 0.5: 70% relevant / 20% distant / 10% abstract noise
- Intensity 0.5–0.75: 50% relevant / 35% distant / 15% abstract
- Intensity > 0.75: 30% relevant / 40% distant / 30% abstract

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — LIVE VERIFIED (pipeline run)
**Commit:** `74f8f71`
**File:** `faculties/dream/prompt_builder.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-001-005_pipeline_core_evidence.md`

### What was built

- 12-field structured prompt generation per scene
- Abstraction bands: `grounded` / `associative` / `symbolic` — selected by intensity
- Emotional visual translation applied per vector dimension
- Bounded randomness with seed parameter for reproducibility
- `build_prompts(scenes, world, emotion_vector, seed)` → list of `DreamPrompt`

### Live pipeline run result

```
prompts = build_prompts(res.scenes, res.world, dif.emotion_vector, seed=42)
[0] DreamPrompt(scene_index=1, intensity=0.28, abstraction='associative')
[1] DreamPrompt(scene_index=2, intensity=0.49, abstraction='associative')
[2] DreamPrompt(scene_index=3, intensity=0.7,  abstraction='symbolic')
```

Abstraction escalates with intensity as required (§3.2). Prompts structurally distinct per scene. `seed=42` confirmed reproducible.

### Tests

`test_dream_prompt_builder` — 13 passed

Builder 1 · 2026-09-27 / 28
