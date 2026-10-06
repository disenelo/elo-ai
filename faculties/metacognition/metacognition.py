"""
faculties/metacognition/metacognition.py — WO-METACOGNITION-001

Self-monitoring faculty: assesses eLo's confidence in its own just-generated
response and detects common reasoning errors. Feeds the honest-absence and
self-correction pipelines.

API:
    assess_confidence(response, context) -> float  (0.0–1.0)
    flag_uncertainty(confidence, threshold) -> bool
    detect_reasoning_error(reasoning_trace) -> str | None  (error description or None)
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger(__name__)

# ── Known reasoning error patterns ────────────────────────────────────────────

_CIRCULAR_PATTERNS = [
    # "X is X because X" — circular definition
    r"(\b\w+\b).{0,30}\bbecause\b.{0,30}\1",
    # "therefore" without evidence phrases
    r"\btherefore\b.{0,60}\bbecause\b",
]

_MISSING_EVIDENCE = [
    "i assume", "i'm guessing", "i think but i'm not sure",
    "i believe but have no", "not certain but", "probably probably",
]

_CONTRADICTION_MARKERS = [
    # sentence containing "is X" immediately followed by "is not X"
    r"\bis\b(.{1,30})\bis not\b\1",
    # "always" immediately contradicted by "never"
    r"\balways\b.{0,50}\bnever\b",
]

# Phrases that signal eLo is asserting something outside its knowledge base
_OVERREACH_PHRASES = [
    "i definitely know", "i'm 100% certain", "i guarantee",
    "it is absolutely", "there is no doubt",
]


# ── Confidence scoring ────────────────────────────────────────────────────────

def _wkg_coverage(response: str) -> float:
    """
    Estimate WKG coverage for the response: fraction of non-trivial nouns in
    the response that have a matching WKG entity. Returns 0.0-1.0.
    Falls back to 0.5 (neutral) if WKG is unavailable.
    """
    try:
        from runtime.wkg_faculty import search_entities
    except Exception:
        return 0.5

    words = re.findall(r"\b[A-Z][a-z]{2,}\b", response)
    unique = list(dict.fromkeys(words))[:10]  # cap at 10 for speed
    if not unique:
        return 0.5

    hits = sum(1 for w in unique if search_entities(w))
    return hits / len(unique)


def _memory_match_score(response: str, context: dict) -> float:
    """
    Score how well the response aligns with known context.
    High score = response references things present in context.
    Returns 0.0-1.0.
    """
    if not context:
        return 0.5

    ctx_text = " ".join(str(v) for v in context.values() if v).lower()
    if not ctx_text:
        return 0.5

    resp_lower = response.lower()
    # Extract words > 4 chars from context as candidate matches
    ctx_words = [w for w in re.findall(r"\b[a-z]{5,}\b", ctx_text)][:20]
    if not ctx_words:
        return 0.5

    matches = sum(1 for w in ctx_words if w in resp_lower)
    return min(1.0, matches / max(1, len(ctx_words) // 2))


def assess_confidence(response: str, context: dict | None = None) -> float:
    """
    Estimate eLo's confidence in the response it just generated (0.0–1.0).

    Factors:
    - WKG coverage: entities in response found in knowledge graph
    - Memory/context match: response references things we know from context
    - Overreach penalty: phrases asserting certainty beyond knowledge
    - Response length: very short responses are lower confidence

    Args:
        response: the candidate response text
        context:  optional dict (wkg_context, user_input, etc.)

    Returns:
        float 0.0–1.0, higher = more confident
    """
    if not response or len(response.strip()) < 5:
        return 0.0

    ctx = context or {}
    wkg   = _wkg_coverage(response)
    mem   = _memory_match_score(response, ctx)
    base  = (wkg * 0.5) + (mem * 0.5)

    # Penalise overreach phrases
    rl = response.lower()
    overreach = sum(1 for p in _OVERREACH_PHRASES if p in rl)
    base = max(0.0, base - overreach * 0.15)

    # Penalise very short responses (< 20 chars often means eLo is guessing)
    if len(response.strip()) < 20:
        base = max(0.0, base - 0.2)

    return round(min(1.0, base), 3)


# ── Uncertainty flagging ──────────────────────────────────────────────────────

def flag_uncertainty(confidence: float, threshold: float = 0.6) -> bool:
    """
    Returns True if confidence is below threshold — signals that the response
    should include an honest-absence hedge rather than asserting directly.

    Args:
        confidence: float from assess_confidence()
        threshold:  default 0.6 — below this, eLo should hedge

    Returns:
        True if confidence < threshold (i.e. hedge is warranted)
    """
    return confidence < threshold


# ── Reasoning error detection ─────────────────────────────────────────────────

def detect_reasoning_error(reasoning_trace: str) -> str | None:
    """
    Check a reasoning trace (eLo's internal thought, planning step, or response)
    for known error patterns. Returns a short description of the detected error,
    or None if no error found.

    Checks:
    1. Circular reasoning (X because X)
    2. Assertions with missing evidence markers
    3. Contradictions (always/never, is/is not)

    Args:
        reasoning_trace: the text to check (inner thought or response)

    Returns:
        str describing the error, or None
    """
    if not reasoning_trace:
        return None

    tl = reasoning_trace.lower()

    # Check circular patterns
    for pattern in _CIRCULAR_PATTERNS:
        try:
            if re.search(pattern, reasoning_trace, re.IGNORECASE | re.DOTALL):
                return "circular_reasoning: claim references itself as its own justification"
        except re.error:
            pass

    # Check missing evidence (hedge without grounding)
    for phrase in _MISSING_EVIDENCE:
        if phrase in tl:
            return f"missing_evidence: assertion made without grounding ('{phrase}' detected)"

    # Check contradictions
    for pattern in _CONTRADICTION_MARKERS:
        try:
            if re.search(pattern, reasoning_trace, re.IGNORECASE | re.DOTALL):
                return "contradiction: statement contradicts itself within the same response"
        except re.error:
            pass

    return None


# ── Self-correction hook ──────────────────────────────────────────────────────

def evaluate_and_record(response: str, context: dict | None = None) -> dict:
    """
    Full metacognitive evaluation of a response. Returns a dict with:
    - confidence (float)
    - needs_hedge (bool)
    - error (str or None)

    If confidence is low or an error is detected, attempts to write to the
    correction store so the pattern is logged for future improvement.

    Args:
        response: the generated response text
        context:  optional context dict

    Returns:
        {"confidence": float, "needs_hedge": bool, "error": str | None}
    """
    confidence = assess_confidence(response, context)
    needs_hedge = flag_uncertainty(confidence)
    error = detect_reasoning_error(response)

    if needs_hedge or error:
        try:
            from self_improvement.correction_store import store_correction
            store_correction(
                trigger="metacognition",
                original=response[:300],
                correction=(
                    f"Low confidence ({confidence:.2f})" if needs_hedge else ""
                ) + (f" | Error: {error}" if error else ""),
            )
        except Exception:
            pass
        _log.debug(
            "metacognition: confidence=%.2f needs_hedge=%s error=%s",
            confidence, needs_hedge, error,
        )

    return {"confidence": confidence, "needs_hedge": needs_hedge, "error": error}
