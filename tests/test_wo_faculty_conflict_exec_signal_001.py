"""
tests/test_wo_faculty_conflict_exec_signal_001.py — WO-FACULTY-CONFLICT-EXEC-SIGNAL-001

Acceptance:
- ExecutiveContext.faculty_conflict field exists and defaults to empty dict
- ec_faculty_conflict key exposed in as_dict()
- High severity + detected → "reflect" >= 0.82 injected into learning_advice
- Moderate severity → ec_faculty_conflict exposed but no reflect injection from conflict
- No conflict → no reflect injection from this path
- build_executive_context() with recall + strong_surprise → detected=True, severity="high"
- build_executive_context() with "answer" intent → no conflict detected

WO Acceptance (verbatim):
  "Input where Memory-endorsed interpretation and WKG-endorsed interpretation
   conflict → Executive selects 'reflect' over 'answer.'
   Without conflict, same input → 'answer.'"
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_ec(faculty_conflict: dict | None = None) -> "ExecutiveContext":
    from runtime.executive_context import ExecutiveContext
    return ExecutiveContext(faculty_conflict=faculty_conflict or {})


def _as_dict(faculty_conflict: dict | None = None) -> dict:
    ec = _make_ec(faculty_conflict)
    return ec.as_dict()


# ── field existence ───────────────────────────────────────────────────────────

def test_ec_faculty_conflict_default_empty():
    from runtime.executive_context import ExecutiveContext
    ec = ExecutiveContext()
    assert ec.faculty_conflict == {}


def test_ec_faculty_conflict_populated():
    fc = {"detected": True, "severity": "high", "conflicting_faculties": ["memory", "wkg"]}
    ec = _make_ec(fc)
    assert ec.faculty_conflict["detected"] is True
    assert ec.faculty_conflict["severity"] == "high"
    assert "memory" in ec.faculty_conflict["conflicting_faculties"]


# ── as_dict() key exposure ─────────────────────────────────────────────────────

def test_ec_faculty_conflict_key_in_as_dict():
    """as_dict() must expose ec_faculty_conflict key."""
    fc = {"detected": False, "severity": "none", "conflicting_faculties": []}
    d = _as_dict(fc)
    assert "ec_faculty_conflict" in d
    assert d["ec_faculty_conflict"]["severity"] == "none"


# ── high-severity injection ────────────────────────────────────────────────────

def test_high_conflict_injects_reflect_082():
    """High severity + detected → learning_advice.preferences['reflect'] >= 0.82."""
    fc = {"detected": True, "severity": "high", "conflicting_faculties": ["memory", "wkg"]}
    d = _as_dict(fc)
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) >= 0.82, (
        f"Expected reflect >= 0.82 for high conflict; got {prefs}"
    )


def test_high_conflict_sets_confidence():
    """High severity conflict raises learning_advice confidence to >= 0.70."""
    fc = {"detected": True, "severity": "high", "conflicting_faculties": ["memory", "wkg"]}
    d = _as_dict(fc)
    la = d.get("learning_advice") or {}
    assert la.get("confidence", 0.0) >= 0.70, (
        f"Expected confidence >= 0.70 for high conflict; got {la}"
    )


def test_high_conflict_sets_rationale():
    """High severity conflict writes a non-empty rationale."""
    fc = {"detected": True, "severity": "high", "conflicting_faculties": ["memory", "wkg"]}
    d = _as_dict(fc)
    la = d.get("learning_advice") or {}
    assert la.get("rationale", ""), f"Expected non-empty rationale; got {la}"


# ── moderate severity — exposed but no injection ──────────────────────────────

def test_moderate_conflict_no_reflect_injection():
    """Moderate severity: ec_faculty_conflict exposed but reflect NOT boosted to 0.82."""
    fc = {"detected": True, "severity": "moderate", "conflicting_faculties": ["memory", "wkg"]}
    d = _as_dict(fc)
    assert d["ec_faculty_conflict"]["severity"] == "moderate"
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    # Moderate conflict must NOT inject reflect at 0.82 via the faculty-conflict path
    assert prefs.get("reflect", 0.0) < 0.82, (
        f"Moderate conflict should not inject reflect >= 0.82; got {prefs}"
    )


# ── no conflict ────────────────────────────────────────────────────────────────

def test_no_conflict_no_reflect_injection():
    """No conflict → faculty-conflict path does not inject reflect."""
    fc = {"detected": False, "severity": "none", "conflicting_faculties": []}
    d = _as_dict(fc)
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    # No reflect injected by faculty-conflict path (other paths absent in bare EC)
    assert prefs.get("reflect", 0.0) < 0.82, (
        f"No conflict should not inject reflect >= 0.82; got {prefs}"
    )


def test_empty_faculty_conflict_no_injection():
    """Empty faculty_conflict dict (default) → no reflect injection."""
    d = _as_dict({})
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) < 0.82, (
        f"Empty conflict dict should not inject reflect; got {prefs}"
    )


# ── build_executive_context detection ─────────────────────────────────────────

def test_build_recall_strong_surprise_high_conflict():
    """Recall intent + strong_surprise → detected=True, severity='high'."""
    from runtime.executive_context import build_executive_context
    with patch("memory.expectation_tracker.score_expectation") as _mock_score:
        _viol = type("V", (), {"prediction_error": 0.82, "level": "strong_surprise"})()
        _mock_score.return_value = _viol
        ec = build_executive_context(
            intent="recall",
            emotional_context={},
            world=None,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=None,
            attention={"wm_winner": "memory"},
            edge_hint="recall:test",
        )
    fc = ec.faculty_conflict
    assert fc.get("detected") is True, f"Expected detected=True; got {fc}"
    assert fc.get("severity") == "high", f"Expected severity='high'; got {fc}"
    assert "memory" in fc.get("conflicting_faculties", [])
    # as_dict() must inject reflect >= 0.82
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) >= 0.82, (
        f"Expected reflect >= 0.82 from build path; got {prefs}"
    )


def test_build_answer_intent_no_conflict():
    """Non-recall intent → no conflict detected."""
    from runtime.executive_context import build_executive_context
    with patch("memory.expectation_tracker.score_expectation") as _mock_score:
        _viol = type("V", (), {"prediction_error": 0.80, "level": "strong_surprise"})()
        _mock_score.return_value = _viol
        ec = build_executive_context(
            intent="answer",
            emotional_context={},
            world=None,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=None,
            attention={"wm_winner": "memory"},
            edge_hint="answer:test",
        )
    fc = ec.faculty_conflict
    assert fc.get("detected") is False, f"Expected no conflict for 'answer' intent; got {fc}"
    assert fc.get("severity") == "none"


def test_build_inquiry_low_pe_no_conflict():
    """Inquiry intent + low prediction error → no conflict (surprise not strong enough)."""
    from runtime.executive_context import build_executive_context
    with patch("memory.expectation_tracker.score_expectation") as _mock_score:
        _viol = type("V", (), {"prediction_error": 0.30, "level": "slight_surprise"})()
        _mock_score.return_value = _viol
        ec = build_executive_context(
            intent="inquiry",
            emotional_context={},
            world=None,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=None,
            attention={},
            edge_hint="inquiry:test",
        )
    fc = ec.faculty_conflict
    assert fc.get("detected") is False, (
        f"Low PE should not trigger conflict; got {fc}"
    )
