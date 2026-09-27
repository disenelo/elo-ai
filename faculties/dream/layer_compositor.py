"""
faculties/dream/layer_compositor.py — Multi-frame visual layering engine.

WO-DREAM-007 + WO-DREAM-013.

Composites scene images into a final dream artwork per sleep cycle.

Layer structure (WO-DREAM-007):
  LAYER 01 — Base (NREM/Early REM, high opacity 0.9, Normal)
  LAYER 02 — Memory layer mid-REM (opacity 0.4-0.6, Multiply/Overlay)
  LAYER 03 — Memory layer mid-REM (opacity 0.4-0.6, Multiply/Overlay)
  LAYER 04 — REM apex (opacity 0.2-0.4, Screen/Difference/Color Dodge)
  LAYER 05+ — Additional apex scenes if present
  SPG layer — recurring symbol overlay (semi-transparent, injected into apex)

Blend mode selection driven by emotion vector:
  Wonder/Joy → Screen or lighter (luminous, opening)
  Anxiety/Fear → Multiply or Difference (darkening, disrupting)
  Sadness → Overlay (muted interference)
  Mixed → composite by highest emotion

Final composite saved as `dream_<dream_id>_final.png`.
Metadata JSON sidecar saved alongside.
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Mapping, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFont


_OUTPUT_DIR = Path.home() / "Desktop" / "eLo Generated" / "dreams"


def _output_path(dream_id: str) -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _OUTPUT_DIR / f"dream_{dream_id}_final.png"


def _sidecar_path(dream_id: str) -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _OUTPUT_DIR / f"dream_{dream_id}_metadata.json"


# ── Blend mode selection ───────────────────────────────────────────────────────

def _blend_mode(emotion_vector: Mapping[str, float], layer_index: int) -> str:
    """
    Select blend mode based on dominant emotion and layer position.

    layer_index: 0=base, 1=mid, 2=apex+
    """
    ev = dict(emotion_vector or {})
    wonder   = float(ev.get("wonder",   0.0))
    joy      = float(ev.get("joy",      0.0))
    anxiety  = float(ev.get("anxiety",  0.0))
    fear     = float(ev.get("fear",     0.0))
    sadness  = float(ev.get("sadness",  0.0))

    if layer_index == 0:
        return "normal"

    positive = wonder + joy
    negative = anxiety + fear
    neutral  = sadness

    if positive >= negative and positive >= neutral:
        return "screen" if layer_index >= 2 else "lighter"
    elif negative > positive:
        return "multiply" if layer_index < 2 else "difference"
    else:
        return "overlay"


def _apply_blend(base: Image.Image, layer: Image.Image, mode: str) -> Image.Image:
    """Apply blend mode. Both images must be RGBA, same size."""
    if base.size != layer.size:
        layer = layer.resize(base.size, Image.LANCZOS)
    if mode == "screen":
        return ImageChops.screen(base, layer)
    elif mode == "multiply":
        return ImageChops.multiply(base, layer)
    elif mode == "overlay":
        return ImageChops.overlay(base, layer)
    elif mode == "difference":
        return ImageChops.difference(base, layer)
    elif mode == "soft_light":
        return ImageChops.soft_light(base, layer)
    elif mode == "lighter":
        return ImageChops.lighter(base, layer)
    else:  # normal
        return Image.alpha_composite(base, layer)


# ── Layer opacity ──────────────────────────────────────────────────────────────

def _with_opacity(img: Image.Image, opacity: float) -> Image.Image:
    """Return img with its alpha channel scaled by opacity (0.0-1.0)."""
    r, g, b, a = img.split()
    a = a.point(lambda v: int(v * max(0.0, min(1.0, opacity))))
    return Image.merge("RGBA", (r, g, b, a))


# ── SPG symbol overlay ─────────────────────────────────────────────────────────

def _symbol_overlay(
    size: tuple[int, int],
    symbol: str,
    intensity: float,
) -> Image.Image:
    """
    Generate a semi-transparent text overlay for a recurring SPG symbol.
    Semi-transparent, centred, scales opacity with intensity.
    """
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    alpha = int(30 + 60 * intensity)  # 30-90 / 255 — always subtle
    font_size = max(20, int(h * 0.08))

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()

    text = f"◌ {symbol} ◌"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = (h - th) // 2

    # Teal glow
    draw.text((x, y), text, font=font, fill=(0, 200, 180, alpha))
    return overlay


# ── Main compositor ───────────────────────────────────────────────────────────

def composite(
    scene_paths: Sequence[str | Path],
    dream_id: str,
    *,
    emotion_vector: Mapping[str, float] | None = None,
    recurring_symbol: str = "",
    intensity: float = 0.5,
    dream_record: Mapping | None = None,
) -> dict:
    """
    Composite scene images into a final artwork.

    scene_paths    — paths to scene PNG files (minimum 1, typically 2-4 per cycle).
    dream_id       — unique dream identifier for filename.
    emotion_vector — 7-dimension emotional state (influences blend modes).
    recurring_symbol — SPG symbol to inject as apex overlay.
    intensity      — dream intensity 0.0-1.0 (affects opacities/blend strength).
    dream_record   — full dream journal entry for the metadata sidecar.

    Returns a dict:
        {"ok": True, "final_path": str, "sidecar_path": str, "layers_used": int}
        {"ok": False, "error": str}
    """
    try:
        if not scene_paths:
            return {"ok": False, "error": "no scene images provided"}

        ev = dict(emotion_vector or {})
        images: list[Image.Image] = []
        for p in scene_paths:
            try:
                images.append(Image.open(str(p)).convert("RGBA"))
            except Exception as e:
                return {"ok": False, "error": f"failed to open {p}: {e}"}

        if not images:
            return {"ok": False, "error": "no images loaded"}

        # All layers resized to first image's dimensions
        w, h = images[0].size
        canvas = images[0].copy()

        # Layer structure:
        #   index 0: base — normal, opacity 0.9
        #   index 1,2: mid — Multiply/Overlay, opacity 0.4-0.6
        #   index 3+: apex — Screen/Difference, opacity 0.2-0.4
        opacities = [0.9, 0.55, 0.45, 0.35, 0.25]
        layer_roles = ["base", "mid", "mid", "apex", "apex"]

        # Base layer
        canvas = _with_opacity(canvas, opacities[0])

        for idx, img in enumerate(images[1:], start=1):
            role_idx = min(idx, len(opacities) - 1)
            opacity = opacities[role_idx]
            layer_role_idx = 0 if idx == 0 else (1 if idx <= 2 else 2)
            mode = _blend_mode(ev, layer_role_idx)

            # Emotional weight: significance lifts opacity slightly
            em_weight = float(ev.get("joy", 0) + ev.get("wonder", 0)) / 2.0
            opacity = min(0.9, opacity + 0.1 * em_weight * intensity)

            layer = img.resize((w, h), Image.LANCZOS)
            layer = _with_opacity(layer, opacity)

            canvas = canvas.convert("RGBA")
            canvas = _apply_blend(canvas, layer, mode)

        # SPG recurring symbol overlay on apex
        if recurring_symbol and intensity > 0.3:
            sym_overlay = _symbol_overlay((w, h), recurring_symbol, intensity)
            canvas = Image.alpha_composite(canvas.convert("RGBA"), sym_overlay)

        # Save final artwork
        out_path = _output_path(dream_id)
        canvas.convert("RGB").save(str(out_path), "PNG")

        # Metadata sidecar
        metadata = {
            "dream_id":          dream_id,
            "timestamp":         time.strftime("%Y-%m-%dT%H:%M:%S"),
            "layers_used":       len(images),
            "scene_paths":       [str(p) for p in scene_paths],
            "final_path":        str(out_path),
            "emotion_vector":    ev,
            "intensity":         intensity,
            "recurring_symbol":  recurring_symbol,
            "output_type":       "DREAM",
        }
        if dream_record:
            metadata["dream_record"] = dict(dream_record)

        sidecar_path = _sidecar_path(dream_id)
        with open(str(sidecar_path), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return {
            "ok":          True,
            "final_path":  str(out_path),
            "sidecar_path": str(sidecar_path),
            "layers_used": len(images),
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}
