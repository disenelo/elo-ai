"""
faculties/dream/prompt_builder.py — Structured dream prompt generation.

WO-DREAM-ENGINE-001 PHASE 4.

Distinct from runtime/prompt_builder.py — that one builds eLo's conversational
system prompt. This one builds image prompts for dream scenes.

The 12-field template:

    SUBJECT + ENVIRONMENT + EMOTIONAL FIELD + SYMBOLIC TRANSFORMATION
    + DREAM RULE + COMPOSITION + LIGHTING + MATERIAL + CAMERA + STYLE
    + ABSTRACTION LEVEL + FELT QUALITY

The WO names eleven fields and then mandates a fixed closing line on every
prompt. That closing line is carried here as the twelfth field, FELT QUALITY,
so the count in the WO and the count in the code agree. It is constant and
is never rewritten.

Consumes the DreamScene / DreamWorld objects built by dream_work.py.
No LLM, no network, no server.py.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field as _field
from typing import Mapping, Sequence

from faculties.dream.dream_input import EMOTION_DIMENSIONS, dominant_emotion
from faculties.dream.dream_work import DreamScene, DreamWorld

# The mandated closing sentence. Every prompt ends with this, verbatim.
FINAL_LINE = (
    "The image should feel like a remembered experience being transformed, "
    "not a literal illustration of the source memory."
)

PROMPT_FIELDS: tuple[str, ...] = (
    "subject",
    "environment",
    "emotional_field",
    "symbolic_transformation",
    "dream_rule",
    "composition",
    "lighting",
    "material",
    "camera",
    "style",
    "abstraction_level",
    "felt_quality",
)

# ── Emotional Visual Translation (WO PHASE 4 table) ────────────────────────────
EMOTION_VISUAL: dict[str, dict[str, str]] = {
    "anxiety_fear": {
        "lighting": "chiaroscuro, harsh shadows, deep monochromatic blues and blacks",
        "visual_language": "unstable perspective, compressed space, repetition, "
                           "interrupted geometry",
    },
    "joy_wonder": {
        "lighting": "volumetric golden hour light, highly saturated pastels",
        "visual_language": "scale, openness, unusual colour, impossible structures",
    },
    "sadness_grief": {
        "lighting": "diffused overcast daylight, muted greys, washed-out teals",
        "visual_language": "absence, empty space, fading forms, incomplete objects",
    },
    "achievement": {
        "lighting": "warm upward light, emergence",
        "visual_language": "upward movement, illumination, structural completion",
    },
    "nostalgia": {
        "lighting": "faded, soft",
        "visual_language": "familiar forms, old textures, partial reconstruction",
    },
    "curiosity": {
        "lighting": "cool clear light",
        "visual_language": "revealed detail, layers, discovery",
    },
}

# Maps every emotion this pipeline can produce onto a table row.
# joy/wonder, fear/anxiety and sadness share rows per the WO.
# anger is NOT given a row in the WO — it is routed to anxiety_fear, whose
# visual language (unstable, compressed, interrupted) is the nearest fit.
# Flagged rather than invented: David/Board to confirm or add an anger row.
_EMOTION_TO_VISUAL: dict[str, str] = {
    "joy": "joy_wonder",
    "wonder": "joy_wonder",
    "fear": "anxiety_fear",
    "anxiety": "anxiety_fear",
    "anger": "anxiety_fear",
    "sadness": "sadness_grief",
    "grief": "sadness_grief",
    "curiosity": "curiosity",
    "achievement": "achievement",
    "nostalgia": "nostalgia",
}


def visual_key_for(emotion: str) -> str:
    """Table row for an emotion name. Unknown emotions fall back to joy_wonder."""
    return _EMOTION_TO_VISUAL.get((emotion or "").strip().lower(), "joy_wonder")


def visual_translation(emotion: str) -> dict[str, str]:
    """Lighting/palette + visual language for an emotion."""
    return dict(EMOTION_VISUAL[visual_key_for(emotion)])


# ── Abstraction bands ──────────────────────────────────────────────────────────
ABSTRACTION_BANDS: tuple[tuple[float, float, str, str], ...] = (
    (0.00, 0.25, "literal",     "literal, grounded, minimal transformation"),
    (0.25, 0.50, "associative", "associative, partial transformation"),
    (0.50, 0.75, "symbolic",    "symbolic, condensation active"),
    (0.75, 1.01, "surreal",     "fully surreal, displacement and abstraction dominant"),
)


def abstraction_band(intensity: float) -> tuple[str, str]:
    """(name, description) for an intensity. Bands are lower-inclusive."""
    value = max(0.0, min(1.0, float(intensity)))
    for low, high, name, description in ABSTRACTION_BANDS:
        if low <= value < high:
            return name, description
    return ABSTRACTION_BANDS[-1][2], ABSTRACTION_BANDS[-1][3]


# ── Bounded randomness (WO PHASE 4) ────────────────────────────────────────────

def bounded_mix(intensity: float) -> dict[str, float]:
    """
    Relevant / distant / abstract-noise proportions for a given intensity.

        < 0.50      -> 70 / 20 / 10
        0.50-0.75   -> 50 / 35 / 15
        > 0.75      -> 30 / 40 / 30
    """
    value = max(0.0, min(1.0, float(intensity)))
    if value < 0.50:
        return {"relevant": 0.70, "distant": 0.20, "abstract": 0.10}
    if value <= 0.75:
        return {"relevant": 0.50, "distant": 0.35, "abstract": 0.15}
    return {"relevant": 0.30, "distant": 0.40, "abstract": 0.30}


_ABSTRACT_NOISE = (
    "a colour that has no name",
    "a sound rendered as texture",
    "an edge that does not close",
    "weight without mass",
    "a direction that is not on the compass",
    "the inside of a pause",
)


def mix_concepts(
    relevant: Sequence[str],
    distant: Sequence[str],
    intensity: float,
    *,
    count: int = 4,
    rng: random.Random | None = None,
) -> list[str]:
    """
    Draw `count` concepts according to the bounded-randomness proportions.

    Falls back across pools when one is empty, so a thin dream still produces
    a full prompt rather than a short one.
    """
    rng = rng or random.Random()
    mix = bounded_mix(intensity)
    pools = {
        "relevant": list(relevant),
        "distant": list(distant),
        "abstract": list(_ABSTRACT_NOISE),
    }

    picks: list[str] = []
    order = ("relevant", "distant", "abstract")
    quotas = {k: int(round(mix[k] * count)) for k in order}
    # Rounding can drift; give any shortfall to the largest share.
    drift = count - sum(quotas.values())
    if drift:
        quotas[max(order, key=lambda k: mix[k])] += drift

    for key in order:
        for _ in range(max(0, quotas[key])):
            pool = pools[key] or pools["relevant"] or pools["distant"] or pools["abstract"]
            if not pool:
                continue
            choice = rng.choice(pool)
            if choice in pool:
                pool.remove(choice)
            if choice not in picks:
                picks.append(choice)

    return picks


# ── Field pools ────────────────────────────────────────────────────────────────
_COMPOSITION_BY_BAND = {
    "literal": "centred, eye-level, stable horizon",
    "associative": "off-centre, one element larger than it should be",
    "symbolic": "layered depth, foreground and background disagreeing on scale",
    "surreal": "no stable horizon, the frame folding back into itself",
}

_CAMERA_BY_BAND = {
    "literal": "35mm, natural perspective, shallow movement",
    "associative": "slightly wide, low angle, gentle distortion at the edges",
    "symbolic": "wide angle, tilted, deep focus holding several scales at once",
    "surreal": "impossible lens, perspective bending across the frame",
}

_MATERIAL_BY_BAND = {
    "literal": "real surfaces — worn paint, dust, fabric, cold metal",
    "associative": "familiar materials behaving slightly wrongly",
    "symbolic": "materials merging — glass that holds warmth, metal that folds like cloth",
    "surreal": "matter without a fixed state, surfaces that remember other shapes",
}

_STYLE_BASE = (
    "painterly, photographic depth, no text, no logos, no watermarks, "
    "no readable writing"
)


# ── Prompt ─────────────────────────────────────────────────────────────────────

@dataclass
class DreamPrompt:
    """One structured prompt for one scene."""
    scene_index: int
    intensity: float
    abstraction: str
    fields: dict[str, str] = _field(default_factory=dict)
    concepts: list[str] = _field(default_factory=list)
    mix: dict[str, float] = _field(default_factory=dict)

    @property
    def text(self) -> str:
        """The prompt as sent to the image model. Always ends with FINAL_LINE."""
        parts = [self.fields[name] for name in PROMPT_FIELDS if self.fields.get(name)]
        return ". ".join(p.rstrip(". ") for p in parts[:-1]) + ". " + self.fields["felt_quality"]

    def as_dict(self) -> dict:
        return {
            "scene_index": self.scene_index,
            "intensity": self.intensity,
            "abstraction": self.abstraction,
            "fields": dict(self.fields),
            "concepts": list(self.concepts),
            "mix": dict(self.mix),
            "text": self.text,
        }


def build_prompt(
    scene: DreamScene,
    world: DreamWorld,
    emotion_vector: Mapping[str, float] | None = None,
    *,
    distant_concepts: Sequence[str] = (),
    rng: random.Random | None = None,
    seed: int | None = None,
) -> DreamPrompt:
    """
    Build the 12-field structured prompt for one dream scene.

    emotion_vector   — the 7-dim vector; the highest dimension picks the
                       lighting/palette and visual language.
    distant_concepts — older or unrelated material for the bounded-randomness
                       "distant" share.
    seed             — pass for a reproducible prompt.
    """
    if rng is None:
        rng = random.Random(seed)

    vector = dict(emotion_vector or {})
    emotion = dominant_emotion(vector) if any(vector.get(d, 0.0) for d in EMOTION_DIMENSIONS) \
        else world.primary_emotion
    visual = visual_translation(emotion)
    band, band_description = abstraction_band(scene.intensity)
    mix = bounded_mix(scene.intensity)

    relevant = list(scene.seed_sources)
    concepts = mix_concepts(relevant, distant_concepts, scene.intensity, rng=rng)

    secondary = world.secondary_emotion
    fields = {
        "subject": scene.subject,
        "environment": f"{world.location}, where {world.physical_rule.lower()}",
        "emotional_field": (
            f"{emotion} dominant, {secondary} beneath it; "
            f"{world.narrative_tension.lower()}"
        ),
        "symbolic_transformation": scene.symbolic_subject,
        "dream_rule": f"{world.physical_rule}. {world.emotional_rule}",
        "composition": _COMPOSITION_BY_BAND[band],
        "lighting": visual["lighting"],
        "material": _MATERIAL_BY_BAND[band],
        "camera": _CAMERA_BY_BAND[band],
        "style": f"{visual['visual_language']}; {_STYLE_BASE}",
        "abstraction_level": f"abstraction {scene.intensity:.2f} — {band_description}",
        "felt_quality": FINAL_LINE,
    }

    # The recurring symbol is present in every scene of the cycle — it is what
    # makes a dream world cohere, and what symbol_history later tracks.
    if world.recurring_symbol:
        fields["environment"] += f"; {world.recurring_symbol} recur throughout"

    return DreamPrompt(
        scene_index=scene.index,
        intensity=scene.intensity,
        abstraction=band,
        fields=fields,
        concepts=concepts,
        mix=mix,
    )


def build_prompts(
    scenes: Sequence[DreamScene],
    world: DreamWorld,
    emotion_vector: Mapping[str, float] | None = None,
    *,
    distant_concepts: Sequence[str] = (),
    seed: int | None = None,
) -> list[DreamPrompt]:
    """One prompt per scene, sharing one RNG stream for a reproducible cycle."""
    rng = random.Random(seed)
    return [
        build_prompt(
            scene, world, emotion_vector,
            distant_concepts=distant_concepts, rng=rng,
        )
        for scene in scenes
    ]
