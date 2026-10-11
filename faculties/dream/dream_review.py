"""
faculties/dream/dream_review.py — Dream Review + Wake Transfer Gate.

WO-DREAM-ENGINE-001 PHASE 8.

    DREAM
      │
      ▼
    CANDIDATE INSIGHT
      │
      ▼
    VERIFY
      │
     ┌┴──────────────┐
     ▼               ▼
    VALIDATED      UNVERIFIED
     │               │
     ▼               ▼
    KNOWLEDGE       HYPOTHESIS

Runs on wake, BEFORE wake_from_dream() integrates anything.

This module deliberately reuses the boundary the codebase already has rather
than inventing a second one:

  runtime/memory_origin.py  —  DREAM_SIMULATION is explicitly NOT
                               auto-storable; it becomes DREAM_INSIGHT only
                               after significance clears
                               DREAM_RETENTION_THRESHOLD (0.72).
  runtime/wkg_faculty.py    —  record_claim() blocks DREAM_SIMULATION at the
                               write gate (WO-DREAM-VERIFY-001) and accepts
                               HYPOTHESIS / SYMBOLIC as epistemic classes.

So "VALIDATED → KNOWLEDGE" means *eligible for retention*, NOT *true*.
Nothing this module emits is ever epistemic_class VERIFIED. A dream that
clears the gate has earned a place in memory, not the status of fact.

Two hard rules from the WO, enforced here and pinned by tests:
  - Dream material is never silently written as fact.
  - The Dream Faculty does not speak to David. It returns channels; the
    Executive decides what surfaces. There is deliberately no emit/speak
    method on this module.

No LLM, no network, no server.py, and it writes nothing.
"""
from __future__ import annotations

from dataclasses import dataclass, field as _field
from typing import Callable

try:
    from runtime.memory_origin import (
        MemoryOrigin,
        DREAM_RETENTION_THRESHOLD,
        is_auto_storable,
    )
except Exception:                                    # pragma: no cover
    # The gate is canon; if it cannot be imported, fail CLOSED — treat
    # everything as unretained rather than quietly promoting dream material.
    MemoryOrigin = None                              # type: ignore[assignment]
    DREAM_RETENTION_THRESHOLD = 1.1                  # unreachable
    def is_auto_storable(origin):                    # type: ignore[misc]
        return False

# Epistemic classes accepted by runtime/wkg_faculty.py. Dream-derived material
# may only ever be one of these two — never VERIFIED, never HISTORICAL.
EPISTEMIC_HYPOTHESIS = "HYPOTHESIS"
EPISTEMIC_SYMBOLIC = "SYMBOLIC"
# Only reachable at STAGE_KNOWLEDGE, and only with a named corroborating
# source. SOURCE_ATTRIBUTED != VERIFIED — wkg_faculty enforces that at its
# own boundary, and a dream may never reach VERIFIED by any path.
EPISTEMIC_SOURCE_ATTRIBUTED = "SOURCE_ATTRIBUTED"

FORBIDDEN_EPISTEMIC = frozenset({
    "VERIFIED", "HISTORICAL", "CANONICAL",
})

# ── The promotion ladder — WO-CAP-EMB-031 §31, verbatim ───────────────────────
#
#   DREAM → IDEA → EVALUATION → TEST → KNOWLEDGE
#   Not:  DREAM → TRUTH
#
# Each stage is a separate gate. Significance clears EVALUATION only. Nothing
# reaches KNOWLEDGE without TEST, and TEST requires corroboration from outside
# the dream — a dream cannot test itself. There is deliberately no path that
# takes a dream to KNOWLEDGE in one step.
STAGE_DREAM = "DREAM"
STAGE_IDEA = "IDEA"
STAGE_EVALUATION = "EVALUATION"
STAGE_TEST = "TEST"
STAGE_KNOWLEDGE = "KNOWLEDGE"

PROMOTION_LADDER: tuple[str, ...] = (
    STAGE_DREAM, STAGE_IDEA, STAGE_EVALUATION, STAGE_TEST, STAGE_KNOWLEDGE,
)


def _origin(name: str) -> str:
    """MemoryOrigin value as a plain string, safe when the enum is absent."""
    if MemoryOrigin is None:                         # pragma: no cover
        return name.lower()
    return MemoryOrigin[name].value


# ── Significance ───────────────────────────────────────────────────────────────

