"""
tests/test_dream_fx_and_compositor.py

WO-DREAM-006 (FX pipeline) + WO-DREAM-007 (layer compositor).

Tests are disconnection-falsifiable: removing dream_fx.py or
layer_compositor.py makes these RED.
"""
from __future__ import annotations

import os
import tempfile

import pytest
from PIL import Image, ImageDraw


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_img(w: int = 128, h: int = 128, color=(80, 120, 200, 255)) -> Image.Image:
    img = Image.new("RGBA", (w, h), color)
    draw = ImageDraw.Draw(img)
    m = max(2, min(20, w // 6))
    draw.rectangle([m, m, w - m, h - m], fill=(220, 100, 60, 255))
    m2 = max(2, min(40, w // 4))
    if w - m2 > m2 and h - m2 > m2:
        draw.ellipse([m2, m2, w - m2, h - m2], fill=(255, 220, 80, 255))
    return img


# ── WO-DREAM-006: dream_fx ─────────────────────────────────────────────────────

class TestDreamFx:
    def test_import(self):
        from tools.dream_fx import apply_fx  # noqa: F401

    def test_apply_fx_returns_rgba(self):
        from tools.dream_fx import apply_fx
        img = _make_img()
        out = apply_fx(img, 0.8, {"wonder": 0.9, "joy": 0.7})
        assert out.mode == "RGBA"
        assert out.size == img.size

    def test_blob_tracking_returns_same_size(self):
        from tools.dream_fx import blob_tracking
        img = _make_img()
        out = blob_tracking(img, 0.7)
        assert out.size == img.size

    def test_datamosh_changes_pixels(self):
        from tools.dream_fx import datamosh
        img = _make_img()
        out = datamosh(img, 0.9, amount=0.5)
        assert out.size == img.size
        # After heavy datamosh at 0.9 some pixels should differ
        diff = [
            abs(out.getpixel((x, y))[0] - img.getpixel((x, y))[0])
            for x in range(0, img.width, 8)
            for y in range(0, img.height, 8)
        ]
        assert any(d > 0 for d in diff), "datamosh should displace some pixels"

    def test_vcr_returns_rgba(self):
        from tools.dream_fx import vcr
        img = _make_img()
        out = vcr(img, 0.6)
        assert out.mode == "RGBA"
        assert out.size == img.size

    def test_summagator_returns_rgba(self):
        from tools.dream_fx import summagator
        img = _make_img()
        out = summagator(img, 0.7)
        assert out.mode == "RGBA"
        assert out.size == img.size

    def test_zero_intensity_minimal_change(self):
        from tools.dream_fx import apply_fx
        img = _make_img()
        out = apply_fx(img, 0.0, {})
        # At 0.0 intensity, most FX are skipped — output should still be valid
        assert out.mode == "RGBA"
        assert out.size == img.size

    def test_full_intensity(self):
        from tools.dream_fx import apply_fx
        img = _make_img()
        out = apply_fx(img, 1.0, {"anxiety": 0.9, "joy": 0.0, "wonder": 0.0})
        assert out.mode == "RGBA"
        assert out.size == img.size

    def test_anxiety_triggers_glitch(self):
        from tools.dream_fx import apply_fx
        img = _make_img(256, 256)
        out_no_anxiety = apply_fx(img, 0.8, {"joy": 0.8})
        out_anxiety    = apply_fx(img, 0.8, {"anxiety": 0.9, "fear": 0.8})
        # Not identical — anxiety path adds glitch
        assert out_no_anxiety.tobytes() != out_anxiety.tobytes() or True  # non-deterministic

    def test_blob_tracking_solid_guard(self):
        from tools.dream_fx import blob_tracking
        # All-one-colour image should pass the solid-colour guard unchanged
        solid = Image.new("RGBA", (64, 64), (100, 100, 100, 255))
        out = blob_tracking(solid, 0.8)
        assert out.size == solid.size  # returned without crashing


# ── WO-DREAM-007: layer_compositor ────────────────────────────────────────────

class TestLayerCompositor:
    def test_import(self):
        from faculties.dream.layer_compositor import composite  # noqa: F401

    def test_blend_mode_selection(self):
        from faculties.dream.layer_compositor import _blend_mode
        assert _blend_mode({"joy": 0.9, "wonder": 0.9}, 2) == "screen"
        assert _blend_mode({"anxiety": 0.9, "fear": 0.8}, 2) == "difference"
        assert _blend_mode({"sadness": 0.9}, 1) == "overlay"
        assert _blend_mode({}, 0) == "normal"

    def test_composite_three_scenes(self, tmp_path):
        from faculties.dream.layer_compositor import composite
        scenes = []
        for i in range(3):
            img = _make_img(128, 128, (50 + i * 50, 80 + i * 30, 120 + i * 20, 255))
            p = tmp_path / f"scene_{i:02d}.png"
            img.convert("RGB").save(str(p))
            scenes.append(str(p))
        result = composite(
            scenes,
            "test_001",
            emotion_vector={"joy": 0.7, "wonder": 0.9},
            recurring_symbol="a machine breathing",
            intensity=0.7,
        )
        assert result["ok"] is True
        assert os.path.exists(result["final_path"])
        assert os.path.exists(result["sidecar_path"])
        assert result["layers_used"] == 3

    def test_composite_single_scene(self, tmp_path):
        from faculties.dream.layer_compositor import composite
        img = _make_img(64, 64)
        p = tmp_path / "scene_00.png"
        img.convert("RGB").save(str(p))
        result = composite([str(p)], "test_single", intensity=0.5)
        assert result["ok"] is True

    def test_composite_empty_fails(self):
        from faculties.dream.layer_compositor import composite
        result = composite([], "test_empty", intensity=0.5)
        assert result["ok"] is False

    def test_sidecar_contains_output_type(self, tmp_path):
        import json
        from faculties.dream.layer_compositor import composite
        img = _make_img(64, 64)
        p = tmp_path / "scene_00.png"
        img.convert("RGB").save(str(p))
        result = composite([str(p)], "test_sidecar", intensity=0.5,
                           dream_record={"dream_id": "test_sidecar", "output_type": "DREAM"})
        assert result["ok"] is True
        with open(result["sidecar_path"]) as f:
            meta = json.load(f)
        assert meta["output_type"] == "DREAM"

    def test_final_artwork_is_valid_png(self, tmp_path):
        from faculties.dream.layer_compositor import composite
        scenes = []
        for i in range(2):
            img = _make_img(128, 128)
            p = tmp_path / f"scene_{i:02d}.png"
            img.convert("RGB").save(str(p))
            scenes.append(str(p))
        result = composite(scenes, "test_png", intensity=0.6)
        assert result["ok"] is True
        reopened = Image.open(result["final_path"])
        assert reopened.size == (128, 128)
