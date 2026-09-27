# WO-DREAM-ENGINE-001 PHASE 6 — Visual Layering Engine

**Filed by:** Builder 2 · 2026-09-27
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · PIL + numpy

---

## STATE BEFORE

`faculties/dream/layer_compositor.py` did not exist. PHASE 5c produced
treated scenes with nothing to composite them into.

## WHAT CHANGED

| WO §6 requirement | Built |
|---|---|
| Base / Scene 01 / 0.9 / Normal | `ROLE_BASE`, `OPACITY_BASE = 0.90`, `BLEND_NORMAL` |
| Memory / Scene 02–03 / 0.4–0.6 / Multiply or Overlay | `ROLE_MEMORY`, band `(0.40, 0.60)` |
| REM apex / Scene 04+ / 0.2–0.4 / Screen, Difference, Color Dodge | `ROLE_APEX`, band `(0.20, 0.40)` |
| Opacity driven by emotional weight | `opacity_for(role, weight)` lerps inside the band |
| Blend by emotion vector | `EMOTION_BLEND`, two per row; apex takes the more extreme |
| SPG motif (≥3 dreams) into the apex | `recurring_symbol` + `motif_image`, overlaid at 0.22 |
| `dream_<id>_final.png` + metadata sidecar | written, with per-layer provenance |
| Seven named artwork layers | `ARTWORK_LAYERS` |

**Apex takes the more extreme blend of its emotion's pair** — a dream opens
or disrupts harder at its peak than in its middle. joy/wonder go
screen → color_dodge; anxiety/fear go multiply → difference.

The emotion→row mapping is the same one `prompt_builder` and `dream_fx` use,
so a scene's lighting, its FX and its blend describe one dream rather than
three.

## THE MOTIF IS NEVER FABRICATED

`symbol_history` reports a recurring symbol as a NAME. The WO asks for it as
a semi-transparent overlay, which needs an image. When the lexicon names a
motif and no image of it exists, the metadata records:

```json
{"symbol": "a machine breathing", "overlaid": false,
 "reason": "no motif image available for this symbol"}
```

Observed but not drawable is recorded as pending. It is not invented, and it
is not silently dropped either. Pinned by
`test_motif_is_never_fabricated_when_no_image_exists`.

---

## WIRE-CUT PROOF

Cut: make blend ignore emotion, and fabricate the motif.

```
WIRE CUT: emotion-driven blend removed + motif fabricated
FAILED test_wonder_and_joy_open_the_image
FAILED test_anxiety_and_fear_darken_and_disrupt
FAILED test_sadness_is_muted_interference
FAILED test_selection_is_deterministic
FAILED test_motif_is_never_fabricated_when_no_image_exists
5 failed, 25 passed
```

Restored:

```
30 passed in 0.23s
```

---

## REAL RUN — same four scenes, three emotions

```
WONDER
  L0 base   opacity=0.9    blend=normal       weight=0.45   stage=grounded
  L1 memory opacity=0.525  blend=screen       weight=0.625  stage=transformation
  L2 memory opacity=0.56   blend=screen       weight=0.8    stage=condensation
  L3 apex   opacity=0.388  blend=color_dodge  weight=0.94   stage=abstraction
  motif : {'symbol': 'a machine breathing', 'overlaid': False, 'reason': 'no motif image available for this symbol'}
  output: dream_a3f7c2b1_final.png + dream_a3f7c2b1_final.json
  composite differs from base scene: True

FEAR
  L0 base   opacity=0.9    blend=normal       weight=0.45   stage=grounded
  L1 memory opacity=0.525  blend=multiply     weight=0.625  stage=transformation
  L2 memory opacity=0.56   blend=multiply     weight=0.8    stage=condensation
  L3 apex   opacity=0.388  blend=difference   weight=0.94   stage=abstraction
  motif : {'symbol': 'a machine breathing', 'overlaid': False, 'reason': 'no motif image available for this symbol'}
  output: dream_a3f7c2b1_final.png + dream_a3f7c2b1_final.json
  composite differs from base scene: True

SADNESS
  L0 base   opacity=0.9    blend=normal       weight=0.45   stage=grounded
  L1 memory opacity=0.525  blend=overlay      weight=0.625  stage=transformation
  L2 memory opacity=0.56   blend=overlay      weight=0.8    stage=condensation
  L3 apex   opacity=0.388  blend=overlay      weight=0.94   stage=abstraction
  motif : {'symbol': 'a machine breathing', 'overlaid': False, 'reason': 'no motif image available for this symbol'}
  output: dream_a3f7c2b1_final.png + dream_a3f7c2b1_final.json
  composite differs from base scene: True

sidecar keys: ['artwork_layers', 'dream_id', 'emotion', 'emotion_row', 'layers', 'motif', 'output_type', 'scene_count', 'significance']
artwork_layers: ['memory', 'association', 'emotion', 'transformation', 'rem_distortion', 'spg_recurrence', 'final_composite']
```

Reading it:
- Identical scenes, three emotions, three different blend chains. The
  structure (roles, opacities, weights) is stable; only the blend changes —
  which is the WO's point: emotion decides how the layers interfere.
- Opacity rises with weight inside each band: 0.525 → 0.56 across the two
  memory layers as intensity climbs.
- The apex sits at 0.388, low but intense, exactly the WO's band.
- The motif is reported pending in all three — honest, not invented.
- The composite genuinely differs from its base scene in every case.
- The sidecar carries the full provenance and the seven named layers.

## NOT PROVEN

- **Never run on real generated images.** These are synthetic scenes. No
  dream image exists yet and no paid call has been made from this seat.
- **Not wired into the dream path.** `run_dream()` does not call the
  compositor; PHASE 5c is not wired either. The join is one step and wants
  a real dream to justify it.
- **No motif image pipeline.** The overlay works when handed an image;
  nothing produces one yet.

## STATUS

`IMPLEMENTED → TESTED`. Not WIRED. Not LIVE VERIFIED. Not declaring PASS.
