"""
tools/dream_fx.py — CompositionDesigner FX pipeline for dream imagery.

WO-DREAM-006 §5c.

Implements Python equivalents of the four DISENELO CompositionDesigner effects,
applied in order: blob_tracking → datamosh → vcr → summagator.

Scaling: all effects are modulated by a dream_intensity 0.0–1.0 value so
early-cycle (gentle) dreams look different from peak-REM (surreal) dreams.

Requires: Pillow (PIL). No numpy dependency.
"""
from __future__ import annotations

import math
import os
import random
import struct
from typing import Mapping, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter


# ── Teal / violet palette for blob overlays ────────────────────────────────────
_TEAL   = (0, 200, 180, 120)   # RGBA
_VIOLET = (140, 60, 200, 100)


# ── 1. Blob tracking (fxBlobTracking) ─────────────────────────────────────────

def blob_tracking(
    img: Image.Image,
    intensity: float,
    *,
    dark_source: bool = True,
    blob_boxes: bool = True,
    blob_dots: bool = True,
) -> Image.Image:
    """
    Adaptive luminance blob detection.

    Dark source (default): detect bright regions.
    Light source (inverted): detect dark regions.
    70th-percentile adaptive threshold.
    Solid-colour guard: skip if lumMax-lumMin < 30.
    Draws detected regions as semi-transparent teal/violet shapes.
    """
    img = img.convert("RGBA")
    lum = img.convert("L")

    pixels = list(lum.getdata())
    lum_min, lum_max = min(pixels), max(pixels)

    if lum_max - lum_min < 30:
        return img  # solid-colour guard

    sorted_px = sorted(pixels)
    threshold = sorted_px[int(0.70 * len(sorted_px))]

    if not dark_source:
        threshold = lum_max - (threshold - lum_min)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = img.size
    block = max(8, int(16 * (1.0 - intensity * 0.5)))  # smaller blocks at high intensity
    blob_color = _TEAL if intensity < 0.5 else _VIOLET

    for y in range(0, h, block):
        for x in range(0, w, block):
            region_pixels = []
            for py in range(y, min(y + block, h)):
                for px in range(x, min(x + block, w)):
                    region_pixels.append(lum.getpixel((px, py)))
            if not region_pixels:
                continue
            avg = sum(region_pixels) / len(region_pixels)
            detected = avg > threshold if dark_source else avg < threshold
            if detected:
                alpha_scale = min(1.0, intensity * 1.4)
                color = blob_color[:3] + (int(blob_color[3] * alpha_scale),)
                if blob_boxes:
                    draw.rectangle(
                        [x, y, min(x + block - 1, w - 1), min(y + block - 1, h - 1)],
                        fill=color,
                    )
                if blob_dots:
                    cx, cy = x + block // 2, y + block // 2
                    r = max(2, block // 4)
                    dot_color = blob_color[:3] + (min(255, color[3] + 40),)
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=dot_color)

    return ImageChops.composite(overlay, img, overlay.split()[3])


# ── 2. Datamosh (fxDatamosh) ─────────────────────────────────────────────────

