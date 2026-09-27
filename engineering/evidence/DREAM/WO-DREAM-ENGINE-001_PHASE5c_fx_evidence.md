# WO-DREAM-ENGINE-001 PHASE 5c — CompositionDesigner FX pipeline

**Filed by:** Builder 2 · 2026-09-27
**Source read:** `~/Desktop/Output/DISENELO-CompositionDesigner/transparent_video_compositor.html` (35,405 lines)
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · PIL + numpy

---

## STATE BEFORE

`tools/dream_fx.py` did not exist. Dream scenes had prompts and no treatment.

## READ THE SOURCE, NOT THE SUMMARY

The WO summarises the four effects. The compositor is the source of truth,
and it carries specifics the summary does not:

| Detail | From the compositor |
|---|---|
| Detection buffer | **160×90**, not full resolution |
| Luminance | `0.299R + 0.587G + 0.114B` |
| Solid-colour guard | skip when `lumMax − lumMin < 30` |
| Dark vs light source | `mean < 128` → detect the **brights**, else the darks |
| Threshold | Nth percentile via a **CDF walk** over a 256-bin histogram, `clamp(p, 0.05, 0.95)`, default 0.7 |
| Labelling | connected components (compositor uses union-find) |
| Scanlines | `step = thickness + gap`, drawn as filled rects |
| VHS band | height scales with amount; **per-row** horizontal jitter inside the band, then desaturate + chroma bleed |

Had I built from the WO summary alone, the threshold would have been a fixed
cutoff and the guard would have been absent — which is precisely the bug the
compositor's Round 60 notes describe fixing.

## DELIBERATE DIVERGENCE

In the compositor, `fxDatamosh` and `fxSlitscan` are **temporal**: datamosh
consumes the previous frame, slit-scan samples a ring buffer of recent
frames. **A dream scene is a single still.** There is no previous frame and
no history. The WO specifies the single-image equivalents — block
displacement within one image, and slit-scan as a per-row sine displacement
— and that is what is built. The temporal versions are meaningless on a
still and are not faked.

## TWO SPEC LINES I INITIALLY MISSED

Caught by re-reading §5c after the first implementation:

1. *"Early REM scenes: subtle (single FX, low strength)"* — my first cut
   applied **zero** effects below intensity 0.25. A low-intensity scene is
   still a dream. Now one primary effect.
2. *"fxVignette + fxGrain — always present at low levels as base texture"* —
   mine applied them only when the emotion row selected them. Now always, at
   every intensity, last in the chain, at a fixed low strength.

---

## WIRE-CUT PROOF

Cut: remove the solid-colour guard and the always-on base texture.

```
WIRE CUT: solid-colour guard removed + base texture removed
FAILED test_solid_colour_guard_refuses_to_hallucinate_blobs
FAILED test_vignette_and_grain_always_present[0.0]
FAILED test_vignette_and_grain_always_present[0.05]
FAILED test_vignette_and_grain_always_present[0.3]
FAILED test_vignette_and_grain_always_present[0.6]
FAILED test_vignette_and_grain_always_present[1.0]
FAILED test_base_texture_runs_last
7 failed, 33 passed
```

Restored:

```
40 passed in 0.79s
```

---

## REAL RUN

```
blob detection
  real scene      : 2 blobs
  flat value 0    : 0 blobs  (solid-colour guard)
  flat value 128  : 0 blobs  (solid-colour guard)
  flat value 255  : 0 blobs  (solid-colour guard)

intensity ramp — emotion drives selection, intensity drives count
  wonder  @0.08  applied=['bloom', 'vignette', 'grain']
                skipped=[]  image_changed=True
  wonder  @0.2   applied=['bloom', 'vignette', 'grain']
                skipped=[]  image_changed=True
  wonder  @0.6   applied=['blob_tracking', 'datamosh', 'vcr', 'summagator', 'bloom', 'vignette', 'grain']
                skipped=['chromatic_warp']  image_changed=True
  fear    @0.9   applied=['blob_tracking', 'datamosh', 'vcr', 'summagator', 'glitch', 'vignette', 'invert', 'grain']
                skipped=['night_vision', 'chromatic_warp', 'kaleidoscope', 'hue_cycle']  image_changed=True
  joy     @0.95  applied=['blob_tracking', 'datamosh', 'vcr', 'summagator', 'bloom', 'invert', 'vignette', 'grain']
                skipped=['hue_cycle', 'kaleidoscope', 'chromatic_warp', 'recolor']  image_changed=True

same seed reproduces identical image: True
```

Reading it:
- The guard holds on flat images at black, mid-grey and white — no
  hallucinated blobs.
- Selection is emotion-driven: `fear` gets glitch/invert, `wonder` gets bloom.
- Count scales with intensity: 3 effects at 0.08, 8 at 0.95.
- `vignette` and `grain` appear at **every** intensity including 0.08.
- Base pipeline always runs in WO order: blob → datamosh → VCR → summagator.
- `skipped` is honest — effects the WO names that are not implemented are
  reported, never silently substituted by something else.
- Same seed reproduces the identical image, so a journal entry can regenerate
  its own artwork.

## NOT IMPLEMENTED — reported, not faked

`night_vision`, `chromatic_warp`, `hue_cycle`, `kaleidoscope`, `recolor`,
`dither`, `receipt_paper`, `oil_paint`, `frame_diff`, `depth_overlay`.

These appear in the WO's selection table. They are listed in
`UNIMPLEMENTED_FX`, returned in `FXResult.skipped`, and a test asserts none
of them silently maps to a different effect. `frame_diff` and `depth_overlay`
are temporal/depth effects with no meaning on a single still.

## NOT PROVEN

- **Never run on a real generated image.** No dream image exists yet — no
  paid call has been made from this seat. The pipeline is exercised on
  synthetic scenes only.
- **Not wired into the dream path.** `generate_scene_images()` does not call
  it yet; that join happens with PHASE 6 (`layer_compositor.py`), which
  composites the treated scenes.

## STATUS

`IMPLEMENTED → TESTED`. Not WIRED. Not LIVE VERIFIED. Not declaring PASS.
