"""
tests/test_dream_fx.py — WO-DREAM-ENGINE-001 PHASE 5c.

CompositionDesigner FX pipeline, ported from the live compositor at
~/Desktop/Output/DISENELO-CompositionDesigner/transparent_video_compositor.html

No network, no paid API. Everything runs on synthetic images.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from tools import dream_fx as fx


def _scene(w=320, h=180) -> Image.Image:
    """Dark gradient with two bright shapes — something blob detection can find."""
    a = np.zeros((h, w, 3), np.uint8)
    a[:, :, 2] = np.linspace(20, 90, w).astype(np.uint8)
    a[40:90, 60:140] = (240, 230, 210)
    a[110:150, 200:280] = (250, 245, 235)
    return Image.fromarray(a)


def _flat(v=128, w=320, h=180) -> Image.Image:
    return Image.fromarray(np.full((h, w, 3), v, np.uint8))


def _differs(a: Image.Image, b: Image.Image) -> bool:
    return not np.array_equal(np.asarray(a), np.asarray(b))


# ── Blob tracking — ported constants and behaviour ────────────────────────────

def test_detection_buffer_matches_the_compositor():
    assert (fx.BLOB_DETECT_W, fx.BLOB_DETECT_H) == (160, 90)
    assert fx.BLOB_UNIFORM_RANGE == 30
    assert fx.BLOB_AUTO_THRESH == 0.7
    assert fx.LUMA == (0.299, 0.587, 0.114)


def test_solid_colour_guard_refuses_to_hallucinate_blobs():
    """The compositor's own guard: range < 30 -> no blobs."""
    assert fx.detect_blobs(_flat(128)) == []
    assert fx.detect_blobs(_flat(0)) == []
    assert fx.detect_blobs(_flat(255)) == []


def test_blobs_found_on_a_real_scene():
    blobs = fx.detect_blobs(_scene())
    assert len(blobs) >= 2
    for b in blobs:
        x0, y0, x1, y1 = b["box"]
        assert x1 > x0 and y1 > y0
        assert b["area"] > 0


def test_blobs_are_ranked_largest_first():
    areas = [b["area"] for b in fx.detect_blobs(_scene())]
    assert areas == sorted(areas, reverse=True)


def test_blob_overlay_changes_the_image():
    import random
    src = _scene()
    out = fx.fx_blob_tracking(src, 0.8, random.Random(1))
    assert _differs(src, out)
    assert out.size == src.size


# ── Emotion drives selection, not chance ──────────────────────────────────────

def test_selection_is_deterministic_not_random():
    for _ in range(5):
        assert fx.select_fx("fear", 0.9) == fx.select_fx("fear", 0.9)


def test_different_emotions_select_different_effects():
    assert fx.select_fx("fear", 0.9) != fx.select_fx("joy", 0.9)


def test_every_emotion_maps_to_a_table_row():
    from faculties.dream.dream_input import EMOTION_DIMENSIONS
    for dim in EMOTION_DIMENSIONS:
        assert fx.row_for_emotion(dim) in fx.EMOTION_FX
    for extra in ("achievement", "nostalgia"):
        assert fx.row_for_emotion(extra) in fx.EMOTION_FX


def test_table_rows_match_the_wo():
    assert set(fx.EMOTION_FX) == {
        "anxiety_fear", "joy_wonder", "sadness_grief",
        "achievement", "nostalgia", "curiosity",
    }


# ── Intensity ramp ────────────────────────────────────────────────────────────

def test_early_rem_gets_a_single_subtle_effect_not_none():
    """WO: 'Early REM scenes: subtle (single FX, low strength)'."""
    selected = fx.select_fx("wonder", 0.1)
    assert len(selected) == 1


def test_late_rem_gets_more_than_early_rem():
    early = fx.apply_fx(_scene(), emotion="wonder", intensity=0.1, seed=1)
    late = fx.apply_fx(_scene(), emotion="wonder", intensity=0.9, seed=1)
    assert len(late.applied) > len(early.applied)


def test_maximum_surreal_combines_everything():
    selected = fx.select_fx("joy", 0.95)
    for name in fx.MAX_SURREAL_FX:
        assert name in selected
    assert fx.MAX_SURREAL_INTENSITY == 0.85


def test_base_pipeline_runs_in_the_wo_order():
    """blob tracking -> datamosh -> VCR -> summagator."""
    assert fx.BASE_PIPELINE == ("blob_tracking", "datamosh", "vcr", "summagator")
    result = fx.apply_fx(_scene(), emotion="wonder", intensity=0.7, seed=2)
    order = [n for n in result.applied if n in fx.BASE_PIPELINE]
    assert order == list(fx.BASE_PIPELINE)


