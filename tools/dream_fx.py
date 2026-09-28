"""
tools/dream_fx.py — CompositionDesigner FX pipeline for dream scenes.

WO-DREAM-ENGINE-001 PHASE 5c.

Ported from the live compositor at
`~/Desktop/Output/DISENELO-CompositionDesigner/transparent_video_compositor.html`
— read from the source, not from the WO's summary. Where the two differ, the
source wins and the difference is noted below.

Order, per the WO: blob tracking → datamosh → VCR → summagator.

**Divergence from the compositor, deliberate.** In the compositor,
`fxDatamosh` and `fxSlitscan` are TEMPORAL effects: datamosh consumes the
previous frame, slit-scan samples a ring buffer of recent frames. A dream
scene is a single still — there is no previous frame and no history. The WO
specifies the single-image equivalents (block displacement within one image;
slit-scan as a per-row sine displacement), and that is what is implemented
here. The temporal versions are meaningless on a still and are not faked.

FX selection is driven by the emotion vector, never random (WO PHASE 5c).
Strength scales with dream_intensity: early REM scenes get one subtle
effect, late REM scenes get several at full strength.

Deterministic: every effect takes a seeded RNG, so a dream's images can be
reproduced from its journal entry.

Requires PIL and numpy, both already present. No network, no paid API, no
server.py.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field as _field
from typing import Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ── Blob tracking (fxBlobTracking) ────────────────────────────────────────────
# Source constants, verbatim from the compositor.
BLOB_DETECT_W, BLOB_DETECT_H = 160, 90      # detection buffer, not full res
BLOB_UNIFORM_RANGE = 30                     # solid-colour guard: skip if range < 30
BLOB_AUTO_THRESH = 0.7                      # Nth percentile cutoff
BLOB_MEAN_SPLIT = 128                       # mean < 128 -> detect brights
LUMA = (0.299, 0.587, 0.114)

# Teal / violet, per the WO.
BLOB_TEAL = (64, 200, 196)
BLOB_VIOLET = (150, 110, 220)

# ── Datamosh (single-image form) ──────────────────────────────────────────────
DATAMOSH_BLOCK = 16
DATAMOSH_FRACTION = (0.30, 0.40)
DATAMOSH_OFFSET = (8, 24)

# ── VCR ───────────────────────────────────────────────────────────────────────
SCANLINE_THICKNESS = 2                      # compositor: clamp(thickness, 1, 8)
SCANLINE_GAP = 4                            # compositor: clamp(gap, 1, 16)
SCANLINE_ALPHA = (0.08, 0.12)
VHS_BANDS = (3, 6)
VHS_BAND_OFFSET = (4, 12)
CHROMA_SHIFT = 2                            # R +2px, B -2px
GRAIN_SIGMA = (4.0, 8.0)

# ── Summagator ────────────────────────────────────────────────────────────────
SUMMAGATOR_SCALES = (1.00, 0.95, 0.90)
SUMMAGATOR_OPACITIES = (1.00, 0.40, 0.20)
SLITSCAN_AMPLITUDE = (8, 16)

# ── Emotion → FX table (WO PHASE 5c) ──────────────────────────────────────────
# Driven by the emotion vector, NOT random.
EMOTION_FX: dict[str, dict[str, tuple[str, ...]]] = {
    "anxiety_fear": {
        "primary": ("glitch", "vcr", "night_vision"),
        "secondary": ("chromatic_warp", "vignette"),
    },
    "joy_wonder": {
        "primary": ("bloom", "hue_cycle", "kaleidoscope"),
        "secondary": ("chromatic_warp", "recolor"),
    },
    "sadness_grief": {
        "primary": ("posterize", "dither", "trails"),
        "secondary": ("receipt_paper", "recolor"),
    },
    "achievement": {
        "primary": ("bloom", "edge_detect"),
        "secondary": ("slitscan_up",),
    },
    "nostalgia": {
        "primary": ("oil_paint", "trails", "receipt_paper"),
        "secondary": ("recolor",),
    },
    "curiosity": {
        "primary": ("edge_detect", "frame_diff"),
        "secondary": ("depth_overlay",),
    },
}

# Above this, everything combines (WO: "Maximum surreal (intensity > 0.85)").
MAX_SURREAL_INTENSITY = 0.85
MAX_SURREAL_FX = ("invert", "kaleidoscope", "hue_cycle")

# Same emotion → row mapping the prompt builder uses, so a scene's FX and its
# lighting agree instead of describing two different dreams.
_EMOTION_TO_ROW = {
    "joy": "joy_wonder", "wonder": "joy_wonder",
    "fear": "anxiety_fear", "anxiety": "anxiety_fear", "anger": "anxiety_fear",
    "sadness": "sadness_grief", "grief": "sadness_grief",
    "curiosity": "curiosity", "achievement": "achievement", "nostalgia": "nostalgia",
}

# The four the WO names as the base pipeline, always applied in this order.
BASE_PIPELINE = ("blob_tracking", "datamosh", "vcr", "summagator")

# "fxVignette + fxGrain — always present at low levels as base texture."
# Applied last, at every intensity, so they sit over whatever else ran.
BASE_TEXTURE = ("vignette", "grain")
BASE_TEXTURE_STRENGTH = 0.18


def row_for_emotion(emotion: str) -> str:
    return _EMOTION_TO_ROW.get((emotion or "").strip().lower(), "joy_wonder")


def select_fx(emotion: str, intensity: float) -> list[str]:
    """
    Which effects this scene gets. Emotion picks them; intensity decides how
    many. Never random — the same emotion and intensity always select the
    same set.

    Early REM (low intensity): one primary effect.
    Late REM (high intensity): primary + secondary.
    Above MAX_SURREAL_INTENSITY: everything, plus invert/kaleidoscope/hue.
    """
    value = max(0.0, min(1.0, float(intensity)))
    row = EMOTION_FX[row_for_emotion(emotion)]

    chosen: list[str] = []
    if value >= MAX_SURREAL_INTENSITY:
        chosen = list(row["primary"]) + list(row["secondary"]) + list(MAX_SURREAL_FX)
    elif value >= 0.5:
        take = 1 + int(round((value - 0.5) * 4))     # 1..3 primaries
        chosen = list(row["primary"][:take]) + list(row["secondary"][:1])
    else:
        # "Early REM scenes: subtle (single FX, low strength)" — one effect,
        # not none. A low-intensity scene is still a dream.
        chosen = list(row["primary"][:1])

    out: list[str] = []
    for name in chosen:
        if name not in out:
            out.append(name)
    return out


# ── Helpers ───────────────────────────────────────────────────────────────────

def _as_rgb(image: Image.Image) -> Image.Image:
    return image if image.mode == "RGB" else image.convert("RGB")


def _luma(arr: np.ndarray) -> np.ndarray:
    return (arr[..., 0] * LUMA[0] + arr[..., 1] * LUMA[1] + arr[..., 2] * LUMA[2])


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


# ── 1. Blob tracking ──────────────────────────────────────────────────────────

def detect_blobs(image: Image.Image, auto_thresh: float = BLOB_AUTO_THRESH) -> list[dict]:
    """
    Adaptive-percentile blob detection, ported from the compositor.

    1. Downsample to a 160x90 detection buffer.
    2. Luminance histogram over that buffer.
    3. Skip entirely if lumMax - lumMin < 30 — refuse to hallucinate blobs on
       a flat surface. This is the compositor's own "solid-colour guard".
    4. mean < 128 -> the source is dark, so detect the BRIGHT pixels;
       otherwise detect the darks (inverted compare).
    5. Cutoff = Nth percentile via a CDF walk over the histogram.
    6. Connected-component labelling (union-find), boxes in detect space
       scaled back to image space.
    """
    small = _as_rgb(image).resize((BLOB_DETECT_W, BLOB_DETECT_H), Image.BILINEAR)
    arr = np.asarray(small, dtype=np.float32)
    lum = _luma(arr).astype(np.int32)

    lum_min, lum_max = int(lum.min()), int(lum.max())
    if auto_thresh > 0 and (lum_max - lum_min) < BLOB_UNIFORM_RANGE:
        return []                                   # solid-colour guard

    if auto_thresh <= 0:
        cutoff = 0.5 * 255                          # legacy fixed path
        detect_bright = True
    else:
        detect_bright = float(lum.mean()) < BLOB_MEAN_SPLIT
        clamp_p = max(0.05, min(0.95, float(auto_thresh)))
        hist = np.bincount(lum.ravel(), minlength=256)
        target = clamp_p * lum.size
        cutoff = int(np.searchsorted(np.cumsum(hist), target))

    mask = (lum >= cutoff) if detect_bright else (lum <= cutoff)
    if not mask.any():
        return []

    # Connected components, 4-connectivity, iterative flood fill.
    labels = np.zeros_like(mask, dtype=np.int32)
    blobs: list[dict] = []
    current = 0
    h, w = mask.shape
    sx, sy = image.width / w, image.height / h

    for y0 in range(h):
        for x0 in range(w):
            if not mask[y0, x0] or labels[y0, x0]:
                continue
            current += 1
            stack = [(y0, x0)]
            labels[y0, x0] = current
            min_x = max_x = x0
            min_y = max_y = y0
            area = 0
            while stack:
                cy, cx = stack.pop()
                area += 1
                min_x, max_x = min(min_x, cx), max(max_x, cx)
                min_y, max_y = min(min_y, cy), max(max_y, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = current
                        stack.append((ny, nx))
            if area < 4:
                continue                            # noise
            blobs.append({
                "area": area,
                "box": (int(min_x * sx), int(min_y * sy),
                        int((max_x + 1) * sx), int((max_y + 1) * sy)),
                "centroid": (int((min_x + max_x) / 2 * sx), int((min_y + max_y) / 2 * sy)),
            })

    blobs.sort(key=lambda b: b["area"], reverse=True)
    return blobs


def fx_blob_tracking(
    image: Image.Image,
    strength: float,
    rng: random.Random,
    *,
    boxes: bool = True,
    dots: bool = True,
) -> Image.Image:
    """Draw detected regions as semi-transparent teal/violet shapes."""
    blobs = detect_blobs(image)
    if not blobs:
        return image

    base = _as_rgb(image).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    alpha = int(_lerp(40, 140, strength))

    for i, blob in enumerate(blobs[:12]):
        colour = BLOB_TEAL if i % 2 == 0 else BLOB_VIOLET
        if boxes:
            draw.rectangle(blob["box"], outline=colour + (alpha,), width=2)
        if dots:
            cx, cy = blob["centroid"]
            r = max(2, int(3 + strength * 4))
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=colour + (alpha,))

    return Image.alpha_composite(base, overlay).convert("RGB")


# ── 2. Datamosh (single-image block displacement) ─────────────────────────────

def fx_datamosh(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    """
    Pixel-block displacement — simulates P-frame compression corruption.

    30-40% of 16x16 blocks copied from a nearby offset of 8-24px. The
    compositor's version consumes the previous video frame; a still has none,
    so blocks are sourced from elsewhere in the same image.
    """
    src = _as_rgb(image)
    arr = np.asarray(src).copy()
    h, w = arr.shape[:2]
    fraction = _lerp(DATAMOSH_FRACTION[0], DATAMOSH_FRACTION[1], strength)

    for by in range(0, h - DATAMOSH_BLOCK, DATAMOSH_BLOCK):
        for bx in range(0, w - DATAMOSH_BLOCK, DATAMOSH_BLOCK):
            if rng.random() > fraction:
                continue
            dx = rng.randint(*DATAMOSH_OFFSET) * rng.choice((-1, 1))
            dy = rng.randint(*DATAMOSH_OFFSET) * rng.choice((-1, 1))
            sy, sx = by + dy, bx + dx
            if not (0 <= sy < h - DATAMOSH_BLOCK and 0 <= sx < w - DATAMOSH_BLOCK):
                continue
            arr[by:by + DATAMOSH_BLOCK, bx:bx + DATAMOSH_BLOCK] = \
                arr[sy:sy + DATAMOSH_BLOCK, sx:sx + DATAMOSH_BLOCK]

    return Image.fromarray(arr)


# ── 3. VCR ────────────────────────────────────────────────────────────────────

def fx_vcr(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    """
    Scanlines + tracking error + chromatic aberration + grain.

    Tracking-error band geometry follows the compositor: a band whose height
    scales with the effect amount, with per-row horizontal jitter inside it.
    """
    src = _as_rgb(image)
    arr = np.asarray(src).astype(np.float32)
    h, w = arr.shape[:2]

    # -- tracking error: horizontal bands, each row inside jittered --
    n_bands = rng.randint(*VHS_BANDS)
    for _ in range(n_bands):
        band_h = max(2, int((40 + strength * 60) / 20 * rng.uniform(1.0, 2.0)))
        y0 = rng.randint(0, max(0, h - band_h - 1))
        for y in range(y0, min(h, y0 + band_h)):
            dx = int(rng.uniform(-1, 1) * _lerp(*VHS_BAND_OFFSET, strength))
            if dx:
                arr[y] = np.roll(arr[y], dx, axis=0)
        # desaturate inside the band, as the compositor does
        band = arr[y0:min(h, y0 + band_h)]
        grey = _luma(band)[..., None]
        arr[y0:min(h, y0 + band_h)] = band * 0.55 + grey * 0.45

    # -- chromatic aberration: R +2px, B -2px, horizontal --
    shift = max(1, int(CHROMA_SHIFT * _lerp(0.5, 1.5, strength)))
    arr[..., 0] = np.roll(arr[..., 0], shift, axis=1)
    arr[..., 2] = np.roll(arr[..., 2], -shift, axis=1)

    # -- scanlines: dark horizontal lines every thickness+gap px --
    step = SCANLINE_THICKNESS + SCANLINE_GAP
    alpha = _lerp(*SCANLINE_ALPHA, strength)
    for y in range(0, h, step):
        arr[y:y + SCANLINE_THICKNESS] *= (1.0 - alpha)

    # -- gaussian grain --
    sigma = _lerp(*GRAIN_SIGMA, strength)
    arr += np.asarray(
        [[rng.gauss(0, sigma) for _ in range(w)] for _ in range(h)],
        dtype=np.float32,
    )[..., None]

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ── 4. Summagator ─────────────────────────────────────────────────────────────

def fx_summagator(
    image: Image.Image,
    strength: float,
    rng: random.Random,
    *,
    upward: bool = False,
) -> Image.Image:
    """
    Three scaled copies screen-composited, with a per-row slit-scan
    displacement of sin(row/H * pi) * 8-16px.

    The compositor's slit-scan samples a ring buffer of past frames. A still
    has no history, so the WO's single-image form is used: a sine
    displacement across the rows.
    """
    src = _as_rgb(image)
    w, h = src.size
    amplitude = _lerp(*SLITSCAN_AMPLITUDE, strength)
    if upward:
        amplitude = -amplitude

    base = np.zeros((h, w, 3), dtype=np.float32)

    for scale, opacity in zip(SUMMAGATOR_SCALES, SUMMAGATOR_OPACITIES):
        if scale != 1.0:
            sw, sh = max(1, int(w * scale)), max(1, int(h * scale))
            layer = src.resize((sw, sh), Image.BILINEAR)
            canvas = Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(layer, ((w - sw) // 2, (h - sh) // 2))
        else:
            canvas = src

        arr = np.asarray(canvas).astype(np.float32)
        for y in range(h):
            dx = int(math.sin(y / max(1, h) * math.pi) * amplitude)
            if dx:
                arr[y] = np.roll(arr[y], dx, axis=0)

        # screen composite: 1 - (1-a)(1-b)
        contribution = arr * opacity
        base = 255.0 - (255.0 - base) * (255.0 - contribution) / 255.0

    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


# ── Additional FX named by the WO ─────────────────────────────────────────────

def fx_invert(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    arr = np.asarray(_as_rgb(image)).astype(np.float32)
    return Image.fromarray(
        np.clip(arr * (1 - strength) + (255 - arr) * strength, 0, 255).astype(np.uint8))


def fx_posterize(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    levels = max(2, int(_lerp(12, 3, strength)))
    arr = np.asarray(_as_rgb(image)).astype(np.float32)
    step = 255.0 / (levels - 1)
    return Image.fromarray(np.clip(np.round(arr / step) * step, 0, 255).astype(np.uint8))


def fx_bloom(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    src = _as_rgb(image)
    blurred = src.filter(ImageFilter.GaussianBlur(radius=_lerp(3, 14, strength)))
    a = np.asarray(src).astype(np.float32)
    b = np.asarray(blurred).astype(np.float32)
    return Image.fromarray(
        np.clip(255.0 - (255.0 - a) * (255.0 - b * strength) / 255.0, 0, 255).astype(np.uint8))


def fx_edge_detect(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    src = _as_rgb(image)
    edges = src.filter(ImageFilter.FIND_EDGES)
    a = np.asarray(src).astype(np.float32)
    e = np.asarray(edges).astype(np.float32)
    return Image.fromarray(np.clip(a * (1 - strength) + e * strength, 0, 255).astype(np.uint8))


def fx_vignette(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    src = _as_rgb(image)
    w, h = src.size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    mask = np.clip(1.0 - (dist - 0.5) * _lerp(0.4, 1.2, strength), 0.0, 1.0)[..., None]
    return Image.fromarray(
        np.clip(np.asarray(src).astype(np.float32) * mask, 0, 255).astype(np.uint8))


def fx_grain(image: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    arr = np.asarray(_as_rgb(image)).astype(np.float32)
    h, w = arr.shape[:2]
    sigma = _lerp(*GRAIN_SIGMA, strength)
    noise = np.asarray([[rng.gauss(0, sigma) for _ in range(w)] for _ in range(h)],
                       dtype=np.float32)[..., None]
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))


# Effects named in the WO's table that map onto an implementation here.
# Anything unmapped is skipped rather than silently substituted.
_FX_IMPL = {
    "blob_tracking": fx_blob_tracking,
    "datamosh": fx_datamosh,
    "vcr": fx_vcr,
    "summagator": fx_summagator,
    "invert": fx_invert,
    "posterize": fx_posterize,
    "bloom": fx_bloom,
    "edge_detect": fx_edge_detect,
    "vignette": fx_vignette,
    "grain": fx_grain,
    # WO table aliases onto the base pipeline
    "glitch": fx_datamosh,
    "trails": fx_summagator,
    "slitscan_up": lambda img, s, r: fx_summagator(img, s, r, upward=True),
}

UNIMPLEMENTED_FX = (
    "night_vision", "chromatic_warp", "hue_cycle", "kaleidoscope", "recolor",
    "dither", "receipt_paper", "oil_paint", "frame_diff", "depth_overlay",
)


@dataclass
class FXResult:
    image: Image.Image
    applied: list[str] = _field(default_factory=list)
    skipped: list[str] = _field(default_factory=list)
    strength: float = 0.0


def _run_pipeline(
    image: Image.Image,
    *,
    emotion: str,
    intensity: float,
    seed: int | None = None,
    include_base: bool = True,
) -> FXResult:
    """
    Apply the FX pipeline for one dream scene.

    emotion   — dominant emotion; selects the FX row.
    intensity — the scene's dream intensity; scales strength AND how many
                effects are applied.
    seed      — reproducibility. Same seed, same image out.

    The four base effects run first, in the WO's order, then the
    emotion-selected ones. Effects named in the WO but not implemented here
    are reported in `skipped`, never silently substituted.
    """
    rng = random.Random(seed)
    strength = max(0.0, min(1.0, float(intensity)))
    out = _as_rgb(image)

    selected = select_fx(emotion, strength)
    order: list[str] = []
    # The four named base effects only run once the scene has left waking
    # residue; below that a single subtle effect is the whole treatment.
    if include_base and strength >= 0.25:
        order.extend(BASE_PIPELINE)
    for name in selected:
        if name not in order:
            order.append(name)
    # "fxVignette + fxGrain — always present at low levels as base texture."
    # Always, at every intensity, applied last so they sit over everything.
    for name in BASE_TEXTURE:
        if name not in order:
            order.append(name)

    applied: list[str] = []
    skipped: list[str] = []
    for name in order:
        impl = _FX_IMPL.get(name)
        if impl is None:
            skipped.append(name)
            continue
        try:
            level = BASE_TEXTURE_STRENGTH if name in BASE_TEXTURE else strength
            out = impl(out, level, rng)
            applied.append(name)
        except Exception:
            skipped.append(name)

    return FXResult(image=out, applied=applied, skipped=skipped, strength=strength)


def apply_to_file(
    path: str,
    out_path: str,
    *,
    emotion: str,
    intensity: float,
    seed: int | None = None,
) -> FXResult:
    """Apply the pipeline to a file on disk and save the result."""
    with Image.open(path) as img:
        result = _run_pipeline(img, emotion=emotion, intensity=intensity, seed=seed)
    result.image.save(out_path)
    return result


# ── Compatibility surface — WO-DREAM-006 ──────────────────────────────────────
#
# tools/dream_fx.py was built twice on 2026-09-27: WO-DREAM-006 (b0dec8a,
# 06:35) and this file, WO-DREAM-ENGINE-001 PHASE 5c (f877ff3, 06:43). The
# second replaced the first wholesale and took its API with it.
#
# That was not only a red test file. tools/image_gen_agent.py:233 calls
#     apply_fx(img, intensity, emotion_vector or {})
# inside a `try/except Exception` that logs a warning and carries on, so from
# f877ff3 onward EVERY generated dream image silently skipped the entire FX
# pipeline, saved untreated, and still reported ok=True to its caller.
#
# Both APIs are kept. The WO-DREAM-006 names are thin adapters over the
# PHASE 5c implementations — one pipeline, two call shapes, nothing
# reimplemented and nothing dropped.


def dominant_emotion(emotion_vector: "Mapping[str, float] | dict | None") -> str:
    """Strongest emotion in a vector. '' when empty — row_for_emotion defaults."""
    vec = {k: float(v) for k, v in dict(emotion_vector or {}).items()}
    if not vec:
        return ""
    return max(vec.items(), key=lambda kv: kv[1])[0]


def apply_fx(
    image: Image.Image,
    intensity: float | None = None,
    emotion_vector: dict | None = None,
    *,
    emotion: str | None = None,
    seed: int | None = None,
    include_base: bool = True,
):
    """
    Two call shapes, one pipeline.

        apply_fx(img, emotion="wonder", intensity=0.7)  -> FXResult  (PHASE 5c)
        apply_fx(img, 0.7, {"wonder": 0.9})             -> Image     (WO-DREAM-006)

    The positional form is what image_gen_agent.py has always called. It
    returns RGBA, as that caller expects.
    """
    if emotion is not None:
        return _run_pipeline(
            image, emotion=emotion,
            intensity=float(intensity if intensity is not None else 0.0),
            seed=seed, include_base=include_base,
        )
    out = _run_pipeline(
        image, emotion=dominant_emotion(emotion_vector),
        intensity=float(intensity or 0.0), seed=seed, include_base=include_base,
    ).image
    return out if out.mode == "RGBA" else out.convert("RGBA")


def _as_rgba(img: Image.Image) -> Image.Image:
    """WO-DREAM-006 returned RGBA from every effect. PHASE 5c works in RGB."""
    return img if img.mode == "RGBA" else img.convert("RGBA")


def blob_tracking(image: Image.Image, intensity: float,
                  rng: random.Random | None = None) -> Image.Image:
    """WO-DREAM-006 name for fx_blob_tracking."""
    return _as_rgba(fx_blob_tracking(image, float(intensity), rng or random.Random()))


def datamosh(image: Image.Image, intensity: float, amount: float = 1.0,
             rng: random.Random | None = None) -> Image.Image:
    """
    WO-DREAM-006 name for fx_datamosh.

    `amount` scaled displacement in the WO-DREAM-006 implementation; it scales
    strength here, which is the same knob in this one. Not ignored.
    """
    strength = max(0.0, min(1.0, float(intensity) * float(amount)))
    return _as_rgba(fx_datamosh(image, strength, rng or random.Random()))


def vcr(image: Image.Image, intensity: float,
        rng: random.Random | None = None) -> Image.Image:
    """WO-DREAM-006 name for fx_vcr."""
    return _as_rgba(fx_vcr(image, float(intensity), rng or random.Random()))


def summagator(image: Image.Image, intensity: float,
               rng: random.Random | None = None) -> Image.Image:
    """WO-DREAM-006 name for fx_summagator."""
    return _as_rgba(fx_summagator(image, float(intensity), rng or random.Random()))
