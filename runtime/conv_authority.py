"""
runtime/conv_authority.py — WO-CONV-AUTHORITY-001
Explicit current conversation authority gate.

Source: eLo Intent Alignment §5 + eLo Response Authority §6
"The most recent explicit user statement must outrank stale inferred context.
 This is mandatory." / "Inference must never overwrite explicit current context."

The authority order (strictly enforced):
    1. explicit_current_statement   — VERIFIED — wins always
    2. governed_current_state       — VERIFIED
    3. explicit_current_task        — VERIFIED
    4. recent_context               — INFERRED
    5. older_inference              — REMEMBERED
    6. model_assumption             — POSSIBLE — loses always
"""
from __future__ import annotations
import re

# ── Authority order ────────────────────────────────────────────────────────────
AUTHORITY_ORDER = [
    "explicit_current_statement",  # VERIFIED — wins always
    "governed_current_state",      # VERIFIED
    "explicit_current_task",       # VERIFIED
    "recent_context",              # INFERRED
    "older_inference",             # REMEMBERED
    "model_assumption",            # POSSIBLE — loses always
]

# ── Correction signal patterns ─────────────────────────────────────────────────
# Match: direct corrections of stated or inferred content.
# Design: recognition, not caricature — common natural speech patterns only.
_CORRECTION_PATTERNS = [
    re.compile(r"\bI never said that\b", re.IGNORECASE),
    re.compile(r"\bthat'?s not what I (said|meant)\b", re.IGNORECASE),
    re.compile(r"\bNo[,.]?\s+(I|we|it|that|this)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+(sending|doing|going|saying|making|writing|posting)\b", re.IGNORECASE),
    re.compile(r"\bI'?m not\s+\w+ing\b", re.IGNORECASE),
    re.compile(r"\byou(?:'re| are) (wrong|mistaken|off)\b", re.IGNORECASE),
    re.compile(r"\b(stop|don'?t)\s+(assume|inferring|guessing)\b", re.IGNORECASE),
    re.compile(r"\bthat wasn't (what|it|the)\b", re.IGNORECASE),
    re.compile(r"\bi didn't (say|mean|ask)\b", re.IGNORECASE),
]


def detect_explicit_correction(raw: str) -> bool:
    """
    Return True if the raw user message contains an explicit correction of
    inferred or stated content. No LLM required — pattern match only.

    Examples that match:
        "Not sending anything out."
        "No, I never said that."
        "I'm not going with that direction."
        "That's not what I meant."

    Non-corrections:
        "Maybe not tomorrow."  → False (hedge, not correction)
        "I haven't decided."   → False (deferral, not correction)
    """
    stripped = raw.strip()
    if not stripped:
        return False
    for pattern in _CORRECTION_PATTERNS:
        if pattern.search(stripped):
            return True
    return False


def build_correction_context(raw: str) -> dict:
    """
    When a correction is detected, return a structured annotation for the
    executive trace. Marks the corrected topic with epistemic tier UNKNOWN
    (per WO-CONV-AUTHORITY-001 D-2: stale inference downgraded to UNKNOWN).
    """
    return {
        "explicit_correction_detected": True,
        "correction_source":            raw.strip(),
        "authority_level":              "explicit_current_statement",
        "stale_inference_tier":         "unknown",
        "correction_applied":           True,
    }
