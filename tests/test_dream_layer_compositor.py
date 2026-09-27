"""
tests/test_dream_layer_compositor.py — WO-DREAM-ENGINE-001 PHASE 6.

Visual layering engine. Blend mode by emotion, opacity by emotional weight,
SPG motif into the apex, provenance for every layer.
"""
from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image

from faculties.dream import layer_compositor as lc


@pytest.fixture
def scenes(tmp_path):
    out = []
    spec = [("grounded", 0.3), ("transformation", 0.55),
            ("condensation", 0.8), ("abstraction", 1.0)]
    for i, (stage, intensity) in enumerate(spec):
        a = np.zeros((120, 160, 3), np.uint8)
        a[:, :, i % 3] = 40 + i * 50
        a[20 + i * 10:70 + i * 10, 20 + i * 20:90 + i * 20] = (220, 200, 180)
        p = tmp_path / f"scene_{i + 1}.png"
        Image.fromarray(a).save(p)
        out.append({"path": str(p), "stage": stage, "intensity": intensity})
    return out


# ── Layer structure (WO PHASE 6 table) ────────────────────────────────────────

def test_scene_one_is_the_base_and_last_is_the_apex(scenes):
    plan = lc.build_layer_plan(scenes, "wonder")
    assert plan[0].role == lc.ROLE_BASE
    assert plan[-1].role == lc.ROLE_APEX
    assert [p.role for p in plan[1:3]] == [lc.ROLE_MEMORY, lc.ROLE_MEMORY]


def test_base_is_normal_at_high_opacity(scenes):
    base = lc.build_layer_plan(scenes, "wonder")[0]
    assert base.blend_mode == lc.BLEND_NORMAL
    assert base.opacity == lc.OPACITY_BASE == 0.90


def test_opacity_bands_match_the_wo(scenes):
    for emotion in ("wonder", "fear", "sadness"):
        for spec in lc.build_layer_plan(scenes, emotion):
            if spec.role == lc.ROLE_MEMORY:
                assert lc.OPACITY_MEMORY[0] <= spec.opacity <= lc.OPACITY_MEMORY[1]
            elif spec.role == lc.ROLE_APEX:
                assert lc.OPACITY_APEX[0] <= spec.opacity <= lc.OPACITY_APEX[1]


def test_a_short_dream_still_gets_an_apex(tmp_path):
    a = tmp_path / "one.png"
    Image.fromarray(np.zeros((40, 40, 3), np.uint8)).save(a)
    two = [{"path": str(a), "intensity": 0.2}, {"path": str(a), "intensity": 0.9}]
    roles = [s.role for s in lc.build_layer_plan(two, "wonder")]
    assert roles == [lc.ROLE_BASE, lc.ROLE_APEX]


# ── Opacity is driven by emotional weight ─────────────────────────────────────

def test_high_significance_fragments_occupy_more_visual_space():
    assert lc.opacity_for(lc.ROLE_MEMORY, 1.0) > lc.opacity_for(lc.ROLE_MEMORY, 0.0)
    assert lc.opacity_for(lc.ROLE_APEX, 1.0) > lc.opacity_for(lc.ROLE_APEX, 0.0)


def test_weak_fragments_are_faint_traces():
    assert lc.opacity_for(lc.ROLE_APEX, 0.0) == lc.OPACITY_APEX[0] == 0.20


def test_dream_significance_lifts_layer_weight(scenes):
    low = lc.build_layer_plan(scenes, "wonder", significance=0.0)
    high = lc.build_layer_plan(scenes, "wonder", significance=1.0)
    assert high[-1].weight > low[-1].weight


# ── Blend mode is driven by the emotion vector, never random ──────────────────

def test_wonder_and_joy_open_the_image():
    assert lc.blend_for("wonder", lc.ROLE_MEMORY) == lc.BLEND_SCREEN
    assert lc.blend_for("joy", lc.ROLE_APEX) == lc.BLEND_COLOR_DODGE


def test_anxiety_and_fear_darken_and_disrupt():
    assert lc.blend_for("fear", lc.ROLE_MEMORY) == lc.BLEND_MULTIPLY
    assert lc.blend_for("anxiety", lc.ROLE_APEX) == lc.BLEND_DIFFERENCE


def test_sadness_is_muted_interference():
    assert lc.blend_for("sadness", lc.ROLE_MEMORY) == lc.BLEND_OVERLAY
    assert lc.blend_for("grief", lc.ROLE_APEX) == lc.BLEND_OVERLAY


def test_selection_is_deterministic():
    for _ in range(5):
        assert lc.blend_for("fear", lc.ROLE_APEX) == lc.BLEND_DIFFERENCE


def test_every_emotion_maps_to_a_blend_row():
    from faculties.dream.dream_input import EMOTION_DIMENSIONS
    for dim in EMOTION_DIMENSIONS:
        assert lc.row_for_emotion(dim) in lc.EMOTION_BLEND


def test_apex_is_at_least_as_extreme_as_the_middle():
    for row, (mid, extreme) in lc.EMOTION_BLEND.items():
        assert mid in lc.EMOTION_BLEND[row]
        assert extreme in lc.EMOTION_BLEND[row]


# ── Blend maths ───────────────────────────────────────────────────────────────

def _solid(v, size=(8, 8)):
    return Image.fromarray(np.full((size[1], size[0], 3), v, np.uint8))