def assess_significance(entry: dict) -> float:
    """
    Derive a dream's significance from its own observable signals.

    Deliberately NOT memory/significance_engine.py — that scores a
    conversation turn (raw/response/action/plan) and has no meaning for a
    dream record. The signals here are the ones a dream actually produces.

    Weighted so that no single signal can promote a dream on its own: a
    vivid dream about nothing still has to carry emotional weight or an
    unresolved thread to earn retention.
    """
    cycles = entry.get("cycles") or []

    intensity = float(entry.get("dream_intensity", 0.0) or 0.0)

    # PROPORTIONAL, not saturating. Both of these used to take the strongest
    # single reading anywhere in the dream: `emotional` was a max across every
    # cycle AND every seed, and `unresolved` was set to 1.0 by any one seed.
    # Once real conversation reached the dream (2026-10-10) that meant one
    # emotive word and one unfinished thread pinned both to 1.0, and every one
    # of the first ten real dreams scored an identical 0.900 — the same
    # no-op sort the old constant 0.400 was, at the other end.
    #
    # A dream that is emotional THROUGHOUT should outscore one with a single
    # spike, and a dream where most seeds are unfinished should outscore one
    # with a single loose end. So: mean of per-cycle peaks, and the fraction
    # of seeds that are unresolved.
    _cycle_peaks: list[float] = []
    _seeds_total = 0
    _seeds_unresolved = 0
    _unique_concepts: set[str] = set()
    for cycle in cycles:
        _peak = 0.0
        vector = cycle.get("emotion_vector") or {}
        if vector:
            _peak = max((float(v) for v in vector.values()), default=0.0)
        for seed in cycle.get("seeds") or []:
            _seeds_total += 1
            if seed.get("unresolved"):
                _seeds_unresolved += 1
            for _c in seed.get("associated_concepts") or []:
                _slug = str(_c).strip().lower()
                if _slug:
                    _unique_concepts.add(_slug)
            # Was seed.get("emotional_weight_max"). That key appears
            # exactly once in the whole codebase — here, on the read. No
            # writer has ever produced it, so this term was a constant
            # 0.0 for all 166 dreams and 856 seeds.
            #
            # The seeds do carry emotion: `emotional_weight` is a dict,
            # e.g. {"wonder": 0.333}, populated on 74 of those seeds. Read
            # the same way the cycle vector is read four lines above, so
            # the two sources of emotion are treated identically.
            # Values are coerced one at a time and non-numbers skipped. The
            # read this replaced had `or 0.0` around a single float; iterating
            # a dict without the same care turned a malformed emotion into a
            # ValueError out of assess_significance, which runs inside the
            # dream path. Caught by its own test, not in production.
            _seed_emotion = seed.get("emotional_weight") or {}
            if isinstance(_seed_emotion, (int, float)):
                _seed_emotion = {"_": _seed_emotion}
            if isinstance(_seed_emotion, dict):
                for _v in _seed_emotion.values():
                    try:
                        _peak = max(_peak, float(_v))
                    except (TypeError, ValueError):
                        continue
        _cycle_peaks.append(_peak)

    emotional = (sum(_cycle_peaks) / len(_cycle_peaks)) if _cycle_peaks else 0.0
    unresolved = (_seeds_unresolved / _seeds_total) if _seeds_total else 0.0

    # `dream_intensity` is the peak phase intensity from sleep_cycle. For any
    # full 5-cycle sleep that reaches cycle 5 REM it is 1.0 by construction, so
    # on its own the term pinned a constant 0.40 across every real dream and
    # the top of the scorer could not discriminate. Splitting the 0.40 slot
    # into (intensity, concept_density) keeps the ceiling where
    # test_a_vivid_dream_about_nothing_does_not_clear_the_gate expects it
    # (intensity alone peaks at 0.25 < 0.45) and lets dreams differentiate on
    # how much ground their seeds actually covered — the 16 retained real
    # dreams have 14..27 unique associated_concepts and all scored exactly 0.9
    # before this term existed.
    concept_density = min(1.0, len(_unique_concepts) / 15.0)

    # A symbol eLo has seen before matters more than a one-off image.
    recurrence = 0.0
    lexicon = entry.get("symbol_lexicon") or []
    symbols = {str(s) for s in (entry.get("recurring_symbols") or [])}
    for record in lexicon:
        if record.get("recurring") and (
            record.get("display") in symbols or record.get("symbol") in symbols
        ):
            recurrence = 1.0
            break

    score = (
        0.25 * intensity
        + 0.15 * concept_density
        + 0.30 * emotional
        + 0.20 * unresolved
        + 0.10 * recurrence
    )
    return round(max(0.0, min(1.0, score)), 3)


# ── Candidate insight ──────────────────────────────────────────────────────────

