"""
faculties.dream — eLo Dream Faculty.

WO-DREAM-ENGINE-001. Offline generative period in which experiences,
memories, relationships, patterns, emotions and unfinished ideas are
recombined into new associations, hypotheses and creative artefacts.

Pipeline, in order:

    sleep_cycle    PHASE 1  5-cycle schedule, phase state machine, intensity
    dream_input    PHASE 2  13 source types, emotion vector, peaks, gravity
    dream_work     PHASE 3  seeds, condensation/displacement/symbolic, worlds
    prompt_builder PHASE 4  12-field structured image prompts

Invariant the WO sets, carried by every stage: dream material is never
silently written as fact. Outputs are tagged DREAM / HYPOTHESIS /
CREATIVE ASSOCIATION, and the Dream Faculty does not speak to David
directly — the Executive routes what surfaces.

Existing modules dream_faculty.py and symbol_engine.py are deliberately NOT
imported here: dream_faculty pulls the LLM-facing path, and importing it at
package level would make every `faculties.dream.*` import pay that cost.
Import it explicitly where it is needed.
"""
from __future__ import annotations

from faculties.dream import sleep_cycle, dream_input, dream_work, prompt_builder

from faculties.dream.sleep_cycle import (
    TOTAL_CYCLES,
    INTENSITY_SCALE,
    CyclePhase,
    SleepCycle,
    build_schedule,
    content_band,
    intensity_for,
    intensity_label,
    rem_phases,
    total_duration_s,
)
from faculties.dream.dream_input import (
    EMOTION_DIMENSIONS,
    GRAVITY_COMPONENTS,
    SOURCE_TYPES,
    DreamInputField,
    MemoryItem,
    collect,
    day_residue,
    dominant_emotion,
    emotional_intensity,
    find_emotional_peaks,
    parse_emotion_vector,
)
from faculties.dream.dream_work import (
    MECHANISMS,
    DreamScene,
    DreamSeed,
    DreamWorkResult,
    DreamWorld,
    build_dream_world,
    build_scenes,
    condense,
    displace,
    run_dream_work,
    select_seeds,
    symbolic_transform,
)
from faculties.dream.prompt_builder import (
    EMOTION_VISUAL,
    FINAL_LINE,
    PROMPT_FIELDS,
    DreamPrompt,
    abstraction_band,
    bounded_mix,
    build_prompt,
    build_prompts,
    visual_translation,
)

# Every dream output carries one of these. Never "FACT".
OUTPUT_TYPES: tuple[str, ...] = ("DREAM", "HYPOTHESIS", "CREATIVE ASSOCIATION")

__all__ = [
    "sleep_cycle", "dream_input", "dream_work", "prompt_builder",
    "OUTPUT_TYPES",
    # PHASE 1
    "TOTAL_CYCLES", "INTENSITY_SCALE", "CyclePhase", "SleepCycle",
    "build_schedule", "content_band", "intensity_for", "intensity_label",
    "rem_phases", "total_duration_s",
    # PHASE 2
    "EMOTION_DIMENSIONS", "GRAVITY_COMPONENTS", "SOURCE_TYPES",
    "DreamInputField", "MemoryItem", "collect", "day_residue",
    "dominant_emotion", "emotional_intensity", "find_emotional_peaks",
    "parse_emotion_vector",
    # PHASE 3
    "MECHANISMS", "DreamScene", "DreamSeed", "DreamWorkResult", "DreamWorld",
    "build_dream_world", "build_scenes", "condense", "displace",
    "run_dream_work", "select_seeds", "symbolic_transform",
    # PHASE 4
    "EMOTION_VISUAL", "FINAL_LINE", "PROMPT_FIELDS", "DreamPrompt",
    "abstraction_band", "bounded_mix", "build_prompt", "build_prompts",
    "visual_translation",
]