def test_multiply_darkens():
    out = lc.blend(_solid(200), _solid(128), lc.BLEND_MULTIPLY, 1.0)
    assert np.asarray(out).mean() < 200


def test_screen_lightens():
    out = lc.blend(_solid(100), _solid(128), lc.BLEND_SCREEN, 1.0)
    assert np.asarray(out).mean() > 100


def test_difference_of_identical_images_is_black():
    out = lc.blend(_solid(180), _solid(180), lc.BLEND_DIFFERENCE, 1.0)
    assert np.asarray(out).max() <= 1


def test_zero_opacity_is_a_no_op():
    base = _solid(120)
    out = lc.blend(base, _solid(255), lc.BLEND_SCREEN, 0.0)
    assert np.array_equal(np.asarray(base), np.asarray(out))


def test_unknown_blend_mode_raises():
    with pytest.raises(ValueError):
        lc.blend(_solid(10), _solid(20), "chartreuse", 1.0)


def test_mismatched_sizes_are_resized():
    out = lc.blend(_solid(100, (32, 32)), _solid(200, (8, 8)), lc.BLEND_NORMAL, 1.0)
    assert out.size == (32, 32)


# ── SPG motif ─────────────────────────────────────────────────────────────────

def test_motif_is_overlaid_when_an_image_exists(scenes, tmp_path):
    motif = tmp_path / "motif.png"
    Image.fromarray(np.full((120, 160, 3), 200, np.uint8)).save(motif)
    r = lc.composite_dream(scenes, dream_id="d1", emotion="wonder",
                           recurring_symbol="a machine breathing",
                           motif_image=str(motif))
    assert r.motif["overlaid"] is True
    assert r.motif["opacity"] == lc.MOTIF_OPACITY


def test_motif_is_never_fabricated_when_no_image_exists(scenes):
    """Observed but not drawable is recorded as pending, not invented."""
    r = lc.composite_dream(scenes, dream_id="d1", emotion="wonder",
                           recurring_symbol="a machine breathing")
    assert r.motif["overlaid"] is False
    assert "no motif image available" in r.motif["reason"]
    assert r.motif["symbol"] == "a machine breathing"


def test_no_recurring_symbol_means_no_motif(scenes):
    r = lc.composite_dream(scenes, dream_id="d1", emotion="wonder")
    assert r.motif["overlaid"] is False


def test_unreadable_motif_is_reported_not_swallowed(scenes, tmp_path):
    broken = tmp_path / "broken.png"
    broken.write_text("not an image", encoding="utf-8")
    r = lc.composite_dream(scenes, dream_id="d1", emotion="wonder",
                           recurring_symbol="x", motif_image=str(broken))
    assert r.motif["overlaid"] is False
    assert "unreadable" in r.motif["reason"]


# ── Output + provenance ───────────────────────────────────────────────────────

def test_final_artwork_and_sidecar_are_written(scenes, tmp_path):
    out = tmp_path / "art"
    r = lc.composite_dream(scenes, dream_id="a3f7c2b1", emotion="wonder",
                           out_dir=out)
    assert r.final_path.endswith("dream_a3f7c2b1_final.png")
    assert r.sidecar_path.endswith("dream_a3f7c2b1_final.json")
    assert (out / "dream_a3f7c2b1_final.png").exists()

    meta = json.loads((out / "dream_a3f7c2b1_final.json").read_text())
    assert meta["dream_id"] == "a3f7c2b1"
    assert meta["output_type"] == "DREAM"
    assert len(meta["layers"]) == len(scenes)


def test_every_layer_carries_provenance(scenes):
    for layer in lc.composite_dream(scenes, dream_id="d1", emotion="fear").metadata["layers"]:
        for key in ("index", "source", "role", "opacity", "blend_mode", "weight"):
            assert key in layer
        assert layer["source"], "layer has no source path"


def test_sidecar_can_carry_the_full_dream_record(scenes, tmp_path):
    record = {"dream_id": "d1", "insight": "the pattern was already there"}
    r = lc.composite_dream(scenes, dream_id="d1", emotion="wonder",
                           out_dir=tmp_path, dream_record=record)
    meta = json.loads(open(r.sidecar_path).read())
    assert meta["dream_record"]["insight"] == "the pattern was already there"


def test_seven_artwork_layers_are_named(scenes):
    meta = lc.composite_dream(scenes, dream_id="d1", emotion="wonder").metadata
    assert len(lc.ARTWORK_LAYERS) == 7
    assert meta["artwork_layers"][-1] == "final_composite"


def test_composite_actually_differs_from_the_base_scene(scenes):
    r = lc.composite_dream(scenes, dream_id="d1", emotion="fear")
    with Image.open(scenes[0]["path"]) as base:
        assert not np.array_equal(np.asarray(base.convert("RGB")), np.asarray(r.image))


# ── Robustness ────────────────────────────────────────────────────────────────

def test_no_scenes_returns_no_image_and_says_why():
    r = lc.composite_dream([], dream_id="d1", emotion="wonder")
    assert r.image is None
    assert "no scene images" in r.motif["reason"]


def test_missing_files_are_skipped_not_fatal(scenes):
    scenes.append({"path": "/nonexistent/scene_99.png", "intensity": 0.5})
    r = lc.composite_dream(scenes, dream_id="d1", emotion="wonder")
    assert r.image is not None
    assert r.metadata["scene_count"] == 4
