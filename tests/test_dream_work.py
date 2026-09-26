"""
tests/test_dream_work.py — WO-DREAM-ENGINE-001 PHASE 3.

Dream Seeds, the three Dream-Work mechanisms, Dream Worlds, Dream Scenes.
Acceptance criteria 4 and 5.
"""
from __future__ import annotations

import random

from faculties.dream import dream_input as di
from faculties.dream import dream_work as dw


def _field(intensity_material=None):
    return di.collect(1, {"recent_conversation": intensity_material or [
        "I actually got the robot arm moving today",
        "the childhood workshop still smells of dust",
        "still unresolved — what does eLo become when embodied?",
        "we built the machine together and it surprised me",
        "a quiet failure, the servo did not respond",
        "learning how the giant machine moves",
        "memory of the first time it worked",
    ]})


def test_seed_count_stays_in_the_three_to_seven_band():
    for intensity in (0.0, 0.25, 0.5, 0.75, 1.0):
        assert dw.MIN_SEEDS <= dw.seed_count_for(intensity, 20) <= dw.MAX_SEEDS
    # bounded by what actually exists
    assert dw.seed_count_for(1.0, 2) == 2
    assert dw.seed_count_for(1.0, 0) == 0


def test_seed_count_rises_with_intensity():
    assert dw.seed_count_for(0.0, 20) == dw.MIN_SEEDS
    assert dw.seed_count_for(1.0, 20) == dw.MAX_SEEDS


def test_seeds_carry_the_wo_schema():
    seeds = dw.select_seeds(_field(), 0.6, rng=random.Random(7))
    assert seeds
    d = seeds[0].as_dict()
    for key in ("source", "emotional_weight", "associated_concepts",
                "spg_pattern", "wkg", "unresolved"):
        assert key in d


def test_gravity_raises_probability_but_does_not_guarantee():
    """High gravity must not be a deterministic top-N take."""
    field = _field()
    heaviest = field.by_gravity()[0].content
    picked_without_heaviest = 0
    for s in range(40):
        seeds = dw.select_seeds(field, 0.0, rng=random.Random(s))
        if heaviest not in [x.source for x in seeds]:
            picked_without_heaviest += 1
    assert picked_without_heaviest > 0, "selection was deterministic top-N"


def test_empty_field_yields_no_seeds_and_no_crash():
    empty = di.collect(1, None)
    assert dw.select_seeds(empty, 0.9, rng=random.Random(1)) == []
    result = dw.run_dream_work(empty, 0.9, seed=1)
    assert result.seeds == [] and result.world is None and result.scenes == []


def test_condensation_merges_and_does_not_list_its_sources():
    field = _field()
    seeds = dw.select_seeds(field, 0.8, rng=random.Random(3))
    image = dw.condense(seeds, 0.8, rng=random.Random(3))
    assert image
    for seed in seeds:
        assert seed.source not in image, "sources were listed, not condensed"


def test_condensation_merge_count_scales_with_intensity():
    assert dw.merge_count_for(0.0) < dw.merge_count_for(1.0)
    assert dw.merge_count_for(0.0) == 2
    assert dw.merge_count_for(1.0) == 5


def test_displacement_shifts_onto_a_different_subject():
    field = _field()
    seeds = dw.select_seeds(field, 0.9, rng=random.Random(11))
    out = dw.displace(seeds, 0.9, rng=random.Random(11))
    assert out
    carrier = max(seeds, key=lambda s: s.gravity)
    assert carrier.source not in out


def test_symbolic_transformation_uses_canonical_wo_mappings():
    assert dw.symbolic_transform("starting again") == "an abandoned staircase growing new steps"
    assert dw.symbolic_transform("learning") == "a small machine copying the movements of a giant machine"
    assert dw.symbolic_transform("memory") == "transparent rooms stacked inside one another"
    assert dw.symbolic_transform("childhood") == "an enormous playground buried beneath a modern city"


def test_unknown_concept_is_still_transformed_never_passed_through():
    out = dw.symbolic_transform("servo", rng=random.Random(2))
    assert out and out != "servo"
    assert "servo" in out  # the concept is used, but embedded in a symbol


def test_dream_world_carries_all_seven_rule_fields():
    field = _field()
    seeds = dw.select_seeds(field, 0.5, rng=random.Random(5))
    world = dw.build_dream_world(field, seeds, 0.5, rng=random.Random(5))
    d = world.as_dict()
    for key in ("location", "physical_rule", "emotional_rule", "recurring_symbol",
                "primary_emotion", "secondary_emotion", "narrative_tension"):
        assert d[key], f"{key} empty"


