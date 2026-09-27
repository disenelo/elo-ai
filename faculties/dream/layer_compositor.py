"""
faculties/dream/layer_compositor.py — Visual Layering Engine.

WO-DREAM-ENGINE-001 PHASE 6.

Composites the scene images of one dream into a single artwork.

    Layer        Source      Opacity            Blend
    Base         Scene 01    high   (0.9)       Normal — structural foundation
    Memory       Scene 02-03 medium (0.4-0.6)   Multiply or Overlay — interference
    REM apex     Scene 04+   low    (0.2-0.4)   Screen, Difference, Color Dodge

Opacity is driven by emotional weight: a high-significance fragment occupies
more visual space, a weak one appears as a faint trace. Blend mode is chosen
by the emotion vector, never at random:

    wonder / joy      -> screen or color_dodge   (luminous, opening)
    anxiety / fear    -> multiply or difference  (darkening, disrupting)
    sadness / grief   -> overlay                 (muted interference)

A motif that symbol_history reports recurring across >= 3 dreams is injected
into the apex layer as a semi-transparent overlay. It builds over time — it
is observed, never hardcoded. If the lexicon names a recurring symbol but no
image of it exists, that is recorded in the metadata as pending rather than
fabricated.

Output: `dream_<dream_id>_final.png` plus a JSON sidecar carrying the full
provenance — every layer, its source, opacity, blend mode and why.
"The artwork is the artefact of eLo's internal process."

Requires PIL and numpy. No network, no paid API, no server.py.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field as _field
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image

# ── Layer roles (WO PHASE 6 table) ────────────────────────────────────────────
ROLE_BASE = "base"
ROLE_MEMORY = "memory"
ROLE_APEX = "apex"

OPACITY_BASE = 0.90
OPACITY_MEMORY = (0.40, 0.60)
OPACITY_APEX = (0.20, 0.40)

# ── Blend modes ───────────────────────────────────────────────────────────────
BLEND_NORMAL = "normal"
BLEND_MULTIPLY = "multiply"
BLEND_OVERLAY = "overlay"
BLEND_SCREEN = "screen"
BLEND_DIFFERENCE = "difference"
BLEND_COLOR_DODGE = "color_dodge"

# Emotion -> the blend family that emotion composites in.
# Two options per row, per the WO; the apex takes the second (more extreme)
# so a dream opens or disrupts harder at its peak than in its middle.
EMOTION_BLEND: dict[str, tuple[str, str]] = {
    "joy_wonder":    (BLEND_SCREEN,   BLEND_COLOR_DODGE),
    "anxiety_fear":  (BLEND_MULTIPLY, BLEND_DIFFERENCE),
    "sadness_grief": (BLEND_OVERLAY,  BLEND_OVERLAY),
    "achievement":   (BLEND_SCREEN,   BLEND_COLOR_DODGE),
    "nostalgia":     (BLEND_OVERLAY,  BLEND_MULTIPLY),
    "curiosity":     (BLEND_OVERLAY,  BLEND_SCREEN),
}

# Same row mapping the prompt builder and dream_fx use, so lighting, FX and
# blend all describe one dream instead of three.
_EMOTION_TO_ROW = {
    "joy": "joy_wonder", "wonder": "joy_wonder",
    "fear": "anxiety_fear", "anxiety": "anxiety_fear", "anger": "anxiety_fear",
    "sadness": "sadness_grief", "grief": "sadness_grief",
    "curiosity": "curiosity", "achievement": "achievement", "nostalgia": "nostalgia",
}

# The seven named layers of the physical artwork output.
ARTWORK_LAYERS: tuple[str, ...] = (
    "memory", "association", "emotion", "transformation",
    "rem_distortion", "spg_recurrence", "final_composite",
)

MOTIF_OPACITY = 0.22


def row_for_emotion(emotion: str) -> str:
    return _EMOTION_TO_ROW.get((emotion or "").strip().lower(), "joy_wonder")


def blend_for(emotion: str, role: str) -> str:
    """Blend mode for a layer role, chosen by emotion. Never random."""
    if role == ROLE_BASE:
        return BLEND_NORMAL                      # structural foundation
    mid, extreme = EMOTION_BLEND[row_for_emotion(emotion)]
    return extreme if role == ROLE_APEX else mid


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def opacity_for(role: str, weight: float) -> float:
    """
    Opacity from emotional weight. High-significance fragments occupy more
    visual space; weak ones are faint traces.
    """
    w = max(0.0, min(1.0, float(weight)))
    if role == ROLE_BASE:
        return OPACITY_BASE
    lo, hi = OPACITY_MEMORY if role == ROLE_MEMORY else OPACITY_APEX
    return round(_lerp(lo, hi, w), 3)


def role_for_index(index: int, total: int) -> str:
    """
    Scene 01 is the base. Scenes 02-03 are memory interference. Scene 04+ is
    the apex. With fewer scenes the last one still carries the apex, so a
    short dream is not left without a peak.
    """
    if index == 0:
        return ROLE_BASE
    if total <= 2:
        return ROLE_APEX
    return ROLE_APEX if index >= 3 or index == total - 1 else ROLE_MEMORY


# ── Blend maths ───────────────────────────────────────────────────────────────

def _blend_arrays(base: np.ndarray, top: np.ndarray, mode: str) -> np.ndarray:
    """All operate on float arrays in 0..255."""
    b = base / 255.0
    t = top / 255.0

    if mode == BLEND_NORMAL:
        out = t
    elif mode == BLEND_MULTIPLY:
        out = b * t
    elif mode == BLEND_SCREEN:
        out = 1.0 - (1.0 - b) * (1.0 - t)
    elif mode == BLEND_OVERLAY:
        out = np.where(b <= 0.5, 2.0 * b * t, 1.0 - 2.0 * (1.0 - b) * (1.0 - t))
    elif mode == BLEND_DIFFERENCE:
        out = np.abs(b - t)
    elif mode == BLEND_COLOR_DODGE:
        out = np.where(t >= 1.0, 1.0, np.minimum(1.0, b / np.maximum(1e-6, 1.0 - t)))
    else:
        raise ValueError(f"unknown blend mode: {mode!r}")

    return np.clip(out * 255.0, 0, 255)


def blend(base: Image.Image, top: Image.Image, mode: str, opacity: float) -> Image.Image:
    """Composite `top` onto `base` at `opacity` using `mode`."""
    if top.size != base.size:
        top = top.resize(base.size, Image.BILINEAR)
    b = np.asarray(base.convert("RGB"), dtype=np.float32)
    t = np.asarray(top.convert("RGB"), dtype=np.float32)
    blended = _blend_arrays(b, t, mode)
    a = max(0.0, min(1.0, float(opacity)))
    return Image.fromarray(np.clip(b * (1.0 - a) + blended * a, 0, 255).astype(np.uint8))


# ── Layer plan ────────────────────────────────────────────────────────────────

@dataclass
class LayerSpec:
    """One layer, with the provenance the WO requires."""
    index: int
    source: str
    role: str
    opacity: float
    blend_mode: str
    weight: float
    stage: str = ""
    intensity: float = 0.0

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "source": self.source,
            "role": self.role,
            "opacity": self.opacity,
            "blend_mode": self.blend_mode,
            "weight": self.weight,
            "stage": self.stage,
            "intensity": self.intensity,
        }


def build_layer_plan(
    scenes: Sequence[dict],
    emotion: str,
    *,
    significance: float = 0.5,
) -> list[LayerSpec]:
    """
    Decide each scene's role, opacity and blend mode before compositing.

    scenes — dicts carrying at least `path`; `stage` and `intensity` are used
             for weighting and provenance when present.
    """
    total = len(scenes)
    plan: list[LayerSpec] = []
    for i, scene in enumerate(scenes):
        role = role_for_index(i, total)
        intensity = float(scene.get("intensity", 0.0) or 0.0)
        # Emotional weight: the scene's own intensity, lifted by how
        # significant the dream as a whole was.
        weight = max(0.0, min(1.0, 0.7 * intensity + 0.3 * float(significance)))
        plan.append(LayerSpec(
            index=i,
            source=str(scene.get("path", "")),
            role=role,
            opacity=opacity_for(role, weight),
            blend_mode=blend_for(emotion, role),
            weight=round(weight, 3),
            stage=str(scene.get("stage", "")),
            intensity=intensity,
        ))
    return plan


# ── Composite ─────────────────────────────────────────────────────────────────

@dataclass
class CompositeResult:
    image: Image.Image | None
    layers: list[LayerSpec] = _field(default_factory=list)
    motif: dict = _field(default_factory=dict)
    final_path: str = ""
    sidecar_path: str = ""
    metadata: dict = _field(default_factory=dict)


def composite_dream(
    scenes: Sequence[dict],
    *,
    dream_id: str,
    emotion: str,
    significance: float = 0.5,
    recurring_symbol: str = "",
    motif_image: str | None = None,
    out_dir: str | Path | None = None,
    dream_record: dict | None = None,
) -> CompositeResult:
    """
    Composite one dream's scenes into a single artwork.

    recurring_symbol — a motif symbol_history reports recurring across >= 3
                       dreams. Observed, never hardcoded.
    motif_image      — an image of that motif. When the lexicon names a
                       recurring symbol but no image exists, the metadata
                       records it as pending rather than inventing one.
    out_dir          — where to write. None means compose in memory only.

    Returns the composite plus full per-layer provenance.
    """
    usable = [s for s in scenes if s.get("path") and Path(s["path"]).exists()]
    if not usable:
        return CompositeResult(
            image=None,
            motif={"symbol": recurring_symbol, "overlaid": False,
                   "reason": "no scene images to composite"},
            metadata={"dream_id": dream_id, "layers": [], "scene_count": 0},
        )

    plan = build_layer_plan(usable, emotion, significance=significance)

    with Image.open(usable[0]["path"]) as first:
        canvas = first.convert("RGB").copy()

    for spec in plan[1:]:
        try:
            with Image.open(spec.source) as layer:
                canvas = blend(canvas, layer.convert("RGB"), spec.blend_mode, spec.opacity)
        except Exception:
            continue

    # SPG recurrence — into the apex layer, semi-transparent.
    motif: dict = {"symbol": recurring_symbol, "overlaid": False}
    if recurring_symbol:
        if motif_image and Path(motif_image).exists():
            try:
                with Image.open(motif_image) as m:
                    canvas = blend(canvas, m.convert("RGB"),
                                   blend_for(emotion, ROLE_APEX), MOTIF_OPACITY)
                motif.update({"overlaid": True, "image": str(motif_image),
                              "opacity": MOTIF_OPACITY})
            except Exception as e:
                motif.update({"overlaid": False, "reason": f"motif image unreadable: {e}"})
        else:
            # Observed but not yet drawable. Recorded, not fabricated.
            motif.update({"overlaid": False,
                          "reason": "no motif image available for this symbol"})

    metadata = {
        "dream_id": dream_id,
        "emotion": emotion,
        "emotion_row": row_for_emotion(emotion),
        "significance": significance,
        "scene_count": len(usable),
        "artwork_layers": list(ARTWORK_LAYERS),
        "layers": [s.as_dict() for s in plan],
        "motif": motif,
        "output_type": "DREAM",
    }
    if dream_record is not None:
        metadata["dream_record"] = dream_record

    final_path = sidecar_path = ""
    if out_dir:
        target = Path(out_dir)
        target.mkdir(parents=True, exist_ok=True)
        final = target / f"dream_{dream_id}_final.png"
        sidecar = target / f"dream_{dream_id}_final.json"
        canvas.save(final)
        sidecar.write_text(json.dumps(metadata, indent=2, ensure_ascii=False),
                           encoding="utf-8")
        final_path, sidecar_path = str(final), str(sidecar)
        metadata["final_artwork"] = final_path

    return CompositeResult(
        image=canvas,
        layers=plan,
        motif=motif,
        final_path=final_path,
        sidecar_path=sidecar_path,
        metadata=metadata,
    )
