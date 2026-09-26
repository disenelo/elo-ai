"""
faculties/dream/dream_work.py — Dream Seeds + Dream-Work Engine.

WO-DREAM-ENGINE-001 PHASE 3.

  3a. Dream Seeds              — structured objects selected by memory gravity
  3b. Dream-Work mechanisms    — condensation, displacement, symbolic transformation
  3c. Dream Worlds             — per-cycle rule set all scenes obey
  3d. Dream Scenes             — one per REM peak, rising in intensity

Transformation here is deterministic template composition driven by the
emotion vector and dream intensity — not an LLM call. The image model is
prompted later by prompt_builder.py, which consumes what this module builds.
Seeding the RNG makes a dream reproducible for evidence.

The rule the WO sets, enforced here: sources are CONDENSED, never listed.
A scene never restates its seeds verbatim.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field as _field
from typing import Sequence

from faculties.dream.dream_input import (
    DreamInputField,
    MemoryItem,
    dominant_emotion,
)

# Seeds per dream cycle — the WO fixes this band at 3-7.
MIN_SEEDS = 3
MAX_SEEDS = 7

# The four scene stages, in order. Scene count scales with intensity.
SCENE_STAGES: tuple[tuple[str, str], ...] = (
    ("grounded",       "Grounded. The literal location."),
    ("transformation", "Transformation. Objects begin to change."),
    ("condensation",   "Condensation fires. Multiple seeds merge."),
    ("abstraction",    "Abstraction. The world folds."),
)

MECHANISMS: tuple[str, ...] = ("condensation", "displacement", "symbolic_transformation")

# ── 3b. Symbolic transformation table ──────────────────────────────────────────
# Canonical entries are verbatim from the WO. Unknown concepts fall through to
# the structural templates below — a concept is never passed through untouched.
SYMBOL_TABLE: dict[str, str] = {
    "starting again": "an abandoned staircase growing new steps",
    "start":          "an abandoned staircase growing new steps",
    "again":          "an abandoned staircase growing new steps",
    "learning":       "a small machine copying the movements of a giant machine",
    "learn":          "a small machine copying the movements of a giant machine",
    "memory":         "transparent rooms stacked inside one another",
    "remember":       "transparent rooms stacked inside one another",
    "childhood":      "an enormous playground buried beneath a modern city",
    "child":          "an enormous playground buried beneath a modern city",
}

_STRUCTURAL_TEMPLATES: tuple[str, ...] = (
    "a {concept} the size of a building, unfinished",
    "a corridor made entirely of {concept}",
    "a {concept} that keeps rebuilding itself",
    "a field of {concept} seen from far above",
    "a {concept} folded inward until it holds a room",
    "the shadow of a {concept} moving without the thing that casts it",
)

_SCALE_WORDS = ("gigantic", "enormous", "tiny", "vast", "miniature", "towering")
_MATERIAL_WORDS = (
    "unfinished machines", "warm glass", "worn fabric", "soft metal",
    "folded paper", "dust and light", "wet clay",
)

# ── 3c. Dream World pools ──────────────────────────────────────────────────────
_PHYSICAL_RULES = (
    "Everything floats",
    "Nothing casts a shadow",
    "Distance folds — far things are close",
    "Objects keep the warmth of whoever last held them",
    "Light moves slower than sound",
    "Anything set down begins to grow",
)

_EMOTIONAL_RULES_BY_EMOTION: dict[str, tuple[str, ...]] = {
    "joy":       ("Nothing can be lost", "Everything answers back"),
    "wonder":    ("Nothing can be completed", "Every door opens onto another scale"),
    "fear":      ("Nothing stays where it was left", "No room has the same exit twice"),
    "anger":     ("Nothing can be undone", "Every surface resists being moved"),
    "sadness":   ("Nothing can be held on to", "Everything is slightly further than it looks"),
    "anxiety":   ("Nothing can be finished", "Time runs out one room ahead"),
    "curiosity": ("Nothing is fully visible at once", "Every object has an inside"),
}

_RECURRING_SYMBOLS = (
    "mechanical birds", "unlit windows", "a staircase with no top",
    "hands that are not attached to anyone", "small doors set too high",
    "a machine breathing", "rooms inside rooms",
)

_TENSIONS = (
    "Something is trying to become alive",
    "Something is being remembered wrongly",
    "Something is almost finished and will not finish",
    "Something is following at the same speed",
    "Something is being built by no one",
)

_SECONDARY_EMOTIONS = ("nostalgia", "unease", "tenderness", "anticipation", "distance")

# The condensation template puts a concept in a "standing in a ___" slot.
# Only a place reads correctly there; anything else produced "standing in a
# stops". Non-place concepts fall back to a place drawn from this pool.
_PLACE_WORDS = frozenset(
    "workshop hallway yard station room corridor kitchen garage attic cellar "
    "basement garden street city town house building field forest shore beach "
    "library museum theatre factory warehouse tunnel bridge stairwell landing "
    "orchard playground school office studio shed barn".split()
)
_PLACE_FALLBACK = ("workshop", "hallway", "yard", "station", "room", "corridor")


_WORD_RE = re.compile(r"[a-z0-9']+")
_CONCEPT_STOP = frozenset(
    "a an the and or but if then that this those these of to in on at for with "
    "from by is are was were be been being it its as i me my we us our you your "
    "he she they them so not no do did does have has had about really just very "
    "got get went came keep still back into out up down own all any each more "
    "most some such than too when while where what which who how why".split()
)

# Determiners and prepositions that introduce a noun phrase. The token run
# after one of these is the closest cheap approximation of a noun head without
# a POS tagger (no nltk/spacy dependency — this module stays stdlib-only).
_NP_INTRODUCERS = frozenset(
    "the a an of in on at my your his her its their our this that these those "
    "with from about".split()
)

# Ordinals and quantifiers sit between the determiner and the head noun.
_PRE_HEAD_MODIFIERS = frozenset(
    "first second third last next other another same new old every one two "
    "three few many several".split()
)

# Participles and adverbs. Rejected because they landed in noun slots and
# produced "a worked the size of a building" / "standing in a stayed".
_VERBAL_SUFFIXES = ("ed", "ing", "ly")

# Nouns that happen to carry a participle/adverb suffix and are worth keeping.
_SUFFIX_ALLOW = frozenset(
    "building ceiling clothing drawing evening feeling meaning morning "
    "opening painting reading recording string thing wedding shed bed "
    "world child field shield friend weekend legend".split()
)


def _article(word: str) -> str:
    """"a" / "an" agreement. "A enormous" was reaching the prompt text."""
    return "an" if word[:1] in "aeiou" else "a"


def _is_concept_token(word: str) -> bool:
    if len(word) <= 3 or word in _CONCEPT_STOP or word in _PRE_HEAD_MODIFIERS:
        return False
    if word in _SUFFIX_ALLOW:
        return True
    return not word.endswith(_VERBAL_SUFFIXES)


def _concepts_from(text: str, limit: int = 6) -> list[str]:
    """
    Concept tokens usable as the SUBJECT of an image.

    Prefers noun-phrase heads: the run of content words following a determiner
    or preposition. Falls back to plain content-word order when the text has
    no noun phrase. Verbs, participles and adverbs are excluded either way —
    a dream image needs a thing, not an action, in its noun slots.
    """
    words = _WORD_RE.findall(text.lower())
    heads: list[str] = []
    fallback: list[str] = []

    in_phrase = False
    for word in words:
        if word in _NP_INTRODUCERS:
            in_phrase = True
            continue
        if word in _PRE_HEAD_MODIFIERS:
            continue  # skip the modifier, keep looking for the head
        if not _is_concept_token(word):
            in_phrase = False
            continue
        if in_phrase and word not in heads:
            heads.append(word)
        elif word not in fallback:
            fallback.append(word)

    ordered = heads + [w for w in fallback if w not in heads]
    return ordered[:limit]


# ── 3a. Dream Seed ─────────────────────────────────────────────────────────────

@dataclass
class DreamSeed:
    """One structured seed. Shape matches the WO section 3a schema."""
    source: str
    emotional_weight: dict[str, float] = _field(default_factory=dict)
    associated_concepts: list[str] = _field(default_factory=list)
    spg_pattern: str = ""
    wkg: dict[str, list[str]] = _field(default_factory=dict)
    unresolved: str = ""
    gravity: float = 0.0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "emotional_weight": self.emotional_weight,
            "associated_concepts": list(self.associated_concepts),
            "spg_pattern": self.spg_pattern,
            "wkg": {k: list(v) for k, v in self.wkg.items()},
            "unresolved": self.unresolved,
            "gravity": self.gravity,
        }


def _seed_from_item(item: MemoryItem) -> DreamSeed:
    concepts = _concepts_from(item.content)
    weight = {k: v for k, v in (item.emotion_vector or {}).items() if v > 0.0}
    anchor = concepts[0] if concepts else "presence"
    return DreamSeed(
        source=item.content,
        emotional_weight=weight,
        associated_concepts=concepts,
        spg_pattern=(
            f"Repeated theme around {anchor}" if item.recurrence > 0.0 else ""
        ),
        wkg={anchor: concepts[1:4]} if concepts else {},
        unresolved=(item.content if item.unfinishedness > 0.0 else ""),
        gravity=item.gravity,
    )


def seed_count_for(intensity: float, available: int) -> int:
    """3-7 seeds, scaling with intensity and bounded by what exists."""
    span = MAX_SEEDS - MIN_SEEDS
    wanted = MIN_SEEDS + int(round(max(0.0, min(1.0, intensity)) * span))
    return max(0, min(wanted, available))


def select_seeds(
    field: DreamInputField,
    intensity: float,
    *,
    rng: random.Random | None = None,
) -> list[DreamSeed]:
    """
    Select 3-7 seeds, weighted by memory gravity.

    Weighted sampling WITHOUT replacement — high gravity raises probability
    but never guarantees selection, per the WO. A zero-gravity field still
    yields seeds (uniform fallback) rather than returning nothing.
    """
    rng = rng or random.Random()
    pool = list(field.items)
    if not pool:
        return []

    want = seed_count_for(intensity, len(pool))
    chosen: list[MemoryItem] = []
    remaining = list(pool)

    for _ in range(want):
        if not remaining:
            break
        weights = [max(i.gravity, 0.0) + 0.01 for i in remaining]
        total = sum(weights)
        roll = rng.random() * total
        cursor = 0.0
        pick = remaining[-1]
        for item, weight in zip(remaining, weights):
            cursor += weight
            if roll <= cursor:
                pick = item
                break
        chosen.append(pick)
        remaining.remove(pick)

    return [_seed_from_item(i) for i in chosen]


# ── 3b. The three mechanisms ───────────────────────────────────────────────────

def merge_count_for(intensity: float) -> int:
    """How many concepts condensation merges. Intensity drives this."""
    return 2 + int(round(max(0.0, min(1.0, intensity)) * 3))


def condense(
    seeds: Sequence[DreamSeed],
    intensity: float,
    *,
    rng: random.Random | None = None,
) -> str:
    """
    CONDENSATION — multiple seeds merge into one image concept.

    Sources are condensed, never listed. The returned string does not name
    the seeds it came from.
    """
    rng = rng or random.Random()
    if not seeds:
        return ""

    concepts: list[str] = []
    for seed in seeds:
        for concept in seed.associated_concepts:
            if concept not in concepts:
                concepts.append(concept)
    if not concepts:
        return ""

    merged = concepts[: merge_count_for(intensity)]
    scale = rng.choice(_SCALE_WORDS)
    material = rng.choice(_MATERIAL_WORDS)

    head = merged[0]
    candidate = merged[1] if len(merged) > 1 else ""
    setting = candidate if candidate in _PLACE_WORDS else rng.choice(_PLACE_FALLBACK)
    tail = [c for c in merged[2:] if c != setting]

    image = f"{_article(scale).capitalize()} {scale} {head} standing in a {setting}"
    if tail:
        image += f", its {tail[0]} built from {material}"
        for extra in tail[1:]:
            image += f", {extra} showing through"
    else:
        image += f", built from {material}"
    return image


def displace(
    seeds: Sequence[DreamSeed],
    intensity: float,
    *,
    rng: random.Random | None = None,
) -> str:
    """
    DISPLACEMENT — emotional importance shifts onto a different subject.

    The actual subject may not appear. Returns the displaced image.
    """
    rng = rng or random.Random()
    if not seeds:
        return ""

    carrier = max(seeds, key=lambda s: s.gravity)
    others = [s for s in seeds if s is not carrier] or list(seeds)
    host = rng.choice(others)

    # Bare noun — the template supplies the article ("A tiny a room stands").
    host_concept = host.associated_concepts[0] if host.associated_concepts else "room"
    scale = "tiny" if intensity >= 0.5 else "small"
    magnitude = "enormous" if intensity >= 0.5 else "large"

    return (
        f"A {scale} {host_concept} stands at the edge of an {magnitude} "
        f"{host.associated_concepts[1] if len(host.associated_concepts) > 1 else 'cliff'}"
    )


def symbolic_transform(
    concept: str,
    *,
    rng: random.Random | None = None,
) -> str:
    """
    SYMBOLIC TRANSFORMATION — a concept becomes a symbol.

    Canonical mappings from the WO are used when the concept matches.
    Anything else goes through the structural templates: a concept is never
    returned unchanged.
    """
    rng = rng or random.Random()
    if not concept:
        return ""
    low = concept.strip().lower()

    if low in SYMBOL_TABLE:
        return SYMBOL_TABLE[low]
    for key, symbol in SYMBOL_TABLE.items():
        if key in low:
            return symbol

    return rng.choice(_STRUCTURAL_TEMPLATES).format(concept=low)


# ── 3c. Dream World ────────────────────────────────────────────────────────────

@dataclass
class DreamWorld:
    """The rule set every scene in a cycle obeys. Produces coherence."""
    location: str
    physical_rule: str
    emotional_rule: str
    recurring_symbol: str
    primary_emotion: str
    secondary_emotion: str
    narrative_tension: str

    def as_dict(self) -> dict:
        return {
            "location": self.location,
            "physical_rule": self.physical_rule,
            "emotional_rule": self.emotional_rule,
            "recurring_symbol": self.recurring_symbol,
            "primary_emotion": self.primary_emotion,
            "secondary_emotion": self.secondary_emotion,
            "narrative_tension": self.narrative_tension,
        }


def build_dream_world(
    field: DreamInputField,
    seeds: Sequence[DreamSeed],
    intensity: float,
    *,
    rng: random.Random | None = None,
    recurring_symbol: str | None = None,
) -> DreamWorld:
    """
    Construct the Dream World for one cycle, before any scene is generated.

    recurring_symbol — when symbol_history reports a motif recurring across
    >= 3 prior dreams, pass it here so the world carries it. Otherwise one is
    drawn from the pool.
    """
    rng = rng or random.Random()
    primary = dominant_emotion(field.emotion_vector) if field.emotion_vector else "wonder"

    concepts: list[str] = []
    for seed in seeds:
        concepts.extend(seed.associated_concepts)
    location = (
        f"An abandoned {concepts[0]} {rng.choice(('workshop', 'hallway', 'yard', 'station'))}"
        if concepts else "An abandoned childhood workshop"
    )

    emotional_rules = _EMOTIONAL_RULES_BY_EMOTION.get(primary, _EMOTIONAL_RULES_BY_EMOTION["wonder"])

    return DreamWorld(
        location=location,
        physical_rule=rng.choice(_PHYSICAL_RULES),
        emotional_rule=rng.choice(emotional_rules),
        recurring_symbol=recurring_symbol or rng.choice(_RECURRING_SYMBOLS),
        primary_emotion=primary,
        secondary_emotion=rng.choice(_SECONDARY_EMOTIONS),
        narrative_tension=rng.choice(_TENSIONS),
    )


# ── 3d. Dream Scenes ───────────────────────────────────────────────────────────

@dataclass
class DreamScene:
    """One scene — one image. Scenes rise in intensity across a REM period."""
    index: int
    stage: str
    stage_note: str
    intensity: float
    subject: str
    symbolic_subject: str
    mechanisms: list[str] = _field(default_factory=list)
    seed_sources: list[str] = _field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "stage": self.stage,
            "stage_note": self.stage_note,
            "intensity": self.intensity,
            "subject": self.subject,
            "symbolic_subject": self.symbolic_subject,
            "mechanisms": list(self.mechanisms),
            "seed_sources": list(self.seed_sources),
        }


def scene_count_for(intensity: float) -> int:
    """1-4 scenes, rising with the cycle's dream intensity."""
    return max(1, min(len(SCENE_STAGES), 1 + int(round(max(0.0, min(1.0, intensity)) * 3))))