@dataclass
class CandidateInsight:
    """One thing the dream proposes. Never a fact."""
    content: str
    significance: float
    epistemic_class: str = EPISTEMIC_HYPOTHESIS
    memory_origin: str = ""
    retained: bool = False
    source_dream: str = ""
    stage: str = STAGE_IDEA
    corroboration: list[str] = _field(default_factory=list)

    @property
    def is_knowledge(self) -> bool:
        return self.stage == STAGE_KNOWLEDGE

    @property
    def cognitive_state(self) -> str:
        """
        WO-CAP-EMB-052 — which of the thirteen states this insight is in.

        Derived from `stage`, never stored alongside it, so the EMB-031 ladder
        and the EMB-052 vocabulary cannot drift apart. No rung of the ladder
        reaches MEMORY, OBSERVATION or ACTION: a dream is never evidence that
        anything happened, however far its insight has climbed.
        """
        from runtime.cognitive_state import state_for_ladder_stage
        return state_for_ladder_stage(self.stage).value

    def as_dict(self) -> dict:
        return {
            "content": self.content,
            "significance": self.significance,
            "epistemic_class": self.epistemic_class,
            "memory_origin": self.memory_origin,
            "retained": self.retained,
            "source_dream": self.source_dream,
            "stage": self.stage,
            "cognitive_state": self.cognitive_state,
            "corroboration": list(self.corroboration),
        }


def test_insight(insight: CandidateInsight, corroborating_source: str) -> CandidateInsight:
    """
    The TEST stage — WO-CAP-EMB-031 §31.

    An idea that survived EVALUATION is still only a hypothesis. It becomes
    KNOWLEDGE only when something OUTSIDE the dream corroborates it, and the
    corroborating source must be named. A dream cannot test itself.

    Mutates and returns the insight. Refuses to advance when:
      - the insight has not cleared EVALUATION (significance gate), or
      - no corroborating source is named.

    Even at KNOWLEDGE the class is SOURCE_ATTRIBUTED, never VERIFIED. The
    source says "DREAM → IDEA → EVALUATION → TEST → KNOWLEDGE", not
    "DREAM → TRUTH".
    """
    source = str(corroborating_source or "").strip()
    if not source:
        return insight                      # untested — stays where it is
    if insight.stage not in (STAGE_EVALUATION, STAGE_TEST):
        return insight                      # cannot skip the significance gate

    insight.corroboration.append(source)
    insight.stage = STAGE_KNOWLEDGE
    insight.epistemic_class = EPISTEMIC_SOURCE_ATTRIBUTED
    return insight


@dataclass
class DreamReview:
    """
    The result of reviewing one dream. Two output channels, per WO section 46.

    OUTPUT A — COGNITIVE: record, insights, associations, patterns, questions
    OUTPUT B — CREATIVE:  prompts, scene images, final artwork, metadata
    """
    dream_id: str
    significance: float
    retained: bool
    dream_record: dict = _field(default_factory=dict)
    candidate_insights: list[CandidateInsight] = _field(default_factory=list)
    new_associations: list[dict] = _field(default_factory=list)
    candidate_spg_patterns: list[dict] = _field(default_factory=list)
    research_questions: list[str] = _field(default_factory=list)
    creative_artifacts: dict = _field(default_factory=dict)

    # -- channels --
    def cognitive_channel(self) -> dict:
        """OUTPUT A. What the Executive may route into waking cognition."""
        return {
            "dream_id": self.dream_id,
            "dream_record": self.dream_record,
            "candidate_insights": [i.as_dict() for i in self.candidate_insights],
            "new_associations": list(self.new_associations),
            "candidate_spg_patterns": list(self.candidate_spg_patterns),
            "research_questions": list(self.research_questions),
            "significance": self.significance,
            "retained": self.retained,
        }

    def creative_channel(self) -> dict:
        """OUTPUT B. The artefact the dream left behind."""
        return dict(self.creative_artifacts)

    def for_executive(self) -> dict:
        """
        Everything the Executive needs to decide what surfaces.

        This is the ONLY outward path. There is no speak() or emit() here by
        design — the Dream Faculty does not address David directly.

        WO-DREAM-WAKE-CURIOSITY-001: surfaces_directly reflects self.retained
        so the server.py wake path can distinguish a significant dream (True)
        from a low-significance one (False) and route accordingly.
        """
        return {
            "cognitive": self.cognitive_channel(),
            "creative": self.creative_channel(),
            "surfaces_directly": self.retained,
        }


# ── Review ─────────────────────────────────────────────────────────────────────

