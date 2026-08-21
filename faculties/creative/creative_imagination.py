"""
faculties/creative/creative_imagination.py — Vol XXVI Ch.1 + Ch.3

Divergent phase, symbolic synthesis, and evaluation. Never selects — the Executive
selects (Ch.1 §1.4, ADR-Exec-002 Single Cognitive Truth). This module proposes and
scores; the caller passes an executive selector to converge.

Reuses the Dream Faculty's Symbol Engine (Vol IX Ch.2) — one symbolic vocabulary,
never forked (Ch.1 §1.5). Every candidate carries epistemic_status="imagined"
(Ch.1 §1.1.2 Verified Speech).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

from faculties.dream.symbol_engine import SYMBOLS, map_to_symbols


@dataclass
class CreativeCandidate:
    concept: str
    metaphor: str
    bridge_symbols: list[str]
    spanned_axes: list[str]
    seeds_used: list[str]
    domain: str = "story"
    epistemic_status: str = "imagined"
    rationale: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CreativeScore:
    originality:        float
    emotional_meaning:  float
    identity_alignment: float
    taste_alignment:    float
    future_potential:   float
    coherence:          float
    weighted_total:     float
    rationale:          str
    epistemic_status:   str = "imagined"

    def to_dict(self) -> dict:
        return asdict(self)


# ── Symbolic synthesis ────────────────────────────────────────────────────────

def synthesise(concept_a: str, concept_b: str, goal: str) -> dict:
    """Fuse two concepts through the shared Symbol Engine (Ch.1 §1.5).

    Returns {bridge, metaphor, symbols} — never asserts, always imagined.
    """
    sym_a = _resolve_symbol(concept_a)
    sym_b = _resolve_symbol(concept_b)

    bridge = _find_bridge(sym_a, sym_b)
    metaphor = _compose_metaphor(sym_a, sym_b, bridge, goal)
    return {
        "bridge": bridge,
        "metaphor": metaphor,
        "symbols": [sym_a["name"], sym_b["name"]],
        "epistemic_status": "imagined",
    }


def _resolve_symbol(concept: str) -> dict:
    low = (concept or "").lower()
    for keyword, (name, meaning) in SYMBOLS.items():
        if keyword in low:
            return {"name": name, "meaning": meaning, "concept": concept}
    return {"name": concept.title() or "Presence", "meaning": "an unmapped concept", "concept": concept}


def _find_bridge(sym_a: dict, sym_b: dict) -> str:
    """A bridge symbol names the shared frame. When both meanings mention a shared word
    it becomes the bridge; otherwise 'presence' — eLo is always the constant (SYMBOLS['elo'])."""
    import re
    def _tokens(s: str) -> set[str]:
        return {t for t in re.findall(r"[a-z]{3,}", s.lower())}
    shared = _tokens(sym_a["meaning"]) & _tokens(sym_b["meaning"])
    shared -= {"the", "and", "for", "from", "with", "into", "onto"}
    if shared:
        return sorted(shared)[0]
    return "presence"


def _compose_metaphor(sym_a: dict, sym_b: dict, bridge: str, goal: str) -> str:
    """Compose a new metaphor from the bridge (Ch.1 §1.5 step 3). 5-question expansion is
    left to downstream production; this returns the seed metaphor David can look at."""
    return f"{sym_a['name']} in a {sym_b['name'].lower()} — {bridge} for '{goal}'"


# ── Divergent phase ───────────────────────────────────────────────────────────

_DEFAULT_AXES = ["tone", "form", "palette", "mechanic", "pacing", "voice"]


def diverge(
    goal: str,
    seeds: list[str],
    *,
    breadth_budget: int = 6,
    domain: str = "story",
    spanned_axes: Optional[list[str]] = None,
) -> list[CreativeCandidate]:
    """Ch.1 §1.3 — bounded, diverse candidate generation.

    No spark → no divergence (silence is valid, Vol V Ch.9 failure mode).
    """
    if not seeds or not goal:
        return []

    axes = spanned_axes or _DEFAULT_AXES
    candidates: list[CreativeCandidate] = []

    # Pair each seed with the next (wrap-around) → distinct fusions along declared axes.
    for i in range(min(breadth_budget, max(len(seeds), 2))):
        a = seeds[i % len(seeds)]
        b = seeds[(i + 1) % len(seeds)]
        synth = synthesise(a, b, goal)
        axis = axes[i % len(axes)]
        candidates.append(CreativeCandidate(
            concept=f"{a} × {b}",
            metaphor=synth["metaphor"],
            bridge_symbols=synth["symbols"],
            spanned_axes=[axis],
            seeds_used=[a, b],
            domain=domain,
            rationale=f"fused via {synth['bridge']} on axis={axis}",
        ))

    # Ensure diversity: distinct spanned axes across the set (Ch.1 §1.3 diversity rule).
    seen_axes = set()
    unique = []
    for c in candidates:
        key = tuple(c.spanned_axes)
        if key not in seen_axes:
            unique.append(c)
            seen_axes.add(key)
    return unique[:breadth_budget] or candidates[:1]


# ── Evaluation (Ch.3 §3.2) ────────────────────────────────────────────────────

_TERM_WEIGHTS = {
    "originality":        0.18,
    "emotional_meaning":  0.15,
    "identity_alignment": 0.22,   # floor-enforced separately; carried as weight when above the floor
    "taste_alignment":    0.15,
    "future_potential":   0.15,
    "coherence":          0.15,
}


def evaluate(
    candidate: CreativeCandidate,
    goal: str,
    *,
    identity_terms: Optional[list[str]] = None,
    aesthetic_profile: Optional[dict] = None,
    canon_terms: Optional[list[str]] = None,
) -> CreativeScore:
    """Ch.3 §3.2 six-term evaluator. identity_alignment is a floor in convergence,
    not a maximised term (Ch.3 §3.2 rule); we still score it here for surfacing."""
    text = f"{candidate.concept} {candidate.metaphor}".lower()

    # Originality: distance from goal words + presence of bridge across axes
    goal_words = {w for w in goal.lower().split() if len(w) > 3}
    cand_words = {w for w in text.split() if len(w) > 3}
    new_words = cand_words - goal_words
    originality = min(1.0, 0.30 + 0.10 * len(new_words))

    # Emotional meaning: any evocative bridge word ("safety", "growth", "flow"...) scores
    evocative = {"safety", "growth", "flow", "transformation", "understanding",
                 "connection", "aspiration", "grounding", "orientation", "presence"}
    emotional_meaning = 0.35 + 0.15 * sum(1 for w in text.split() if w in evocative)
    emotional_meaning = min(1.0, emotional_meaning)

    # Identity alignment: presence of identity terms
    id_terms = [t.lower() for t in (identity_terms or ["elo", "presence", "moon", "garden"])]
    hits = sum(1 for t in id_terms if t in text)
    identity_alignment = min(1.0, 0.30 + 0.20 * hits)

    # Taste alignment: from stated_direction in profile; silent → None-flagged (Ch.3 §3.4)
    if aesthetic_profile and aesthetic_profile.get("stated_direction"):
        prefs = [p.lower() for p in aesthetic_profile["stated_direction"]]
        taste_hits = sum(1 for p in prefs if p in text)
        taste_alignment = min(1.0, 0.40 + 0.15 * taste_hits)
        taste_source = "stated"
    else:
        taste_alignment = 0.0  # silent → excluded from ranking (ST-1: Silence explored, not fabricated)
        taste_source = "silent:explore_within_canon"

    # Future potential: number of axes + bridge symbols opens further work
    future_potential = min(1.0, 0.30 + 0.15 * len(candidate.bridge_symbols)
                            + 0.10 * len(candidate.spanned_axes))

    # Coherence: canon term presence
    canon = [t.lower() for t in (canon_terms or ["elo", "planet", "book"])]
    coh_hits = sum(1 for t in canon if t in text)
    coherence = min(1.0, 0.40 + 0.15 * coh_hits)

    scores = {
        "originality":        round(originality, 3),
        "emotional_meaning":  round(emotional_meaning, 3),
        "identity_alignment": round(identity_alignment, 3),
        "taste_alignment":    round(taste_alignment, 3),
        "future_potential":   round(future_potential, 3),
        "coherence":          round(coherence, 3),
    }
    weighted = sum(scores[k] * _TERM_WEIGHTS[k] for k in _TERM_WEIGHTS)
    rationale = (f"orig={scores['originality']} · meaning={scores['emotional_meaning']} · "
                 f"identity={scores['identity_alignment']} · taste={scores['taste_alignment']} "
                 f"({taste_source}) · potential={scores['future_potential']} · "
                 f"coherence={scores['coherence']}")
    return CreativeScore(
        originality=scores["originality"],
        emotional_meaning=scores["emotional_meaning"],
        identity_alignment=scores["identity_alignment"],
        taste_alignment=scores["taste_alignment"],
        future_potential=scores["future_potential"],
        coherence=scores["coherence"],
        weighted_total=round(weighted, 3),
        rationale=rationale,
    )


# ── Convergence: Executive selects (Ch.1 §1.4) ────────────────────────────────

IDENTITY_FLOOR = 0.45  # below this → identity filter rejects (Ch.3 §3.2 "floor, not weight")


def executive_select(
    candidates: list[CreativeCandidate],
    scores: list[CreativeScore],
    *,
    identity_floor: float = IDENTITY_FLOOR,
) -> Optional[dict]:
    """The reference Executive-selection routine used when the caller wants a default.
    Callers may pass their own selector to run_creative_loop — this is the seam that
    goes RED when disconnected.

    Single Cognitive Truth (ADR-Exec-002): exactly one selection, from one frozen set.
    Identity filter is a floor. Selection may be 'none' (Ch.1 §1.4 rule: no weak creation).
    """
    if not candidates or not scores or len(candidates) != len(scores):
        return None

    ranked: list[tuple[CreativeCandidate, CreativeScore]] = []
    for c, s in zip(candidates, scores):
        if s.identity_alignment < identity_floor:
            continue
        ranked.append((c, s))
    if not ranked:
        return None
    ranked.sort(key=lambda pair: pair[1].weighted_total, reverse=True)
    winner_c, winner_s = ranked[0]
    return {
        "candidate": winner_c.to_dict(),
        "score":     winner_s.to_dict(),
        "runners_up": [c.to_dict() for c, _ in ranked[1:]],
    }


# ── Full creative loop (spark → memory) ───────────────────────────────────────

def run_creative_loop(
    spark: str,
    goal: str,
    seeds: list[str],
    executive_select_fn: Optional[Callable[[list[CreativeCandidate], list[CreativeScore]], Optional[dict]]],
    *,
    breadth_budget: int = 6,
    domain: str = "story",
    aesthetic_profile: Optional[dict] = None,
    identity_terms: Optional[list[str]] = None,
    canon_terms: Optional[list[str]] = None,
    memory_threshold: float = 0.5,
) -> dict:
    """Vol XXVI IT-1 — spark → diverge → evaluate → Executive selects → Ch.5 significance
    → high-significance routes to memory. Executive-selection is the wire; passing
    executive_select_fn=None cuts it and the loop returns no selection (test goes RED).

    Args:
        spark: the seed event that triggered creation (user input / drop-file content).
        goal:  creative intent (from Intent Engine / drop-file title).
        seeds: source concepts to fuse.
        executive_select_fn: Executive selector (Ch.1 §1.4). None → wire cut.
        aesthetic_profile: David's direction (Ch.3 §3.4). Silent → explore_within_canon.
        memory_threshold: Ch.5 overall significance floor for memory routing.

    Returns:
        {
          "selected": dict | None,          # Executive's choice — the observable
          "significance": dict | None,      # Ch.5 sig profile if selected
          "memory_ref": str | None,         # populated if overall >= memory_threshold
          "candidates": [...],              # runners-up (Ch.1 §1.4: kept, not discarded)
          "scores": [...],
          "reason": str,                    # human-readable state note
        }
    """
    candidates = diverge(goal, seeds, breadth_budget=breadth_budget, domain=domain)
    if not candidates:
        return {"selected": None, "significance": None, "memory_ref": None,
                "candidates": [], "scores": [], "reason": "no_spark_or_goal"}

    scores = [evaluate(c, goal, identity_terms=identity_terms,
                       aesthetic_profile=aesthetic_profile, canon_terms=canon_terms)
              for c in candidates]

    if executive_select_fn is None:
        return {"selected": None, "significance": None, "memory_ref": None,
                "candidates": [c.to_dict() for c in candidates],
                "scores":     [s.to_dict() for s in scores],
                "reason":     "executive_disconnected"}

    selection = executive_select_fn(candidates, scores)
    if selection is None:
        return {"selected": None, "significance": None, "memory_ref": None,
                "candidates": [c.to_dict() for c in candidates],
                "scores":     [s.to_dict() for s in scores],
                "reason":     "no_candidate_cleared_floor"}

    from memory.significance_engine import evaluate as significance_evaluate
    sig = significance_evaluate(
        raw=spark,
        response=selection["candidate"]["metaphor"],
        action="build",
        plan=None,
        state={"last_topics": [], "session_anchor": {"open_loops": []}},
    )

    memory_ref = None
    if sig.get("overall", 0.0) >= memory_threshold:
        memory_ref = _route_to_creative_memory(selection, sig, spark, goal, domain)

    return {
        "selected":     selection,
        "significance": sig,
        "memory_ref":   memory_ref,
        "candidates":   [c.to_dict() for c in candidates],
        "scores":       [s.to_dict() for s in scores],
        "reason":       "selected_and_scored",
    }


def _route_to_creative_memory(selection: dict, sig: dict, spark: str, goal: str, domain: str) -> str:
    """High-significance selections route to Universe/Creative memory (Ch.3 §3.5,
    Vol V Ch.9 §14). Returns a ref string (an identifier the caller can persist)."""
    import hashlib
    payload = f"{goal}|{selection['candidate']['metaphor']}|{sig.get('overall', 0):.3f}"
    return "creative:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
