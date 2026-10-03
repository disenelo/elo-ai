"""
tests/test_correction_exec_wire.py — WO-CORRECTION-EXEC-WIRE-001

Acceptance:
- ExecutiveContext.correction_alert field exists and defaults to empty dict
- ec_correction_alert key exposed in as_dict()
- frequency >= 5 → "reflect" >= 0.80 injected into learning_advice
- frequency >= 3 → "reflect" >= 0.65 injected into learning_advice (advisory)
- frequency < 3 → no reflect injection from correction path
- build_executive_context() with raw_input matching 5+ corrections → reflect >= 0.80
- build_executive_context() with raw_input matching 0 corrections → no reflect injection
- Counterfactual: same input, correction-matched → reflect; no correction → answer allowed
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_ec(correction_alert: dict | None = None) -> "ExecutiveContext":
    from runtime.executive_context import ExecutiveContext
    return ExecutiveContext(correction_alert=correction_alert or {})


def _as_dict(correction_alert: dict | None = None) -> dict:
    return _make_ec(correction_alert).as_dict()


def _mock_corrections(n: int, why: str = "scrub: raw generation differed") -> list:
    return [
        {"id": f"CX-{i:07d}", "input": "walk around", "corrected_response": "ok", "why": why}
        for i in range(n)
    ]


# ── field existence ───────────────────────────────────────────────────────────

def test_ec_correction_alert_default_empty():
    from runtime.executive_context import ExecutiveContext
    ec = ExecutiveContext()
    assert ec.correction_alert == {}


def test_ec_correction_alert_populated():
    ca = {"category": "scrub", "frequency": 5, "top_correction": None}
    ec = _make_ec(ca)
    assert ec.correction_alert["frequency"] == 5


# ── as_dict() key exposure ────────────────────────────────────────────────────

def test_ec_correction_alert_key_in_as_dict():
    ca = {"category": "scrub", "frequency": 0}
    d = _as_dict(ca)
    assert "ec_correction_alert" in d
    assert d["ec_correction_alert"]["frequency"] == 0


# ── frequency >= 5 → reflect 0.80 ────────────────────────────────────────────

def test_freq5_injects_reflect_080():
    """frequency >= 5 → learning_advice.preferences['reflect'] >= 0.80."""
    ca = {"category": "scrub", "frequency": 6}
    d = _as_dict(ca)
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) >= 0.80, (
        f"Expected reflect >= 0.80 for frequency=6; got {prefs}"
    )


def test_freq5_sets_confidence():
    ca = {"category": "scrub", "frequency": 5}
    d = _as_dict(ca)
    la = d.get("learning_advice") or {}
    assert la.get("confidence", 0.0) >= 0.60


# ── frequency >= 3 → reflect 0.65 ────────────────────────────────────────────

def test_freq3_injects_reflect_065():
    """frequency >= 3 but < 5 → learning_advice.preferences['reflect'] >= 0.65."""
    ca = {"category": "scrub", "frequency": 3}
    d = _as_dict(ca)
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) >= 0.65, (
        f"Expected reflect >= 0.65 for frequency=3; got {prefs}"
    )


def test_freq4_injects_reflect_065_not_080():
    """frequency=4: reflect >= 0.65 but should not be forced to 0.80 by this path."""
    ca = {"category": "scrub", "frequency": 4}
    d = _as_dict(ca)
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    r = prefs.get("reflect", 0.0)
    assert r >= 0.65, f"Expected reflect >= 0.65 for frequency=4; got {r}"
    # Advisory: weight should be 0.65, not forced to 0.80 threshold
    assert r < 0.80, f"frequency=4 should inject 0.65, not 0.80; got {r}"


# ── frequency < 3 → no injection ─────────────────────────────────────────────

def test_freq2_no_injection():
    """frequency < 3 → no reflect injected from correction path."""
    ca = {"category": "scrub", "frequency": 2}
    d = _as_dict(ca)
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) < 0.65, (
        f"frequency=2 should not inject reflect; got {prefs}"
    )


def test_empty_alert_no_injection():
    d = _as_dict({})
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) < 0.65


# ── build_executive_context integration ──────────────────────────────────────

def test_build_5_matches_injects_reflect():
    """build_executive_context with raw_input matching 5+ corrections → reflect >= 0.80."""
    from runtime.executive_context import build_executive_context
    _mocks = _mock_corrections(5)
    with patch("self_improvement.correction_store.search_corrections", return_value=_mocks):
        ec = build_executive_context(
            intent="conversation",
            emotional_context={},
            world=None,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=None,
            attention={},
            raw_input="walk around for a while please",
        )
    assert ec.correction_alert.get("frequency") == 5
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) >= 0.80, (
        f"Expected reflect >= 0.80 from 5 matched corrections; got {prefs}"
    )


def test_build_no_matches_no_inject():
    """build_executive_context with no matching corrections → no correction reflect."""
    from runtime.executive_context import build_executive_context
    with patch("self_improvement.correction_store.search_corrections", return_value=[]):
        ec = build_executive_context(
            intent="conversation",
            emotional_context={},
            world=None,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=None,
            attention={},
            raw_input="hello",
        )
    assert ec.correction_alert == {}
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    # No correction-driven reflect
    assert prefs.get("reflect", 0.0) < 0.65, (
        f"No corrections should not inject reflect; got {prefs}"
    )


# ── counterfactual: same input, different correction match count ──────────────

def test_counterfactual_same_input_different_count():
    """Same input: 6 corrections → reflect; 0 corrections → reflect absent."""
    from runtime.executive_context import build_executive_context

    with patch("self_improvement.correction_store.search_corrections",
               return_value=_mock_corrections(6)):
        ec_with = build_executive_context(
            intent="conversation", emotional_context={}, world=None,
            working_memory=None, capabilities=[], cognitive_state=None,
            affordances=None, attention={}, raw_input="walk around please",
        )

    with patch("self_improvement.correction_store.search_corrections",
               return_value=[]):
        ec_without = build_executive_context(
            intent="conversation", emotional_context={}, world=None,
            working_memory=None, capabilities=[], cognitive_state=None,
            affordances=None, attention={}, raw_input="walk around please",
        )

    d_with    = ec_with.as_dict()
    d_without = ec_without.as_dict()

    prefs_with    = (d_with.get("learning_advice") or {}).get("preferences") or {}
    prefs_without = (d_without.get("learning_advice") or {}).get("preferences") or {}

    assert prefs_with.get("reflect", 0.0) >= 0.80, (
        f"6 corrections: expected reflect >= 0.80; got {prefs_with}"
    )
    assert prefs_without.get("reflect", 0.0) < 0.65, (
        f"0 corrections: expected reflect < 0.65; got {prefs_without}"
    )