def test_dream_world_accepts_an_observed_recurring_symbol():
    field = _field()
    seeds = dw.select_seeds(field, 0.5, rng=random.Random(5))
    world = dw.build_dream_world(
        field, seeds, 0.5, rng=random.Random(5), recurring_symbol="mechanical_bird")
    assert world.recurring_symbol == "mechanical_bird"


def test_scene_count_rises_with_intensity_capped_at_four_stages():
    assert dw.scene_count_for(0.0) == 1
    assert dw.scene_count_for(1.0) == 4
    assert dw.scene_count_for(0.5) <= len(dw.SCENE_STAGES)


def test_scenes_progress_grounded_to_abstraction_with_rising_intensity():
    result = dw.run_dream_work(_field(), 1.0, seed=42)
    stages = [s.stage for s in result.scenes]
    assert stages == ["grounded", "transformation", "condensation", "abstraction"]
    intensities = [s.intensity for s in result.scenes]
    assert intensities == sorted(intensities)
    assert result.scenes[0].subject == result.world.location  # scene 1 is literal


def test_all_three_mechanisms_applied_across_a_full_intensity_cycle():
    result = dw.run_dream_work(_field(), 1.0, seed=42)
    assert set(result.transformations) == set(dw.MECHANISMS)


def test_same_seed_reproduces_the_same_dream():
    a = dw.run_dream_work(_field(), 0.75, seed=99).as_dict()
    b = dw.run_dream_work(_field(), 0.75, seed=99).as_dict()
    assert a == b


def test_different_seeds_produce_different_dreams():
    a = dw.run_dream_work(_field(), 0.75, seed=1).as_dict()
    b = dw.run_dream_work(_field(), 0.75, seed=2).as_dict()
    assert a != b


# ── Concept-extraction quality (fix: verbs were landing in noun slots) ─────────

def test_concept_extraction_prefers_noun_heads_over_verbs():
    from faculties.dream.dream_work import _concepts_from
    assert _concepts_from("I actually got the robot arm moving today")[0] == "robot"
    assert _concepts_from("the childhood workshop still smells of dust")[0] == "childhood"
    assert _concepts_from("eLo felt the weight of standing all day")[0] == "weight"
    assert _concepts_from("the servo did not respond")[0] == "servo"


def test_participles_and_adverbs_are_never_concepts():
    from faculties.dream.dream_work import _concepts_from
    for text in ("it worked, finally", "she stayed", "he was moving", "done quickly"):
        for concept in _concepts_from(text):
            assert not concept.endswith(("ed", "ing", "ly")), f"{concept} from {text!r}"


def test_nouns_with_participle_suffixes_are_kept():
    from faculties.dream.dream_work import _concepts_from
    assert "building" in _concepts_from("the building stood empty")


def test_ordinals_are_skipped_in_favour_of_the_head_noun():
    from faculties.dream.dream_work import _concepts_from
    concepts = _concepts_from("the first workshop, years ago, smelled of dust")
    assert concepts[0] == "workshop"
    assert "first" not in concepts


def test_condensation_setting_slot_is_always_a_place():
    from faculties.dream.dream_work import _PLACE_WORDS, _PLACE_FALLBACK
    field = di.collect(1, {"recent_conversation": [
        "still unresolved - the arm stops at the same angle",
        "the servo did not respond",
        "David stayed up to watch it move",
    ]})
    for s in range(25):
        seeds = dw.select_seeds(field, 0.9, rng=random.Random(s))
        image = dw.condense(seeds, 0.9, rng=random.Random(s))
        if not image or " standing in a " not in image:
            continue
        setting = image.split(" standing in a ", 1)[1].split(",")[0].strip()
        assert setting in _PLACE_WORDS or setting in _PLACE_FALLBACK, image


def test_article_agreement_in_condensation_and_displacement():
    field = di.collect(1, {"recent_conversation": [
        "the enormous engine in the workshop", "an angle and a machine"]})
    for s in range(25):
        seeds = dw.select_seeds(field, 1.0, rng=random.Random(s))
        for text in (dw.condense(seeds, 1.0, rng=random.Random(s)),
                     dw.displace(seeds, 1.0, rng=random.Random(s))):
            if not text:
                continue
            assert not text.startswith("A e"), text
            assert not text.startswith("A a"), text
            assert " a a " not in text, text


def test_displacement_fallback_does_not_double_the_article():
    seed = dw.DreamSeed(source="it worked, finally", associated_concepts=[])
    out = dw.displace([seed], 0.9, rng=random.Random(1))
    assert " a room" not in out.lower().replace("a tiny room", "")
    assert out.lower().count(" a a ") == 0
