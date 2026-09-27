# WO-DREAM-ENGINE-001 — creative channel joined end to end (5b → 5c → 6)

**Filed by:** Builder 2 · 2026-09-27
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · PIL + numpy

---

## STATE BEFORE

PHASE 5c (`dream_fx`) and PHASE 6 (`layer_compositor`) were built and tested
but **not wired**. `run_dream()` generated scene images and stopped. Nothing
treated them and nothing composited them.

## WHAT CHANGED

`render_dream_artwork()` in `dream_faculty.py` joins the three phases:

    scene prompts → images (5b) → FX treatment (5c) → composited artwork (6)

Called from `run_dream()` behind `publish_phases`, the same gate as every
other side effect. Journal gains `scene_images`, `fx_applied`,
`final_artwork`, `artwork_sidecar`, `artwork_layers`, `artwork_motif`.

---

## THE BUG THIS RUN FOUND

The first end-to-end run produced a valid artwork with the wrong foundation:

```
L0 base   op=0.9    blend=normal       stage=abstraction     <-- WRONG
L1 memory op=0.572  blend=screen       stage=condensation
L2 memory op=0.572  blend=screen       stage=condensation
L3 apex   op=0.344  blend=color_dodge  stage=condensation
```

`generate_scene_images()` sorts highest-intensity-first so a capped run keeps
the most transformed scenes. But PHASE 6 makes **Scene 01 the base layer** —
"Normal, structural foundation" — and §3d defines Scene 01 as the grounded,
literal location. Sorting by intensity made the most ABSTRACT frame the
structural base, and numbered `scene_01.png` as the most intense.

Worse: with a cap, the grounded scene is the *least* intense, so it was the
first one dropped. The composite was losing exactly the layer it cannot do
without.

**Neither unit test caught this.** `dream_fx` and `layer_compositor` were
each correct in isolation. The defect lived in the seam, and only appeared
when a real dream ran through both.

**Fix:** intensity-first still decides *which* scenes survive the cap, but
the first scene is always kept, and narrative order is restored before
numbering and compositing.

```
L0 base   op=0.9    blend=normal       stage=grounded       int=0.08
L1 memory op=0.572  blend=screen       stage=condensation   int=0.8
L2 memory op=0.572  blend=screen       stage=condensation   int=0.8
L3 apex   op=0.4    blend=color_dodge  stage=abstraction    int=1.0
```

---

## REAL RUN — a complete dream, real files on disk

The **only** stub is the paid DALL-E call, replaced by a generator that
writes a real PNG. Everything after it is the production pipeline.

```
DREAM 1d6b51e0 | NREM+REM | 5 cycles | 14 scenes | intensity 1.0

SCENE IMAGES (real PNGs on disk):
   dream_1d6b51e0_scene_01.png       154776 bytes  (384, 256)
   dream_1d6b51e0_scene_02.png       192260 bytes  (384, 256)
   dream_1d6b51e0_scene_03.png       192045 bytes  (384, 256)
   dream_1d6b51e0_scene_04.png       193951 bytes  (384, 256)

FX PER SCENE:
   scene 1: ['bloom', 'vignette', 'grain']
   scene 2: ['blob_tracking', 'datamosh', 'vcr', 'summagator', 'bloom', 'vignette', 'grain']
   scene 3: ['blob_tracking', 'datamosh', 'vcr', 'summagator', 'bloom', 'vignette', 'grain']
   scene 4: ['blob_tracking', 'datamosh', 'vcr', 'summagator', 'bloom', 'invert', 'vignette', 'grain']

FINAL ARTWORK: dream_1d6b51e0_final.png  189755 bytes  (384, 256)  exists=True
SIDECAR      : dream_1d6b51e0_final.json

LAYER PROVENANCE:
   L0 base   op=0.9    blend=normal       stage=grounded       int=0.08
   L1 memory op=0.572  blend=screen       stage=condensation   int=0.8
   L2 memory op=0.572  blend=screen       stage=condensation   int=0.8
   L3 apex   op=0.4    blend=color_dodge  stage=abstraction    int=1.0

BASE LAYER IS THE GROUNDED SCENE: True
OUTPUT TAG: DREAM
```

Reading it:
- Five cycles, 14 scenes planned, 4 generated under the cost cap.
- Four real PNGs on disk, each ~190KB at 384×256.
- FX scale with the scene: the grounded frame gets 3 subtle effects, the
  abstraction frame gets 8 including `invert`. That is §5c's "early REM
  subtle, late REM heavy" holding in a real run.
- One final artwork, 189,755 bytes, plus a provenance sidecar.
- Base layer is the grounded scene. Apex is the abstraction scene.
- Everything tagged `DREAM`.

This is the first complete artefact the dream engine has produced.

## NOT PROVEN

- **No real generated image.** The DALL-E call is stubbed; no paid call has
  been made from this seat. The pipeline is real, the source imagery is not.
- **Not live.** No dream has fired on the running server (PID 9577, up 5h+,
  still pre-`ff98065`). This ran out of process.
- **Motif overlay untested with an image** in the wired path — the lexicon
  was empty on a first dream, so `artwork_motif` reports no symbol.

## STATUS

`IMPLEMENTED → WIRED → TESTED`. Not LIVE VERIFIED. Not declaring PASS.