def build_scenes(
    world: DreamWorld,
    seeds: Sequence[DreamSeed],
    intensity: float,
    *,
    rng: random.Random | None = None,
) -> list[DreamScene]:
    """
    Build the scene progression for one REM period.

    Scene intensity ramps from a grounded fraction of the cycle intensity up
    to the cycle intensity itself, so early scenes stay literal and late
    scenes abstract. All scenes obey the Dream World.
    """
    rng = rng or random.Random()
    if not seeds:
        return []

    count = scene_count_for(intensity)
    scenes: list[DreamScene] = []

    for i in range(count):
        stage, note = SCENE_STAGES[i]
        # Ramp: first scene sits at ~40% of cycle intensity, last at 100%.
        ramp = 0.4 + 0.6 * (i / max(1, count - 1)) if count > 1 else 0.4
        scene_intensity = round(intensity * ramp, 2)

        if stage == "grounded":
            subject = world.location
            mechanisms = []
        elif stage == "transformation":
            subject = symbolic_transform(
                seeds[0].associated_concepts[0] if seeds[0].associated_concepts else world.location,
                rng=rng,
            )
            mechanisms = ["symbolic_transformation"]
        elif stage == "condensation":
            subject = condense(seeds, scene_intensity, rng=rng)
            mechanisms = ["condensation", "symbolic_transformation"]
        else:  # abstraction
            subject = displace(seeds, scene_intensity, rng=rng)
            mechanisms = list(MECHANISMS)

        anchor = seeds[i % len(seeds)]
        anchor_concept = (
            anchor.associated_concepts[0] if anchor.associated_concepts else world.recurring_symbol
        )

        scenes.append(
            DreamScene(
                index=i + 1,
                stage=stage,
                stage_note=note,
                intensity=scene_intensity,
                subject=subject or world.location,
                symbolic_subject=symbolic_transform(anchor_concept, rng=rng),
                mechanisms=mechanisms,
                seed_sources=[s.source for s in seeds],
            )
        )

    return scenes


