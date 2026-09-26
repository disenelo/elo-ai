"""
tests/test_dream_input.py — WO-DREAM-ENGINE-001 PHASE 2.

Dream Input Field, emotional parser, peaks, memory gravity.
Acceptance criterion 3 (7-dimension emotion vector extracted per dream).
"""
from __future__ import annotations

from faculties.dream import dream_input as di


def test_thirteen_source_types_in_canonical_order():
    assert len(di.SOURCE_TYPES) == 13
    assert [sid for sid, _k, _d in di.SOURCE_TYPES] == list(range(1, 14))
    assert di.SOURCE_KEYS[0] == "recent_conversation"
    assert di.SOURCE_KEYS[-1] == "embodiment"


def test_band_source_filtering_matches_wo():
    assert di.BAND_SOURCE_IDS["early"] == (1, 2, 3, 4)
    assert di.BAND_SOURCE_IDS["middle"] == (5, 6, 7, 8)
    # late = 9-13 plus cross-era memory (source 3)
    assert set(di.BAND_SOURCE_IDS["late"]) == {9, 10, 11, 12, 13, 3}


def test_emotion_vector_has_exactly_seven_dimensions():
    vec = di.parse_emotion_vector("I am so happy and curious about this")
    assert set(vec) == set(di.EMOTION_DIMENSIONS)
    assert len(vec) == 7
    assert all(0.0 <= v <= 1.0 for v in vec.values())


def test_unemotional_text_produces_flat_vector():
    vec = di.parse_emotion_vector("the value of n equals four")
    assert all(v == 0.0 for v in vec.values())
    assert di.emotional_intensity(vec) == 0.0


def test_emotion_dimensions_detected_separately():
    joy = di.parse_emotion_vector("happy glad delight")
    assert joy["joy"] > 0
    fear = di.parse_emotion_vector("afraid scared danger")
    assert fear["fear"] > 0
    assert fear["joy"] == 0.0
    assert di.dominant_emotion(fear) == "fear"


def test_emotional_intensity_normalised_to_unit_range():
    full = {d: 1.0 for d in di.EMOTION_DIMENSIONS}
    assert di.emotional_intensity(full) == 1.0
    assert di.emotional_intensity({d: 0.0 for d in di.EMOTION_DIMENSIONS}) == 0.0


def test_memory_gravity_has_seven_components_and_unit_range():
    assert len(di.GRAVITY_COMPONENTS) == 7
    item = di.MemoryItem(content="x", source_id=1, source_key="recent_conversation")
    assert item.gravity == 0.0
    for comp in di.GRAVITY_COMPONENTS:
        setattr(item, comp, 1.0)
    assert item.gravity == 1.0


def test_explicit_metadata_overrides_derived_gravity():
    field = di.collect(1, {"recent_conversation": [
        {"content": "a quiet note", "significance": 0.99, "future_relevance": 0.9},
    ]})
    item = field.items[0]
    assert item.significance == 0.99
    assert item.future_relevance == 0.9


def test_recurrence_observed_across_the_field_not_declared():
    field = di.collect(1, {"recent_conversation": [
        "the robot arm moved",
        "robot arm again today",
        "still thinking about the robot arm",
        "unrelated weather note",
    ]})
    by_content = {i.content: i for i in field.items}
    assert by_content["the robot arm moved"].recurrence > 0
    assert by_content["unrelated weather note"].recurrence == 0.0


def test_day_residue_is_sources_1_and_2_only_and_untransformed():
    ctx = {
        "recent_conversation": ["we talked about the arm"],
        "recent_experiences": ["eLo watched the screen"],
        "memory": ["an older session"],
    }
    residue = di.day_residue(ctx)
    assert residue == ["we talked about the arm", "eLo watched the screen"]
    assert "an older session" not in residue


def test_emotional_peaks_ranked_and_carry_seven_dimensions():
    peaks = di.find_emotional_peaks([
        {"timestamp": "22:14", "content": "I actually got the arm moving.",
         "significance": 0.92},
        {"timestamp": "22:20", "content": "the value of n equals four",
         "significance": 0.10},
    ])
    assert len(peaks) == 1
    peak = peaks[0]
    assert peak["timestamp"] == "22:14"
    assert peak["significance"] == 0.92
    for dim in di.EMOTION_DIMENSIONS:
        assert dim in peak


def test_collect_selects_sources_by_cycle_band():
    ctx = {key: [f"material from {key}"] for key in di.SOURCE_KEYS}
    early = di.collect(1, ctx)
    middle = di.collect(3, ctx)
    late = di.collect(5, ctx)

    assert early.content_band == "early"
    assert {i.source_key for i in early.items} == {
        "recent_conversation", "recent_experiences", "memory", "project_memory"}
    assert {i.source_key for i in middle.items} == {
        "wkg", "spg", "emotional_significance", "unfinished_threads"}
    # late pulls 9-13 plus cross-era memory
    assert "memory" in {i.source_key for i in late.items}
    assert "embodiment" in {i.source_key for i in late.items}


def test_collect_degrades_to_empty_without_raising():
    field = di.collect(1, None)
    assert field.is_empty
    assert field.emotional_intensity == 0.0
    assert field.peaks == []
    assert field.as_dict()["items"] == []


def test_by_gravity_ranks_heaviest_first():
    field = di.collect(1, {"recent_conversation": [
        {"content": "flat note", "significance": 0.0},
        {"content": "this mattered enormously", "significance": 1.0,
         "emotional_weight": 1.0, "relationship_importance": 1.0},
    ]})
    ranked = field.by_gravity()
    assert ranked[0].content == "this mattered enormously"
    assert ranked[0].gravity > ranked[-1].gravity


def test_unresolvedness_rises_with_unfinished_cues():
    open_field = di.collect(1, {"recent_conversation": [
        "still unresolved, need to finish this tomorrow?"]})
    closed_field = di.collect(1, {"recent_conversation": ["done"]})
    assert open_field.unresolvedness > closed_field.unresolvedness
