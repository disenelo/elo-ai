"""
faculties/imagination/imagination_faculty.py — WO-IMAGINATION-001

Deliberate simulation (Imagination) faculty. eLo choosing to model "what if"
while awake — distinct from Dream State (offline, generative, unstructured).

Five simulation types:
  1. outcome        — "If I do X, what happens?"
  2. counterfactual — "What if that had gone differently?"
  3. perspective    — "How might David experience this?"
  4. design         — "If this mechanism works this way, what can it do?"
  5. self           — "What am I capable of in this embodiment?"

Epistemic gate: SIMULATED → CANDIDATE → VERIFY → KNOWLEDGE | REMAINS_HYPOTHESIS
SimulationResults are NEVER written to WKG as fact. Executive receives them
as hypotheses to evaluate, not as knowledge to store.

Source: SOURCE_2026-09-27_DAVID_imagination_spec.md
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Literal

_log = logging.getLogger(__name__)

# ── Types ──────────────────────────────────────────────────────────────────────

SimulationType = Literal[
    "outcome",
    "counterfactual",
    "perspective",
    "design",
    "self",
]

EpistemicStatus = Literal[
    "SIMULATED",     # initial — never treated as fact
    "CANDIDATE",     # nominated for verification
    "VERIFY",        # under verification
    "KNOWLEDGE",     # verified and promoted to knowledge
    "REMAINS_HYPOTHESIS",  # verification concluded — not proven
]

VALID_SIMULATION_TYPES: frozenset[str] = frozenset({
    "outcome", "counterfactual", "perspective", "design", "self",
})


@dataclass
class SimulationResult:
    """
    Output of one imagination simulation.

    Never written to WKG directly. Must pass epistemic gate to become KNOWLEDGE.
    """
    simulation_type:  SimulationType
    hypothesis:       str                          # the simulated claim
    confidence:       float                        # 0.0 (pure guess) – 1.0 (near-certain)
    evidence:         list[str]  = field(default_factory=list)   # reasoning chain
    expiry:           float      = field(default_factory=lambda: time.time() + 3600.0)
    epistemic_status: EpistemicStatus = "SIMULATED"
    context:          dict        = field(default_factory=dict)  # what was simulated
    timestamp:        float       = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
        if self.simulation_type not in VALID_SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {self.simulation_type!r}")
        if not self.hypothesis.strip():
            raise ValueError("hypothesis cannot be empty")

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expiry

    def promote(self) -> "SimulationResult":
        """Advance through the epistemic gate — returns a new instance."""
        _NEXT: dict[str, EpistemicStatus] = {
            "SIMULATED": "CANDIDATE",
            "CANDIDATE": "VERIFY",
            "VERIFY":    "KNOWLEDGE",
        }
        next_status = _NEXT.get(self.epistemic_status)
        if next_status is None:
            return self
        return SimulationResult(
            simulation_type  = self.simulation_type,
            hypothesis       = self.hypothesis,
            confidence       = self.confidence,
            evidence         = list(self.evidence),
            expiry           = self.expiry,
            epistemic_status = next_status,
            context          = dict(self.context),
            timestamp        = self.timestamp,
        )

    def invalidate(self) -> "SimulationResult":
        """Mark as unverifiable — stays hypothesis forever."""
        return SimulationResult(
            simulation_type  = self.simulation_type,
            hypothesis       = self.hypothesis,
            confidence       = self.confidence,
            evidence         = list(self.evidence),
            expiry           = self.expiry,
            epistemic_status = "REMAINS_HYPOTHESIS",
            context          = dict(self.context),
            timestamp        = self.timestamp,
        )


# ── Simulation functions ───────────────────────────────────────────────────────

def simulate_outcome(
    action: str,
    context: dict | None = None,
    confidence: float = 0.5,
) -> SimulationResult:
    """
    'If I do X, what happens?' — outcome simulation.
    Produces a hypothesis about the consequence of a proposed action.
    """
    hypothesis = f"If {action}, the likely outcome is: [deliberate simulation — unverified]"
    evidence = [f"simulated from context: {action}"]
    if context:
        evidence.append(f"context signals: {list(context.keys())}")
    return SimulationResult(
        simulation_type = "outcome",
        hypothesis      = hypothesis,
        confidence      = confidence,
        evidence        = evidence,
        context         = context or {},
    )


def simulate_counterfactual(
    past_event: str,
    alternative: str,
    context: dict | None = None,
    confidence: float = 0.35,
) -> SimulationResult:
    """
    'What if that had gone differently?' — counterfactual simulation.
    Models an alternative history branching from a past event.
    """
    hypothesis = (
        f"Had {past_event} gone differently ({alternative}), "
        "the counterfactual outcome would be: [deliberate simulation — unverified]"
    )
    return SimulationResult(
        simulation_type = "counterfactual",
        hypothesis      = hypothesis,
        confidence      = confidence,
        evidence        = [f"divergence point: {past_event}", f"alternative: {alternative}"],
        context         = context or {},
    )


def simulate_perspective(
    subject: str,
    situation: str,
    context: dict | None = None,
    confidence: float = 0.4,
) -> SimulationResult:
    """
    'How might {subject} experience this?' — perspective simulation.
    Feeds CCM (cross-character model) — helps eLo understand how others experience him.
    """
    hypothesis = (
        f"From {subject}'s perspective, {situation} would likely feel: "
        "[deliberate simulation — unverified]"
    )
    return SimulationResult(
        simulation_type = "perspective",
        hypothesis      = hypothesis,
        confidence      = confidence,
        evidence        = [f"perspective: {subject}", f"situation: {situation}"],
        context         = context or {},
    )


def simulate_design(
    mechanism: str,
    capability_query: str,
    context: dict | None = None,
    confidence: float = 0.5,
) -> SimulationResult:
    """
    'If this mechanism works this way, what can it do?' — design simulation.
    Models the capability envelope of a described mechanism.
    """
    hypothesis = (
        f"If {mechanism} operates as described, it can: {capability_query} "
        "[deliberate simulation — unverified]"
    )
    return SimulationResult(
        simulation_type = "design",
        hypothesis      = hypothesis,
        confidence      = confidence,
        evidence        = [f"mechanism: {mechanism}", f"query: {capability_query}"],
        context         = context or {},
    )


def simulate_self(
    embodiment: str,
    capability_query: str,
    context: dict | None = None,
    confidence: float = 0.45,
) -> SimulationResult:
    """
    'What am I capable of in this embodiment?' — self simulation.
    eLo models its own capabilities within a given embodiment context.
    """
    hypothesis = (
        f"In embodiment '{embodiment}', the capability for '{capability_query}' is: "
        "[deliberate simulation — unverified]"
    )
    return SimulationResult(
        simulation_type = "self",
        hypothesis      = hypothesis,
        confidence      = confidence,
        evidence        = [f"embodiment: {embodiment}", f"capability query: {capability_query}"],
        context         = context or {},
    )


# ── Dispatcher ────────────────────────────────────────────────────────────────

_SIMULATORS = {
    "outcome":       simulate_outcome,
    "counterfactual": simulate_counterfactual,
    "perspective":   simulate_perspective,
    "design":        simulate_design,
    "self":          simulate_self,
}


def simulate(
    simulation_type: SimulationType,
    **kwargs,
) -> SimulationResult:
    """
    Dispatch to the appropriate simulation function.

    Raises ValueError for unknown simulation_type. The result is always
    SIMULATED epistemic_status — never fact, never stored to WKG directly.
    Executive receives SimulationResults as hypotheses only.
    """
    if simulation_type not in _SIMULATORS:
        raise ValueError(
            f"Unknown simulation_type: {simulation_type!r}. "
            f"Valid: {sorted(VALID_SIMULATION_TYPES)}"
        )
    result = _SIMULATORS[simulation_type](**kwargs)
    _log.debug(
        "imagination: %s simulation → hypothesis=%r confidence=%.2f status=%s",
        simulation_type, result.hypothesis[:80], result.confidence, result.epistemic_status,
    )
    return result


def context_block(results: list[SimulationResult]) -> str:
    """
    Convert a list of SimulationResults into a context injection string.
    Marked SIMULATED — Executive sees these as deliberate hypotheses, not facts.
    All results must be non-expired.
    """
    active = [r for r in results if not r.is_expired and r.epistemic_status == "SIMULATED"]
    if not active:
        return ""
    lines = ["[IMAGINATION — deliberate simulations, not facts. Treat as hypotheses only.]"]
    for r in active:
        lines.append(
            f"  [{r.simulation_type.upper()} sim, confidence={r.confidence:.0%}] {r.hypothesis}"
        )
    return "\n".join(lines)
