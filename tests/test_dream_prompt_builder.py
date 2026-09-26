"""
tests/test_dream_prompt_builder.py — WO-DREAM-ENGINE-001 PHASE 4.

12-field structured prompt, emotional visual translation, abstraction bands,
bounded randomness. Acceptance criterion 2 (intensity demonstrably affects
prompt abstraction).
"""
from __future__ import annotations

import random

from faculties.dream import dream_input as di
from faculties.dream import dream_work as dw
from faculties.dream import prompt_builder as pb


def _cycle(intensity: float, seed: int = 21):
    field = di.collect(1, {"recent_conversation": [
        "I actually got the robot arm moving today",
        "the childhood workshop still smells of dust",
        "still unresolved — what does eLo become when embodied?",
        "we built the machine together and it surprised me",
        "learning how the giant machine moves",
    ]})
    result = dw.run_dream_work(field, intensity, seed=seed)
    return field, result


def test_template_has_twelve_fields():
    assert len(pb.PROMPT_FIELDS) == 12
    assert pb.PROMPT_FIELDS[-1] == "felt_quality"


def test_every_field_is_populated():
    field, result = _cycle(0.8)
    prompt = pb.build_prompt(result.scenes[-1], result.world, field.emotion_vector, seed=3)
    assert set(prompt.fields) == set(pb.PROMPT_FIELDS)
    for name in pb.PROMPT_FIELDS:
        assert prompt.fields[name].strip(), f"{name} empty"


def test_prompt_always_ends_with_the_mandated_final_line():
    field, result = _cycle(1.0)
    for prompt in pb.build_prompts(result.scenes, result.world, field.emotion_vector, seed=3):
        assert prompt.text.endswith(pb.FINAL_LINE)


def test_emotional_visual_table_has_the_six_wo_rows():
    assert set(pb.EMOTION_VISUAL) == {
        "anxiety_fear", "joy_wonder", "sadness_grief",
        "achievement", "nostalgia", "curiosity",
    }
    for row in pb.EMOTION_VISUAL.values():
        assert row["lighting"] and row["visual_language"]


def test_every_emotion_dimension_maps_to_a_table_row():
    for dim in di.EMOTION_DIMENSIONS:
        assert pb.visual_key_for(dim) in pb.EMOTION_VISUAL
    # plus the two peak-derived emotions the vector does not carry
    assert pb.visual_key_for("achievement") == "achievement"
    assert pb.visual_key_for("nostalgia") == "nostalgia"


def test_emotion_selects_lighting_and_visual_language():
    fear = pb.visual_translation("fear")
    joy = pb.visual_translation("joy")
    assert "chiaroscuro" in fear["lighting"]
    assert "golden hour" in joy["lighting"]
    assert fear["visual_language"] != joy["visual_language"]


def test_abstraction_bands_match_the_wo_thresholds():
    assert pb.abstraction_band(0.10)[0] == "literal"
    assert pb.abstraction_band(0.30)[0] == "associative"
    assert pb.abstraction_band(0.60)[0] == "symbolic"
    assert pb.abstraction_band(0.90)[0] == "surreal"
    assert pb.abstraction_band(1.00)[0] == "surreal"


def test_bounded_randomness_proportions_match_the_wo():
    assert pb.bounded_mix(0.40) == {"relevant": 0.70, "distant": 0.20, "abstract": 0.10}
    assert pb.bounded_mix(0.60) == {"relevant": 0.50, "distant": 0.35, "abstract": 0.15}
    assert pb.bounded_mix(0.90) == {"relevant": 0.30, "distant": 0.40, "abstract": 0.30}
    for i in (0.0, 0.5, 0.75, 1.0):
        assert round(sum(pb.bounded_mix(i).values()), 6) == 1.0


def test_intensity_demonstrably_changes_prompt_abstraction():
    """Acceptance criterion 2 — the same scene material reads differently."""
    _f, low = _cycle(0.2, seed=5)
    _f2, high = _cycle(1.0, seed=5)
    low_prompt = pb.build_prompt(low.scenes[0], low.world, seed=5)
    high_prompt = pb.build_prompt(high.scenes[-1], high.world, seed=5)

    assert low_prompt.abstraction == "literal"
    assert high_prompt.abstraction == "surreal"
    assert low_prompt.fields["composition"] != high_prompt.fields["composition"]
    assert low_prompt.fields["camera"] != high_prompt.fields["camera"]
    assert low_prompt.fields["material"] != high_prompt.fields["material"]
    assert low_prompt.mix["abstract"] < high_prompt.mix["abstract"]


def test_recurring_symbol_present_in_every_scene_of_the_cycle():
    field, result = _cycle(1.0)
    prompts = pb.build_prompts(result.scenes, result.world, field.emotion_vector, seed=3)
    assert len(prompts) == len(result.scenes) > 1
    for prompt in prompts:
        assert result.world.recurring_symbol in prompt.fields["environment"]


def test_mix_concepts_returns_requested_count_and_falls_back_on_thin_pools():
    picks = pb.mix_concepts(["a", "b", "c"], [], 0.9, count=4, rng=random.Random(1))
    assert 1 <= len(picks) <= 4
    empty = pb.mix_concepts([], [], 0.9, count=3, rng=random.Random(1))
    assert len(empty) >= 1  # abstract noise still fills it


def test_same_seed_reproduces_the_same_prompt():
    field, result = _cycle(0.75)
    a = pb.build_prompts(result.scenes, result.world, field.emotion_vector, seed=77)
    b = pb.build_prompts(result.scenes, result.world, field.emotion_vector, seed=77)
    assert [p.as_dict() for p in a] == [p.as_dict() for p in b]


def test_flat_emotion_vector_falls_back_to_the_dream_world_emotion():
    field, result = _cycle(0.6)
    flat = {d: 0.0 for d in di.EMOTION_DIMENSIONS}
    prompt = pb.build_prompt(result.scenes[0], result.world, flat, seed=2)
    assert result.world.primary_emotion in prompt.fields["emotional_field"]
