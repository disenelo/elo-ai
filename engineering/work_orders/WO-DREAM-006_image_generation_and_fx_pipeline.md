# WO-DREAM-006 — Dream Faculty: Image Generation and FX Pipeline

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 5 — Image Generation + FX Pipeline

**File:** `tools/image_gen_agent.py` (extend existing) + `tools/dream_fx.py` (new)

### 5a. Fix image_gen_agent (DREAM-1 — prerequisite)

- Confirm `openai` package installed
- Surface actual exception (not swallowed)
- Log `[dream] image generation failed: <reason>` — never silent None

### 5b. Generate one image per dream scene

- One DALL-E call per scene, using the structured prompt for that scene
- Each scene uses the scene's intensity level
- Images saved as `dream_<dream_id>_scene_<N>.png`

### 5c. Apply CompositionDesigner FX per scene (`tools/dream_fx.py`)

Source: `Output/DISENELO-CompositionDesigner/` — all four effects are live in the compositor. Implement as Python equivalents applied in order: blob tracking → datamosh → VCR → summagator.

- **Blob tracking** (`fxBlobTracking`) — adaptive luminance blob detection. Dark source: detect brights. Light source: detect darks (inverted). 70th-percentile adaptive threshold. Solid-colour guard (skip if lumMax-lumMin < 30). Draw detected regions as semi-transparent shapes in teal/violet. `blobColor`, `blobBoxes`, `blobDots` sub-options.
- **Datamosh** (`fxDatamosh`) — pixel-block displacement. 30–40% of 16×16 blocks copied from nearby offset (8–24px). Simulates P-frame compression corruption. `datamoshAmount` 0.3–0.5.
- **VCR** (`fxVhsTrackError` + `fxScanlines` + `fxCrt`) — three sub-layers: scanlines (dark horizontal lines every 3–4px, alpha 0.08–0.12), tracking error (3–6 horizontal bands offset 4–12px), chromatic aberration (R +2px / B -2px horizontal), gaussian grain (σ=4–8).
- **Summagator** (`fxSlitscan` + `fxTrails`) — 3 copies at scales 1.0/0.95/0.90, opacities 1.0/0.4/0.2. Slit-scan vertical displacement: `sin(row/H×π) × 8–16px` per row. Screen or soft-light composite.

### Additional FX (apply selectively by emotion/intensity)

- `fxGlitch` — horizontal slice displacement (anxiety/fear dominant)
- `fxChromaticWarp` — radial chromatic aberration (surreal/wonder)
- `fxBloom` + `fxBloomThresh` — glow bloom (joy/wonder, achievement)
- `fxEdgeDetect` — edge outlines (analytical, curiosity dominant)
- `fxHueCycle` — hue rotation over time (late REM, high intensity)
- `fxTrails` — motion trail accumulation (memory layers, nostalgia)
- `fxFrameDiff` — frame difference highlight (transformation moments)
- `fxPosterize` — colour quantisation (grief/sadness, simplified palette)
- `fxDither1bit` — 1-bit dither (fragmented memory, early cycles)
- `fxKaleidoscope` — mirrored symmetry (strong REM, apex)
- `fxOilPaint` — painterly smoothing (nostalgia, mid-cycle)
- `fxDepthOverlay` — depth-map overlay (embodiment dreams)
- `fxNightVision` — green phosphor (fear/anxiety dominant)
- `fxReceiptPaper` — thermal texture (memory distance, old material)
- `fxVignette` + `fxGrain` — always present at low levels as base texture
- `fxRecolor` — palette replacement by emotion (sadness → washed teal, joy → saturated)
- `fxInvert` — full inversion (displacement peak, maximum surreal)

### FX selection table — driven by emotion vector, not random

| Emotion dominant | Primary FX | Secondary FX |
|---|---|---|
| Anxiety / Fear | Glitch, VCR tracking error, Night vision | Chromatic warp, vignette |
| Joy / Wonder | Bloom, Hue cycle, Kaleidoscope | Chromatic warp, recolor |
| Sadness / Grief | Posterize, Dither, Trails | Receipt paper, recolor (teal) |
| Achievement | Bloom (high), Edge detect | Upward slit-scan direction |
| Nostalgia | Oil paint, Trails, Receipt paper | Faded recolor |
| Curiosity | Edge detect, Frame diff | Depth overlay |
| Maximum surreal (intensity > 0.85) | Invert + Kaleidoscope + Hue cycle | All above combined |

FX intensity scales with `dream_intensity`. Early REM scenes: subtle (single FX, low strength). Late REM scenes: heavy distortion (multiple FX, full strength).

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — image gen BLOCKED on live API cost
**Commits:** `f877ff3` (dream_fx.py) + `2266ac0` (image_gen_agent extension)
**Files:** `tools/dream_fx.py`, `tools/image_gen_agent.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-006-007_fx_and_compositor_evidence.md`

### FX pipeline — built (`tools/dream_fx.py`)

| Function | Effect |
|---|---|
| `blob_tracking(img, intensity)` | 70th-percentile adaptive luminance; teal <0.5, violet ≥0.5 |
| `datamosh(img, intensity, amount)` | 16×16 pixel-block displacement |
| `vcr(img, intensity)` | Chromatic aberration, scanlines, tracking bands, Gaussian grain |
| `summagator(img, intensity)` | 3-copy slit-scan, screen/soft_light blend |
| `apply_fx(img, intensity, emotion_vector)` | Canonical pipeline: blob→datamosh→vcr→summagator |

Selective FX: anxiety+fear>0.5 → glitch; joy+wonder>0.6 → bloom; curiosity>0.5 → edge detect.

### Image generation — `generate_dream_scene()` built and wired

Saves as `dream_<dream_id>_scene_<N:02d>.png`. Calls `generate()` with `preview=False, write_hud=False`.

**BLOCKED:** DALL-E 3 requires live API call with real cost. `openai` now installed (`3.19.2`). Image gen path confirmed in code — gated on cost cap in production. Backend confirmed: `python path confirmed` (from evidence). 

### Known gap

10 FX the WO names are unimplemented — reported in `skipped`, never substituted for another effect.

### Tests

`test_dream_fx_and_compositor` — 17/17 passed

Builder 1 · 2026-09-27 / 28
