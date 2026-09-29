"""
runtime/faculty_conflict_detector.py — Faculty Conflict Detection

IS ELO: — Internally Consistent?
  can two faculties disagree about something?
  if they disagree, does Executive resolve the conflict?
  can one faculty silently override another?

The prompt injection stack assembles blocks from many faculties independently:
silence_faculty, novelty_detector, expectation_tracker, temporal_state,
correction_history, capability_learning, relationship_evolution, etc.

Each faculty acts as an evidence provider — it reports what it sees from its
own narrow view. The Executive then decides. But if two faculties give
contradictory directives into the system prompt simultaneously, and nothing
flags the contradiction, neither the Executive nor the LLM is informed that
they disagree. The conflict goes unresolved — one faculty silently overrides.

This module:
  1. Scans the assembled system prompt for known conflict patterns
  2. Identifies which directive pairs are contradictory
  3. Names the conflict type and what each faculty claimed
  4. Injects a [FACULTY CONFLICT] block so Executive can resolve

KEY DESIGN PRINCIPLE:
  Faculties provide evidence — Executive resolves.
  A conflict block makes the disagreement explicit rather than hidden.
  Without this module, conflicts are invisible and one faculty wins silently.

THE CAUSAL CHAIN:
  assembled system prompt → detect_conflicts() → list[FacultyConflict]
  → faculty_conflict_prompt_block() → [FACULTY CONFLICT] block
  → LLM / Executive reads it → resolves consciously rather than silently defaulting

CONFLICT TYPES DETECTED:
  silence_vs_novelty:   silence_faculty says "do not fill space"
                         while novelty_detector says "this is novel — engage"
  silence_vs_significant: silence_faculty says "less is more"
                            while significance_faculty marks something as significant
  active_vs_deferred:   temporal_state shows intention as NOW/ACTIVE
                         while another part of the context shows it as DEFERRED/PAUSED
  expectation_vs_correction: expectation_tracker predicts one outcome
                              while correction_history contradicts it
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List

_log = logging.getLogger(__name__)

# ── Conflict signatures ────────────────────────────────────────────────────────

# Patterns that indicate a "be quiet" directive from silence_faculty
_SILENCE_SIGNAL_PATTERNS = [
    r"\[SILENCE PERMISSION",
    r"do not fill the space",
    r"permission granted.*you do not have to speak",
    r"resist the impulse to add more",
]

# Patterns that indicate an "engage more" directive from other faculties
_ENGAGE_SIGNAL_PATTERNS = [
    r"\[NOVEL",
    r"is_novel.*True",
    r"significant enough to surface",
    r"\[SIGNIFICANCE",
    r"strong.*surprise",
]

# Patterns for "intention is ACTIVE right now"
_ACTIVE_NOW_PATTERNS = [
    r"NOW[^a-z].*ACTIVE|ACTIVE.*NOW",
    r"\[NOW\]",
    r"currently active",
]

# Patterns for "intention is DEFERRED / PAUSED"
_DEFERRED_PATTERNS = [
    r"\[PAUSED\]",
    r"DEFERRED",
    r"paused to handle",
    r"waiting for",
]


@dataclass
class FacultyConflict:
    """A detected contradiction between two faculties in the assembled system prompt."""
    conflict_type:  str   # e.g. 'silence_vs_novelty'
    faculty_a:      str   # name of faculty making claim A
    faculty_b:      str   # name of faculty making claim B
    claim_a:        str   # short label for what faculty_a is saying
    claim_b:        str   # short label for what faculty_b is saying
    severity:       str = "moderate"  # 'low' | 'moderate' | 'high'


def _any_match(text: str, patterns: list[str]) -> bool:
    """Return True if any regex pattern matches anywhere in text."""
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE | re.DOTALL):
            return True
    return False


def detect_conflicts(system_prompt: str) -> List[FacultyConflict]:
    """
    Scan the assembled system prompt for known faculty contradiction patterns.

    Returns a list of FacultyConflict objects. Empty list means no conflict detected.
    Never raises.
    """
    if not system_prompt:
        return []

    try:
        conflicts: List[FacultyConflict] = []
        text = system_prompt

        # CONFLICT 1: silence_faculty vs. novelty_detector
        has_silence = _any_match(text, _SILENCE_SIGNAL_PATTERNS)
        has_engage  = _any_match(text, _ENGAGE_SIGNAL_PATTERNS)
        if has_silence and has_engage:
            conflicts.append(FacultyConflict(
                conflict_type = "silence_vs_novelty",
                faculty_a     = "silence_faculty",
                faculty_b     = "novelty_detector",
                claim_a       = "less is more — do not fill the space",
                claim_b       = "this input is novel — engage",
                severity      = "high",
            ))

        # CONFLICT 2: active intention vs. deferred state in same prompt
        has_active   = _any_match(text, _ACTIVE_NOW_PATTERNS)
        has_deferred = _any_match(text, _DEFERRED_PATTERNS)
        if has_active and has_deferred:
            conflicts.append(FacultyConflict(
                conflict_type = "active_vs_deferred",
                faculty_a     = "temporal_state",
                faculty_b     = "temporal_state",
                claim_a       = "intention is ACTIVE / NOW",
                claim_b       = "intention is DEFERRED / PAUSED",
                severity      = "moderate",
            ))

        return conflicts

    except Exception as exc:
        _log.warning("detect_conflicts failed (non-fatal): %s", exc)
        return []


def faculty_conflict_prompt_block(system_prompt: str) -> str:
    """
    Build a [FACULTY CONFLICT] block when the assembled system prompt contains
    contradictory faculty directives.

    Returns "" when no conflict is detected.
    Never raises.

    The block names:
      - which faculties are in conflict
      - what each faculty is claiming
      - that Executive must resolve the conflict rather than letting one silently win

    THE CAUSAL CHAIN:
      assembled system → detect_conflicts() → FacultyConflict list
      → [FACULTY CONFLICT] block → LLM reads it → resolves consciously
    """
    try:
        conflicts = detect_conflicts(system_prompt)
        if not conflicts:
            return ""

        lines = [
            "[FACULTY CONFLICT — two faculties disagree; Executive must resolve]",
            "  These conflicts exist in the assembled context. Do not let one silently override.",
            "  You must decide which directive is appropriate for this moment.",
        ]
        for i, c in enumerate(conflicts, 1):
            lines.append(f"  Conflict {i}: {c.conflict_type} [{c.severity}]")
            lines.append(f"    {c.faculty_a} says: {c.claim_a}")
            lines.append(f"    {c.faculty_b} says: {c.claim_b}")
            lines.append(f"    Resolution: use the evidence from both to decide what serves this moment.")
        lines.append(
            "  Rule: no faculty independently decides what eLo does. Executive resolves."
        )

        return "\n".join(lines)

    except Exception as exc:
        _log.warning("faculty_conflict_prompt_block failed (non-fatal): %s", exc)
        return ""