def datamosh(
    img: Image.Image,
    intensity: float,
    *,
    amount: float = 0.4,
) -> Image.Image:
    """
    Pixel-block displacement. 30-40% of 16×16 blocks copied from a nearby
    offset. Simulates P-frame compression corruption.
    """
    img = img.convert("RGBA")
    out = img.copy()
    w, h = img.size
    rng = random.Random(int(intensity * 1000))

    block = 16
    effective_amount = max(0.1, min(0.7, amount * intensity))
    max_offset = int(8 + 16 * intensity)  # 8-24px

    for y in range(0, h, block):
        for x in range(0, w, block):
            if rng.random() > effective_amount:
                continue
            ox = rng.randint(-max_offset, max_offset)
            oy = rng.randint(-max_offset // 2, max_offset // 2)
            src_x = max(0, min(w - block, x + ox))
            src_y = max(0, min(h - block, y + oy))
            bw = min(block, w - x, w - src_x)
            bh = min(block, h - y, h - src_y)
            if bw <= 0 or bh <= 0:
                continue
            region = img.crop((src_x, src_y, src_x + bw, src_y + bh))
            out.paste(region, (x, y))

    return out


# ── 3. VCR (fxVhsTrackError + fxScanlines + fxCrt) ──────────────────────────

def vcr(img: Image.Image, intensity: float) -> Image.Image:
    """
    Three sub-layers:
    - Scanlines: dark horizontal lines every 3-4px, alpha 0.08-0.12
    - Tracking error: 3-6 horizontal bands offset 4-12px
    - Chromatic aberration: R +2px / B -2px horizontal
    - Gaussian grain: σ=4-8
    """
    img = img.convert("RGBA")
    out = img.copy()
    w, h = img.size
    rng = random.Random(int(intensity * 999))

    # Chromatic aberration (shift R right, B left)
    shift = max(1, int(2 + intensity * 4))
    r, g, b, a = out.split()
    r = r.transform(r.size, Image.AFFINE, (1, 0, -shift, 0, 1, 0))
    b = b.transform(b.size, Image.AFFINE, (1, 0, shift, 0, 1, 0))
    out = Image.merge("RGBA", (r, g, b, a))

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Scanlines
    scanline_step = rng.randint(3, 4)
    scanline_alpha = int(255 * rng.uniform(0.08, 0.12) * intensity)
    for y in range(0, h, scanline_step):
        draw.line([(0, y), (w - 1, y)], fill=(0, 0, 0, scanline_alpha))

    # Tracking error bands
    n_bands = rng.randint(2, max(2, int(6 * intensity)))
    for _ in range(n_bands):
        band_y = rng.randint(0, h - 1)
        band_h = rng.randint(1, max(2, int(8 * intensity)))
        band_off = rng.randint(-12, 12)
        band_region = out.crop((0, band_y, w, min(h, band_y + band_h)))
        shifted = band_region.transform(
            band_region.size,
            Image.AFFINE,
            (1, 0, -band_off, 0, 1, 0),
        )
        out.paste(shifted, (0, band_y))

    out = ImageChops.composite(overlay, out, overlay.split()[3])

    # Gaussian grain (simulated via ImageFilter)
    if intensity > 0.2:
        grain_strength = int(4 + intensity * 4)
        grain_strength = min(grain_strength, 8)
        grain = Image.new("L", img.size, 128)
        for _ in range(grain_strength):
            grain = grain.filter(ImageFilter.GaussianBlur(0.5))
        # Add random noise to grain layer
        grain_px = list(grain.getdata())
        noisy = [max(0, min(255, v + rng.randint(-20, 20))) for v in grain_px]
        grain.putdata(noisy)
        grain_rgba = grain.convert("RGBA")
        strength = int(30 * intensity)
        faded = Image.new("RGBA", img.size, (0, 0, 0, 0))
        faded.paste(grain_rgba, (0, 0), grain.point(lambda v: strength))
        out = ImageChops.screen(out, faded)

    return out


# ── 4. Summagator (fxSlitscan + fxTrails) ────────────────────────────────────

def summagator(img: Image.Image, intensity: float) -> Image.Image:
    """
    3 copies at scales 1.0/0.95/0.90, opacities 1.0/0.4/0.2.
    Slit-scan vertical displacement: sin(row/H×π) × 8-16px per row.
    Screen or soft-light composite.
    """
    img = img.convert("RGBA")
    w, h = img.size

    max_disp = int(8 + 8 * intensity)  # 8-16px

    # Slit-scan displacement on the base image
    slitted = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for row in range(h):
        disp = int(math.sin(row / max(1, h) * math.pi) * max_disp * intensity)
        src_x = max(0, min(w - 1, abs(disp)))
        if disp >= 0:
            row_strip = img.crop((0, row, w - disp, row + 1))
            slitted.paste(row_strip, (disp, row))
        else:
            row_strip = img.crop((src_x, row, w, row + 1))
            slitted.paste(row_strip, (0, row))

    # Three copies at different scales and opacities
    layers = [
        (slitted,                              1.0, 1.0),
        (slitted.resize((int(w * 0.95), int(h * 0.95)), Image.LANCZOS), 0.4, 0.95),
        (slitted.resize((int(w * 0.90), int(h * 0.90)), Image.LANCZOS), 0.2, 0.90),
    ]

    out = img.copy()
    for layer_img, opacity, scale in layers:
        if scale < 1.0:
            # Centre the scaled layer
            lw, lh = layer_img.size
            padded = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ox, oy = (w - lw) // 2, (h - lh) // 2
            padded.paste(layer_img, (ox, oy))
            layer_img = padded

        # Apply opacity
        r2, g2, b2, a2 = layer_img.split()
        a2 = a2.point(lambda v: int(v * opacity))
        layer_img = Image.merge("RGBA", (r2, g2, b2, a2))

        if intensity > 0.5:
            out = ImageChops.screen(out, layer_img)
        else:
            out = ImageChops.soft_light(out, layer_img)

    return out


# ── 5. Selective FX (by emotion) ─────────────────────────────────────────────

def _apply_glitch(img: Image.Image, intensity: float) -> Image.Image:
    """Horizontal slice displacement — anxiety/fear dominant."""
    w, h = img.size
    rng = random.Random(int(intensity * 7777))
    out = img.copy()
    n_slices = int(4 + intensity * 8)
    for _ in range(n_slices):
        sy = rng.randint(0, h - 2)
        sh = rng.randint(1, max(1, int(h * 0.04 * intensity)))
        off = rng.randint(-int(w * 0.15 * intensity), int(w * 0.15 * intensity))
        if off == 0:
            continue
        strip = img.crop((0, sy, w, min(h, sy + sh)))
        shifted = strip.transform(
            strip.size, Image.AFFINE, (1, 0, -off, 0, 1, 0)
        )
        out.paste(shifted, (0, sy))
    return out


def _apply_bloom(img: Image.Image, intensity: float) -> Image.Image:
    """Glow bloom — joy/wonder/achievement."""
    blurred = img.filter(ImageFilter.GaussianBlur(radius=int(3 + intensity * 5)))
    return ImageChops.screen(img, blurred)


def _apply_edge_detect(img: Image.Image, intensity: float) -> Image.Image:
    """Edge outlines — analytical/curiosity dominant."""
    edges = img.filter(ImageFilter.FIND_EDGES)
    alpha = int(100 * intensity)
    r, g, b, a = edges.split()
    a = a.point(lambda v: min(v, alpha))
    edges = Image.merge("RGBA", (r, g, b, a))
    return ImageChops.add(img, edges)


# ── 6. Main apply_fx ─────────────────────────────────────────────────────────

def apply_fx(
    img: Image.Image,
    intensity: float,
    emotion_vector: Mapping[str, float] | None = None,
) -> Image.Image:
    """
    Apply all four CompositionDesigner effects in canonical order:
    blob_tracking → datamosh → vcr → summagator.

    Then apply selective FX based on emotion vector.
    Intensity 0.0-1.0 scales all effects.
    """
    intensity = max(0.0, min(1.0, float(intensity)))
    ev = dict(emotion_vector or {})

    img = img.convert("RGBA")

    if intensity > 0.05:
        img = blob_tracking(img, intensity, dark_source=True, blob_boxes=True, blob_dots=True)
    if intensity > 0.10:
        img = datamosh(img, intensity, amount=0.3 + 0.2 * intensity)
    if intensity > 0.10:
        img = vcr(img, intensity)
    if intensity > 0.15:
        img = summagator(img, intensity)

    # Selective FX
    anxiety = float(ev.get("anxiety", 0.0) or ev.get("fear", 0.0))
    joy = float(ev.get("joy", 0.0))
    wonder = float(ev.get("wonder", 0.0))
    curiosity = float(ev.get("curiosity", 0.0))

    if anxiety > 0.5 and intensity > 0.3:
        img = _apply_glitch(img, intensity * anxiety)
    if (joy + wonder) > 0.6 and intensity > 0.2:
        img = _apply_bloom(img, intensity * (joy + wonder) / 2.0)
    if curiosity > 0.5 and intensity > 0.2:
        img = _apply_edge_detect(img, intensity * curiosity * 0.5)

    return img
