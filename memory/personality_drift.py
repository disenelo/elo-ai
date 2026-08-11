"""
memory/personality_drift.py — personality drift gate for eLo OS.

WO-CANON-X / Ruling D (2026-08-10): drift is a PROPOSAL, not a direct write.
Conversational signals produce a DriftProposal stored in drift_proposals.json.
Nothing is ever written to personality_state.json from this path — the Reflection
gate (V Ch.7) owns that write.

One trait model: Volume V Ch.7's PersonalityVector
    curiosity / patience / confidence / empathy / discipline / wonder / playfulness / directness

Value traits (need David's yes):  wonder, empathy, directness
Nuance traits (free to evolve):   curiosity, patience, confidence, discipline, playfulness
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

_ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH      = os.path.join(_ROOT, "memory", "personality_state.json")
_PROPOSALS = os.path.join(_ROOT, "memory", "drift_proposals.json")

# ── Volume V Ch.7 canonical trait vector ─────────────────────────────────────
_V5_CH7_TRAITS: dict[str, float] = {
    "curiosity":   0.80,
    "patience":    0.70,
    "confidence":  0.70,
    "empathy":     0.80,
    "discipline":  0.60,
    "wonder":      0.90,
    "playfulness": 0.70,
    "directness":  0.75,
}

# Value traits: touching these requires David's approval (Ruling XXI)
_VALUE_TRAITS: frozenset[str] = frozenset({"wonder", "empathy", "directness"})

_CLAMP_MIN = 0.20
_CLAMP_MAX = 0.95
_MAX_STEP  = 0.02


def _clamp(v: float) -> float:
    return max(_CLAMP_MIN, min(_CLAMP_MAX, v))


def load() -> dict:
    """Load personality state from disk. Returns V Ch.7 baseline if missing or corrupt."""
    if not os.path.exists(_PATH):
        return dict(_V5_CH7_TRAITS)
    try:
        with open(_PATH, encoding="utf-8") as f:
            state = json.load(f)
        for k, v in _V5_CH7_TRAITS.items():
            if k not in state:
                state[k] = v
        return state
    except Exception:
        return dict(_V5_CH7_TRAITS)


def _analyse_session(emotional_history: list, session_summaries: list) -> dict[str, float]:
    """
    Derive V Ch.7 trait deltas from one session's signals.
    Returns only traits with non-zero delta; all values are capped to _MAX_STEP.
    """
    if not emotional_history:
        return {}

    recent_tones = [h.get("tone", "neutral") for h in emotional_history[-10:]]
    user_texts   = " ".join(s.get("user", "") for s in session_summaries[-10:]).lower()

    counts: dict = {}
    for t in recent_tones:
        counts[t] = counts.get(t, 0) + 1
    dominant = max(counts, key=counts.get) if counts else "neutral"

    adj: dict[str, float] = {}

    # patience — calm, grounded communication
    if dominant in ("neutral", "positive"):
        adj["patience"] = +0.01
    elif dominant == "frustrated":
        adj["patience"] = -0.02

    simplify_words = ["too much", "overwhelm", "can't", "stuck", "confused"]
    if any(w in user_texts for w in simplify_words):
        adj["patience"] = adj.get("patience", 0.0) + 0.01

    # curiosity — exploratory tone
    if dominant in ("exploratory", "positive"):
        adj["curiosity"] = +0.01

    # playfulness — creative engagement (was expressive)
    creative_words = ["what if", "imagine", "create", "build", "design"]
    if any(w in user_texts for w in creative_words):
        adj["playfulness"] = +0.01
        adj["wonder"]      = +0.01       # wonder co-rises with imagination
    elif dominant == "low-energy":
        adj["playfulness"] = -0.01

    # empathy — emotional inputs (VALUE trait — flagged for David)
    if dominant in ("low-energy", "positive"):
        adj["empathy"] = +0.01
    elif dominant == "frustrated":
        adj["empathy"] = -0.01

    # discipline — technical focus (was technical_focus)
    tech_words = ["system", "memory", "kernel", "backend", "build", "implement", "code"]
    if any(w in user_texts for w in tech_words):
        adj["discipline"] = +0.02
    else:
        adj["discipline"] = -0.01

    # cap every delta to ±_MAX_STEP
    return {k: max(-_MAX_STEP, min(_MAX_STEP, v)) for k, v in adj.items() if v != 0.0}


def propose(emotional_history: list, session_summaries: list) -> dict:
    """
    Produce a DriftProposal from one session's signals. Does NOT write to
    personality_state.json. Appends the proposal to drift_proposals.json and
    returns the proposal dict.

    The proposal carries `needs_david: True` if any delta touches a _VALUE_TRAIT.
    Status is always "pending" — the Reflection gate (V Ch.7) decides if it's applied.
    """
    deltas = _analyse_session(emotional_history, session_summaries)

    needs_david = any(trait in _VALUE_TRAITS for trait in deltas)

    proposal = {
        "ts":          datetime.now(timezone.utc).isoformat(),
        "source":      "conversational_drift",
        "trait_model": "v5_ch7",
        "deltas":      deltas,
        "needs_david": needs_david,
        "status":      "pending",
    }

    # append proposal to the proposals ledger (never touch personality_state.json)
    try:
        if os.path.exists(_PROPOSALS):
            with open(_PROPOSALS, encoding="utf-8") as f:
                ledger = json.load(f)
            if not isinstance(ledger, list):
                ledger = []
        else:
            ledger = []
        ledger.append(proposal)
        with open(_PROPOSALS, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return proposal


if __name__ == "__main__":
    ps = load()
    print("Current personality state (read-only in drift path):")
    print(json.dumps(ps, indent=2))
