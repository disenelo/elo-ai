"""
faculties/dream/dream_input.py — Dream Input Field + Emotional Parser.

WO-DREAM-ENGINE-001 PHASE 2.

Collects the raw material a dream is made from, before any transformation:

  2a. Dream Input Field  — 13 source types, filtered by cycle content band
  2b. Day Residue        — raw recent experience; NEVER a prompt directly
  2c. Emotional Vector   — 7 dimensions, 0.0-1.0
  2d. Emotional Peaks    — moments where significance spiked (dream seed candidates)
  2e. Memory Gravity     — selection probability, 7 weighted components

This module reads a caller-supplied context mapping. It does not import
server.py, does not call an LLM and does not reach the network — the faculty
that owns those connections passes the material in. Missing sources degrade
to empty rather than raising.

Nothing here is a dream yet. Day residue becomes input for Dream-Work
transformation (dream_work.py), not a prompt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field as _field
from typing import Any, Iterable, Mapping, Sequence

from faculties.dream.sleep_cycle import content_band

# ── 2a. The 13 source types ────────────────────────────────────────────────────
# Order is canonical — the WO filters by source NUMBER, so this order is the
# contract. Each entry: (id, context_key, description).
SOURCE_TYPES: tuple[tuple[int, str, str], ...] = (
    (1,  "recent_conversation",     "Recent conversation — last session content"),
    (2,  "recent_experiences",      "Recent experiences — eLo encounter log"),
    (3,  "memory",                  "Memory — previous sessions"),
    (4,  "project_memory",          "Project memory — what is currently being built"),
    (5,  "wkg",                     "WKG — connected concepts"),
    (6,  "spg",                     "SPG — recently repeated patterns"),
    (7,  "emotional_significance",  "Emotional significance — what carried unusual weight"),
    (8,  "unfinished_threads",      "Unfinished threads — what wasn't resolved"),
    (9,  "novelty",                 "Novelty — what was unusual"),
    (10, "failure",                 "Failure — what didn't behave as expected"),
    (11, "achievement",             "Achievement — what succeeded"),
    (12, "relationship",            "Relationship — what interaction mattered"),
    (13, "embodiment",              "Embodiment — what the current body experienced"),
)

SOURCE_KEYS: tuple[str, ...] = tuple(key for _id, key, _desc in SOURCE_TYPES)

# Cycle content band -> which source ids feed the dream.
# Late cycles also pull cross-era memory (source 3 re-entering from a distance).
BAND_SOURCE_IDS: dict[str, tuple[int, ...]] = {
    "early":  (1, 2, 3, 4),
    "middle": (5, 6, 7, 8),
    "late":   (9, 10, 11, 12, 13, 3),
}

# Sources whose material is, by definition, day residue.
DAY_RESIDUE_IDS: tuple[int, ...] = (1, 2)

# ── 2c. Emotional vector ───────────────────────────────────────────────────────
EMOTION_DIMENSIONS: tuple[str, ...] = (
    "joy", "wonder", "fear", "anger", "sadness", "anxiety", "curiosity",
)

_EMOTION_CUES: dict[str, tuple[str, ...]] = {
    "joy": (
        "joy", "happy", "glad", "delight", "love", "laugh", "brilliant", "great",
        "wonderful", "celebrate", "proud", "pleased", "fun", "warm", "yes",
    ),
    "wonder": (
        "wonder", "awe", "amazing", "beautiful", "vast", "strange", "magic",
        "impossible", "incredible", "marvel", "dream", "float", "glow",
    ),
    "fear": (
        "fear", "afraid", "scared", "terror", "threat", "danger", "dread",
        "panic", "frightened", "dark", "alone",
    ),
    "anger": (
        "anger", "angry", "furious", "rage", "frustrat", "annoy", "irritat",
        "resent", "unfair", "broken", "hate",
    ),
    "sadness": (
        "sad", "grief", "loss", "lost", "lonely", "empty", "miss", "mourn",
        "heavy", "tired", "quiet", "fading", "gone",
    ),
    "anxiety": (
        "anxious", "anxiety", "worry", "worried", "stress", "overwhelm",
        "nervous", "uncertain", "unsure", "pressure", "stuck", "too much",
    ),
    "curiosity": (
        "curious", "wonder why", "question", "explore", "discover", "learn",
        "what if", "how does", "interesting", "notice", "try", "unknown",
    ),
}

# ── 2e. Memory gravity components ──────────────────────────────────────────────
GRAVITY_COMPONENTS: tuple[str, ...] = (
    "significance", "recurrence", "novelty", "emotional_weight",
    "unfinishedness", "relationship_importance", "future_relevance",
)

_UNFINISHED_CUES = (
    "unresolved", "unfinished", "not finished", "still", "todo", "to do",
    "next", "pending", "waiting", "incomplete", "left it", "didn't get",
    "haven't", "need to", "should", "?",
)
_RELATIONSHIP_CUES = (
    "david", "we ", "us ", "together", "you said", "told me", "asked me",
    "with me", "our ",
)
_FUTURE_CUES = (
    "will", "going to", "plan", "next", "soon", "tomorrow", "future",
    "want to", "build", "become",
)
_NOVELTY_CUES = (
    "first time", "never", "new", "unexpected", "surprise", "suddenly",
    "didn't expect", "strange", "unusual",
)

_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = frozenset(
    "a an the and or but if then than that this those these of to in on at "
    "for with from by is are was were be been being it its as i me my we us "
    "our you your he she they them so not no do did does have has had".split()
)


def _words(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS and len(w) > 2]


def _cue_score(text: str, cues: Iterable[str]) -> float:
    """Fraction of cue families present, saturating — 0.0-1.0."""
    low = text.lower()
    hits = sum(1 for c in cues if c in low)
    if hits <= 0:
        return 0.0
    return round(min(1.0, hits / 3.0), 3)


def parse_emotion_vector(texts: str | Sequence[str]) -> dict[str, float]:
    """
    7-dimension emotional vector from raw text. Keyword-derived, no LLM.

    Each dimension saturates at 1.0. Absent emotion = 0.0 (not 0.5) — an
    unemotional input should produce a flat vector, not a warm one.
    """
    if isinstance(texts, str):
        texts = [texts]
    blob = " ".join(str(t) for t in texts if t).lower()
    if not blob.strip():
        return {dim: 0.0 for dim in EMOTION_DIMENSIONS}

    vector: dict[str, float] = {}
    for dim in EMOTION_DIMENSIONS:
        hits = sum(blob.count(cue) for cue in _EMOTION_CUES[dim])
        vector[dim] = round(min(1.0, hits / 3.0), 3)
    return vector


def emotional_intensity(vector: Mapping[str, float]) -> float:
    """
    Magnitude of the emotion vector, normalised so an all-1.0 vector reads 1.0.
    """
    if not vector:
        return 0.0
    total = sum(float(vector.get(d, 0.0)) ** 2 for d in EMOTION_DIMENSIONS)
    return round(min(1.0, (total ** 0.5) / (len(EMOTION_DIMENSIONS) ** 0.5)), 3)


def dominant_emotion(vector: Mapping[str, float]) -> str:
    """Highest-scoring dimension. Ties break in canonical dimension order."""
    best, best_v = EMOTION_DIMENSIONS[0], -1.0
    for dim in EMOTION_DIMENSIONS:
        v = float(vector.get(dim, 0.0))
        if v > best_v:
            best, best_v = dim, v
    return best


# ── Material item ──────────────────────────────────────────────────────────────

@dataclass
class MemoryItem:
    """One piece of dream material, with its gravity components."""
    content: str
    source_id: int
    source_key: str
    emotion_vector: dict[str, float] = _field(default_factory=dict)
    significance: float = 0.0
    recurrence: float = 0.0
    novelty: float = 0.0
    emotional_weight: float = 0.0
    unfinishedness: float = 0.0
    relationship_importance: float = 0.0
    future_relevance: float = 0.0

    @property
    def gravity(self) -> float:
        """
        MEMORY GRAVITY — mean of the 7 components, 0.0-1.0.

        High gravity = higher probability of selection. Not guaranteed
        (dream_work.py samples, it does not take the top N).
        """
        total = sum(float(getattr(self, c, 0.0)) for c in GRAVITY_COMPONENTS)
        return round(total / len(GRAVITY_COMPONENTS), 3)

    def as_dict(self) -> dict:
        d = {
            "content": self.content,
            "source_id": self.source_id,
            "source_key": self.source_key,
            "emotion_vector": self.emotion_vector,
            "gravity": self.gravity,
        }
        d.update({c: round(float(getattr(self, c, 0.0)), 3) for c in GRAVITY_COMPONENTS})
        return d


def _normalise_entry(entry: Any) -> tuple[str, dict]:
    """Accept a plain string or a dict with a content/text field."""
    if isinstance(entry, Mapping):
        for key in ("content", "text", "summary", "title", "claim_text"):
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip(), dict(entry)
        return "", dict(entry)
    return (str(entry).strip(), {}) if entry is not None else ("", {})


def _build_item(content: str, meta: Mapping, source_id: int, source_key: str) -> MemoryItem:
    vec = parse_emotion_vector(content)
    item = MemoryItem(
        content=content,
        source_id=source_id,
        source_key=source_key,
        emotion_vector=vec,
        emotional_weight=emotional_intensity(vec),
        unfinishedness=_cue_score(content, _UNFINISHED_CUES),
        relationship_importance=_cue_score(content, _RELATIONSHIP_CUES),
        future_relevance=_cue_score(content, _FUTURE_CUES),
        novelty=_cue_score(content, _NOVELTY_CUES),
    )
    # Caller-supplied metadata overrides anything derived.
    for comp in GRAVITY_COMPONENTS:
        if comp in meta:
            try:
                setattr(item, comp, max(0.0, min(1.0, float(meta[comp]))))
            except (TypeError, ValueError):
                pass
    if "significance" not in meta:
        # Derived significance: emotional weight carries it when nothing else does.
        item.significance = round(
            min(1.0, 0.6 * item.emotional_weight + 0.4 * item.unfinishedness), 3
        )
    return item


def _apply_recurrence(items: Sequence[MemoryItem]) -> None:
    """
    Recurrence is observed across the whole field, not declared per item.
    A term repeated across several items lifts every item that carries it.
    """
    counts: dict[str, int] = {}
    per_item: list[set[str]] = []
    for item in items:
        terms = set(_words(item.content))
        per_item.append(terms)
        for term in terms:
            counts[term] = counts.get(term, 0) + 1

    for item, terms in zip(items, per_item):
        if not terms:
            continue
        repeated = [counts[t] for t in terms if counts[t] > 1]
        if not repeated:
            continue
        # Saturates: a term seen in 4+ items is full recurrence.
        peak = max(repeated)
        item.recurrence = round(min(1.0, (peak - 1) / 3.0), 3)


# ── 2d. Emotional peaks ────────────────────────────────────────────────────────

def find_emotional_peaks(
    history: Sequence[Any],
    *,
    threshold: float = 0.5,
    limit: int = 8,
) -> list[dict]:
    """
    Scan session history for moments where significance spiked.

    A peak is a candidate Dream Seed. Peaks do NOT appear literally in the
    dream — dream_work.py transforms them first.

    history — strings, or dicts that may carry timestamp/content plus any
    explicit emotion scores. Explicit scores win over derived ones.
    """
    peaks: list[dict] = []
    for entry in history or []:
        content, meta = _normalise_entry(entry)
        if not content:
            continue
        vec = parse_emotion_vector(content)
        significance = meta.get("significance")
        if significance is None:
            significance = round(
                min(1.0, 0.7 * emotional_intensity(vec)
                    + 0.3 * _cue_score(content, _NOVELTY_CUES)), 3
            )
        try:
            significance = max(0.0, min(1.0, float(significance)))
        except (TypeError, ValueError):
            continue
        if significance < threshold:
            continue

        peak = {
            "timestamp": meta.get("timestamp", ""),
            "content": content,
            "significance": significance,
        }
        peak.update({d: vec[d] for d in EMOTION_DIMENSIONS})
        for extra in ("surprise", "achievement"):
            if extra in meta:
                peak[extra] = meta[extra]
        peaks.append(peak)

    peaks.sort(key=lambda p: p["significance"], reverse=True)
    return peaks[:limit]


# ── The field ──────────────────────────────────────────────────────────────────

@dataclass
class DreamInputField:
    """Everything a single dream cycle has to work with."""
    cycle_number: int
    content_band: str
    source_ids: tuple[int, ...]
    items: list[MemoryItem] = _field(default_factory=list)
    day_residue: list[str] = _field(default_factory=list)
    emotion_vector: dict[str, float] = _field(default_factory=dict)
    emotional_intensity: float = 0.0
    significance: float = 0.0
    novelty: float = 0.0
    unresolvedness: float = 0.0
    peaks: list[dict] = _field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.items

    @property
    def dominant_emotion(self) -> str:
        return dominant_emotion(self.emotion_vector)

    def by_gravity(self) -> list[MemoryItem]:
        """Items ranked by memory gravity, heaviest first."""
        return sorted(self.items, key=lambda i: i.gravity, reverse=True)

    def as_dict(self) -> dict:
        return {
            "cycle_number": self.cycle_number,
            "content_band": self.content_band,
            "source_ids": list(self.source_ids),
            "items": [i.as_dict() for i in self.items],
            "day_residue": list(self.day_residue),
            "emotion_vector": self.emotion_vector,
            "emotional_intensity": self.emotional_intensity,
            "significance": self.significance,
            "novelty": self.novelty,
            "unresolvedness": self.unresolvedness,
            "dominant_emotion": self.dominant_emotion,
            "peaks": list(self.peaks),
        }


def day_residue(context: Mapping[str, Any]) -> list[str]:
    """
    2b. Raw material from recent experience.

    Does NOT become a prompt directly — it is input for Dream-Work
    transformation. Returned raw and untransformed on purpose.
    """
    residue: list[str] = []
    for source_id, key, _desc in SOURCE_TYPES:
        if source_id not in DAY_RESIDUE_IDS:
            continue
        for entry in context.get(key) or []:
            content, _meta = _normalise_entry(entry)
            if content:
                residue.append(content)
    return residue


def collect(
    cycle_number: int,
    context: Mapping[str, Any] | None = None,
    *,
    history: Sequence[Any] | None = None,
) -> DreamInputField:
    """
    Build the Dream Input Field for one cycle.

    cycle_number — 1-5. Selects the content band, which selects the sources.
    context      — mapping of the 13 SOURCE_KEYS to lists of strings or dicts.
                   Unknown keys are ignored; missing keys degrade to empty.
    history      — session history scanned for emotional peaks. Falls back to
                   the day residue when not supplied.
    """
    context = dict(context or {})
    band = content_band(cycle_number)
    source_ids = BAND_SOURCE_IDS[band]
    id_to_key = {sid: key for sid, key, _d in SOURCE_TYPES}

    items: list[MemoryItem] = []
    for source_id in source_ids:
        key = id_to_key[source_id]
        for entry in context.get(key) or []:
            content, meta = _normalise_entry(entry)
            if content:
                items.append(_build_item(content, meta, source_id, key))

    _apply_recurrence(items)

    residue = day_residue(context)
    peaks = find_emotional_peaks(history if history is not None else residue)

    all_text = [i.content for i in items]
    vector = parse_emotion_vector(all_text)
    count = max(1, len(items))

    return DreamInputField(
        cycle_number=cycle_number,
        content_band=band,
        source_ids=source_ids,
        items=items,
        day_residue=residue,
        emotion_vector=vector,
        emotional_intensity=emotional_intensity(vector),
        significance=round(sum(i.significance for i in items) / count, 3),
        novelty=round(sum(i.novelty for i in items) / count, 3),
        unresolvedness=round(sum(i.unfinishedness for i in items) / count, 3),
        peaks=peaks,
    )