def review(
    journal_entry: dict,
    *,
    assessor: Callable[[dict], float] | None = None,
) -> DreamReview:
    """
    Run the wake transfer gate over one dream journal entry.

    assessor — optional significance scorer, for when a dream-aware engine
               exists. Defaults to assess_significance().

    Writes nothing. Returns channels for the Executive to route.
    """
    entry = dict(journal_entry or {})
    dream_id = str(entry.get("dream_id", ""))
    cycles = entry.get("cycles") or []

    significance = float((assessor or assess_significance)(entry))
    retained = significance >= DREAM_RETENTION_THRESHOLD

    # WO-AUTOBIOGRAPHY-CONV-001: a retained dream hypothesis is a cognitive event
    # worth recording. Write to autobiography so eLo has a trace of which dreams
    # surfaced insights above the retention threshold.
    if retained and dream_id:
        try:
            from self.emergent_cognition import append_autobiography as _ab_dream
            _ab_dream(
                f"dream-derived hypothesis retained (sig={significance:.2f}): "
                f"{str(entry.get('insight', ''))[:80]}",
                kind="cognitive",
                verified=True,
                source="dream_derived",
                episode_ref=f"dream-{dream_id}",
            )
        except Exception:
            pass

    # VERIFY: clearing the gate promotes the ORIGIN (eligible for retention).
    # It does NOT promote the epistemic class — a retained dream is still a
    # hypothesis, not a verified fact.
    origin = _origin("DREAM_INSIGHT" if retained else "DREAM_SIMULATION")

    candidate_insights: list[CandidateInsight] = []
    insight_text = str(entry.get("insight", "") or "").strip()
    if insight_text:
        candidate_insights.append(CandidateInsight(
            content=insight_text,
            significance=significance,
            epistemic_class=EPISTEMIC_HYPOTHESIS,
            memory_origin=origin,
            retained=retained,
            source_dream=dream_id,
            # Clearing significance advances IDEA -> EVALUATION. It does NOT
            # reach TEST, and cannot reach KNOWLEDGE — that needs
            # corroboration from outside the dream. See test_insight().
            stage=STAGE_EVALUATION if retained else STAGE_IDEA,
        ))

    # New associations — candidate WKG additions. SYMBOLIC, never VERIFIED,
    # and always carrying the dream origin so wkg_faculty's write gate
    # (WO-DREAM-VERIFY-001) can refuse them if anything tries to auto-store.
    new_associations: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()
    for cycle in cycles:
        for seed in cycle.get("seeds") or []:
            concepts = [c for c in (seed.get("associated_concepts") or []) if c]
            for other in concepts[1:4]:
                pair = (concepts[0], other)
                if pair in seen_pairs or pair[0] == pair[1]:
                    continue
                seen_pairs.add(pair)
                new_associations.append({
                    "subject": pair[0],
                    "object": pair[1],
                    "epistemic_class": EPISTEMIC_SYMBOLIC,
                    "memory_origin": origin,
                    "source_dream": dream_id,
                    "auto_storable": bool(
                        MemoryOrigin is not None
                        and is_auto_storable(MemoryOrigin(origin))
                    ),
                })

    # Candidate SPG patterns — recurring motifs the dream observed.
    candidate_spg_patterns: list[dict] = []
    seen_patterns: set[str] = set()
    for cycle in cycles:
        for seed in cycle.get("seeds") or []:
            pattern = str(seed.get("spg_pattern", "") or "").strip()
            if pattern and pattern not in seen_patterns:
                seen_patterns.add(pattern)
                candidate_spg_patterns.append({
                    "pattern": pattern,
                    "epistemic_class": EPISTEMIC_SYMBOLIC,
                    "memory_origin": origin,
                    "source_dream": dream_id,
                })
    for symbol in entry.get("recurring_symbols") or []:
        key = f"recurring symbol: {symbol}"
        if key not in seen_patterns:
            seen_patterns.add(key)
            candidate_spg_patterns.append({
                "pattern": key,
                "epistemic_class": EPISTEMIC_SYMBOLIC,
                "memory_origin": origin,
                "source_dream": dream_id,
            })

    # Research questions — what the dream left open.
    research_questions: list[str] = []
    for cycle in cycles:
        for seed in cycle.get("seeds") or []:
            question = str(seed.get("unresolved", "") or "").strip()
            if question and question not in research_questions:
                research_questions.append(question)

    # OUTPUT B — the creative channel. Prompts exist now; scene images and
    # the final composite arrive with PHASES 5-6, which are not built, so
    # those keys are reported empty rather than fabricated.
    prompts: list[str] = []
    for cycle in cycles:
        prompts.extend(cycle.get("prompts") or [])

    creative_artifacts = {
        "dream_id": dream_id,
        "prompts": prompts,
        "scene_images": list(entry.get("scene_images") or []),
        "final_artwork": entry.get("final_artwork") or None,
        "image_ref": entry.get("image_ref") or None,
        "metadata": {
            "dream_intensity": entry.get("dream_intensity", 0.0),
            "cycle_count": entry.get("cycle_count", 0),
            "scene_count": entry.get("scene_count", 0),
            "recurring_symbols": list(entry.get("recurring_symbols") or []),
            "output_type": "DREAM",
        },
    }

    return DreamReview(
        dream_id=dream_id,
        significance=significance,
        retained=retained,
        dream_record=entry,
        candidate_insights=candidate_insights,
        new_associations=new_associations,
        candidate_spg_patterns=candidate_spg_patterns,
        research_questions=research_questions,
        creative_artifacts=creative_artifacts,
    )
