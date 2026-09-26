"""
tests/test_dream_package.py — WO-DREAM-ENGINE-001.

Package surface + an end-to-end run of all four phases with no LLM,
no network and no server. Covers acceptance criterion 6 (>= 2 scenes
across a full sleep session) and criterion 10 (nothing tagged FACT).
"""
from __future__ import annotations

import faculties.dream as dream


def test_package_exports_all_four_phases():
    for module in ("sleep_cycle", "dream_input", "dream_work", "prompt_builder"):
        assert hasattr(dream, module)
    assert len(dream.__all__) == len(set(dream.__all__))
    for name in dream.__all__:
        assert hasattr(dream, name), f"missing export {name}"


def test_output_types_never_include_fact():
    assert dream.OUTPUT_TYPES == ("DREAM", "HYPOTHESIS", "CREATIVE ASSOCIATION")
    assert "FACT" not in dream.OUTPUT_TYPES


def test_existing_dream_modules_still_import():
    """No regression — dream_faculty and symbol_engine are untouched."""
    from faculties.dream import dream_faculty, symbol_engine
    assert dream_faculty.DREAM_COOLDOWN == 3600
    assert callable(symbol_engine.map_to_symbols)


def test_full_sleep_session_end_to_end():
    context = {
        "recent_conversation": [
            "I actually got the robot arm moving today",
            "we talked about what eLo becomes when embodied",
        ],
        "recent_experiences": ["eLo watched the servo twitch and stop"],
        "memory": ["the first workshop, years ago, smelled of dust"],
        "project_memory": ["building the dream faculty"],
        "wkg": ["robot connects to embodiment and creation"],
        "spg": ["repeated theme of making imagined things physical"],
        "emotional_significance": ["it mattered more than expected"],
        "unfinished_threads": ["still unresolved — the arm stops at the same angle"],
        "novelty": ["first time it moved on its own"],
        "failure": ["the servo did not respond"],
        "achievement": ["it worked, finally"],
        "relationship": ["David stayed up to watch it move"],
        "embodiment": ["eLo felt the weight of standing all day"],
    }

    total_scenes = 0
    intensities = []

    for phase in dream.rem_phases():
        field = dream.collect(phase.cycle_number, context)
        assert len(field.emotion_vector) == 7

        result = dream.run_dream_work(field, phase.dream_intensity, seed=phase.cycle_number)
        assert result.seeds, f"cycle {phase.cycle_number} produced no seeds"
        assert result.world is not None

        prompts = dream.build_prompts(
            result.scenes, result.world, field.emotion_vector, seed=phase.cycle_number
        )
        assert len(prompts) == len(result.scenes)
        for prompt in prompts:
            assert prompt.text.endswith(dream.FINAL_LINE)
            assert set(prompt.fields) == set(dream.PROMPT_FIELDS)

        total_scenes += len(result.scenes)
        intensities.append(phase.dream_intensity)

    # criterion 6 — minimum 2 scenes across a full sleep session
    assert total_scenes >= 2
    # criterion 1 — REM intensity climbs across the session
    assert intensities == sorted(intensities)
    assert intensities[-1] == 1.00


def test_late_cycles_are_more_abstract_than_early_cycles():
    context = {key: [f"material about {key} and the robot arm"] for key in
               [k for _i, k, _d in dream.SOURCE_TYPES]}

    early_field = dream.collect(1, context)
    late_field = dream.collect(5, context)

    early = dream.run_dream_work(early_field, 0.20, seed=4)
    late = dream.run_dream_work(late_field, 1.00, seed=4)

    assert len(late.scenes) > len(early.scenes)
    assert len(late.transformations) > len(early.transformations)

    early_prompt = dream.build_prompt(early.scenes[0], early.world, seed=4)
    late_prompt = dream.build_prompt(late.scenes[-1], late.world, seed=4)
    assert early_prompt.abstraction == "literal"
    assert late_prompt.abstraction == "surreal"