# ── Base texture is always present ────────────────────────────────────────────

@pytest.mark.parametrize("intensity", [0.0, 0.05, 0.3, 0.6, 1.0])
def test_vignette_and_grain_always_present(intensity):
    """WO: 'fxVignette + fxGrain — always present at low levels as base texture'."""
    result = fx.apply_fx(_scene(), emotion="wonder", intensity=intensity, seed=3)
    assert "vignette" in result.applied
    assert "grain" in result.applied


def test_base_texture_runs_last():
    result = fx.apply_fx(_scene(), emotion="fear", intensity=0.9, seed=3)
    assert result.applied[-1] in fx.BASE_TEXTURE


def test_base_texture_is_low_level_regardless_of_intensity():
    assert 0.0 < fx.BASE_TEXTURE_STRENGTH <= 0.25


# ── Honesty about what is not implemented ─────────────────────────────────────

def test_unimplemented_effects_are_reported_not_silently_substituted():
    result = fx.apply_fx(_scene(), emotion="fear", intensity=0.95, seed=4)
    assert result.skipped, "nothing reported as skipped"
    for name in result.skipped:
        assert name not in result.applied
        assert name in fx.UNIMPLEMENTED_FX or name in fx._FX_IMPL


def test_no_unimplemented_effect_silently_maps_to_another():
    for name in fx.UNIMPLEMENTED_FX:
        assert name not in fx._FX_IMPL


# ── Individual effects ────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", ["datamosh", "vcr", "summagator", "invert",
                                  "posterize", "bloom", "edge_detect",
                                  "vignette", "grain"])
def test_each_effect_changes_the_image_and_keeps_its_size(name):
    import random
    src = _scene()
    out = fx._FX_IMPL[name](src, 0.8, random.Random(5))
    assert out.size == src.size
    assert out.mode == "RGB"
    assert _differs(src, out)


def test_datamosh_displaces_blocks_of_the_wo_size():
    assert fx.DATAMOSH_BLOCK == 16
    assert fx.DATAMOSH_FRACTION == (0.30, 0.40)
    assert fx.DATAMOSH_OFFSET == (8, 24)


def test_vcr_constants_match_the_wo():
    assert fx.SCANLINE_ALPHA == (0.08, 0.12)
    assert fx.VHS_BANDS == (3, 6)
    assert fx.VHS_BAND_OFFSET == (4, 12)
    assert fx.CHROMA_SHIFT == 2
    assert fx.GRAIN_SIGMA == (4.0, 8.0)


def test_summagator_constants_match_the_wo():
    assert fx.SUMMAGATOR_SCALES == (1.00, 0.95, 0.90)
    assert fx.SUMMAGATOR_OPACITIES == (1.00, 0.40, 0.20)
    assert fx.SLITSCAN_AMPLITUDE == (8, 16)


# ── Reproducibility ───────────────────────────────────────────────────────────

def test_same_seed_reproduces_the_same_image():
    a = fx.apply_fx(_scene(), emotion="fear", intensity=0.9, seed=42).image
    b = fx.apply_fx(_scene(), emotion="fear", intensity=0.9, seed=42).image
    assert np.array_equal(np.asarray(a), np.asarray(b))


def test_different_seeds_differ():
    a = fx.apply_fx(_scene(), emotion="fear", intensity=0.9, seed=1).image
    b = fx.apply_fx(_scene(), emotion="fear", intensity=0.9, seed=2).image
    assert not np.array_equal(np.asarray(a), np.asarray(b))


# ── Robustness ────────────────────────────────────────────────────────────────

def test_flat_image_survives_the_whole_pipeline():
    result = fx.apply_fx(_flat(), emotion="wonder", intensity=1.0, seed=6)
    assert result.image.size == (320, 180)


def test_tiny_image_does_not_crash():
    tiny = Image.fromarray(np.zeros((8, 8, 3), np.uint8))
    assert fx.apply_fx(tiny, emotion="joy", intensity=1.0, seed=7).image.size == (8, 8)


def test_non_rgb_input_is_converted():
    grey = Image.fromarray(np.full((60, 60), 90, np.uint8), mode="L")
    assert fx.apply_fx(grey, emotion="joy", intensity=0.6, seed=8).image.mode == "RGB"


def test_apply_to_file_round_trip(tmp_path):
    src = tmp_path / "in.png"
    dst = tmp_path / "out.png"
    _scene().save(src)
    result = fx.apply_to_file(str(src), str(dst), emotion="wonder",
                              intensity=0.8, seed=9)
    assert dst.exists()
    assert result.applied
    assert _differs(Image.open(src).convert("RGB"), Image.open(dst).convert("RGB"))