# ── Cycle assembly ─────────────────────────────────────────────────────────────

@dataclass
class DreamWorkResult:
    """Everything PHASE 3 produces for one cycle."""
    seeds: list[DreamSeed]
    world: DreamWorld | None
    scenes: list[DreamScene]
    transformations: list[str]

    def as_dict(self) -> dict:
        return {
            "seeds": [s.as_dict() for s in self.seeds],
            "dream_world": self.world.as_dict() if self.world else None,
            "scenes": [s.as_dict() for s in self.scenes],
            "transformations": list(self.transformations),
        }


def run_dream_work(
    field: DreamInputField,
    intensity: float,
    *,
    seed: int | None = None,
    recurring_symbol: str | None = None,
) -> DreamWorkResult:
    """
    Seeds -> Dream World -> Scenes for one cycle.

    seed — RNG seed. Pass one to make a dream reproducible for evidence.
    """
    rng = random.Random(seed)
    seeds = select_seeds(field, intensity, rng=rng)
    if not seeds:
        return DreamWorkResult(seeds=[], world=None, scenes=[], transformations=[])

    world = build_dream_world(
        field, seeds, intensity, rng=rng, recurring_symbol=recurring_symbol
    )
    scenes = build_scenes(world, seeds, intensity, rng=rng)

    applied: list[str] = []
    for scene in scenes:
        for mech in scene.mechanisms:
            if mech not in applied:
                applied.append(mech)

    return DreamWorkResult(seeds=seeds, world=world, scenes=scenes, transformations=applied)
