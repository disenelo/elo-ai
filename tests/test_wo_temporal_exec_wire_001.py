"""
tests/test_wo_temporal_exec_wire_001.py — WO-TEMPORAL-EXEC-WIRE-001

Acceptance:
- ExecutiveContext.temporal_state is populated from the temporal param
- interaction_gap_hours >= 24 → "celebrate" injected into learning_advice
- has_deferred_threads=True → "reflect" injected into learning_advice
- Neither flag set → no temporal injection
- build_executive_context() accepts temporal kwarg and passes it through
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_ec(temporal: dict | None = None) -> "ExecutiveContext":
    from runtime.executive_context import ExecutiveContext
    return ExecutiveContext(temporal_state=temporal or {})


def _as_dict(temporal: dict | None = None) -> dict:
    ec = _make_ec(temporal)
    return ec.as_dict()


# ── temporal_state field ──────────────────────────────────────────────────────

def test_ec_temporal_state_default_empty():
    from runtime.executive_context import ExecutiveContext
    ec = ExecutiveContext()
    assert ec.temporal_state == {}


def test_ec_temporal_state_populated():
    td = {"circadian_phase": "active", "interaction_gap_hours": 26.5, "has_deferred_threads": False}
    ec = _make_ec(td)
    assert ec.temporal_state["interaction_gap_hours"] == 26.5
    assert ec.temporal_state["circadian_phase"] == "active"


# ── celebrate injection ───────────────────────────────────────────────────────

def test_24h_gap_injects_celebrate():
    """interaction_gap_hours >= 24 → learning_advice.preferences["celebrate"] >= 0.82."""
    d = _as_dict({"interaction_gap_hours": 30.0, "has_deferred_threads": False})
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("celebrate", 0.0) >= 0.82, (
        f"Expected celebrate >= 0.82 for 30h gap; got {prefs}"
    )


def test_23h_gap_does_not_inject_celebrate():
    """interaction_gap_hours < 24 → no celebrate injected by temporal."""
    d = _as_dict({"interaction_gap_hours": 23.0, "has_deferred_threads": False})
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    # celebrate may be 0.0 or absent — must not be >= 0.82 from temporal
    assert prefs.get("celebrate", 0.0) < 0.82, (
        f"Should not inject celebrate for 23h gap; got {prefs}"
    )


# ── reflect injection ─────────────────────────────────────────────────────────

def test_deferred_threads_injects_reflect():
    """has_deferred_threads=True → learning_advice.preferences["reflect"] >= 0.70."""
    d = _as_dict({"interaction_gap_hours": 0.5, "has_deferred_threads": True})
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("reflect", 0.0) >= 0.70, (
        f"Expected reflect >= 0.70 when has_deferred_threads; got {prefs}"
    )


def test_no_deferred_threads_no_reflect_injection():
    """has_deferred_threads=False and gap < 24 → no temporal injection."""
    d = _as_dict({"interaction_gap_hours": 1.0, "has_deferred_threads": False})
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    # No temporal injection — reflect should be 0 or absent
    assert prefs.get("reflect", 0.0) < 0.70, (
        f"Should not inject reflect when no deferred threads; got {prefs}"
    )


# ── ec_temporal_state in as_dict() ───────────────────────────────────────────

def test_ec_temporal_state_in_as_dict():
    """as_dict() must expose ec_temporal_state key."""
    td = {"circadian_phase": "low", "interaction_gap_hours": 48.0, "has_deferred_threads": True}
    d = _as_dict(td)
    assert "ec_temporal_state" in d
    assert d["ec_temporal_state"]["circadian_phase"] == "low"


# ── build_executive_context accepts temporal ──────────────────────────────────

def test_build_executive_context_accepts_temporal():
    """build_executive_context() must accept temporal kwarg without error."""
    from runtime.executive_context import build_executive_context
    ec = build_executive_context(
        intent="conversation",
        emotional_context={},
        world=None,
        working_memory=None,
        capabilities=[],
        cognitive_state=None,
        affordances=None,
        attention={},
        temporal={"circadian_phase": "active", "interaction_gap_hours": 25.0, "has_deferred_threads": False},
    )
    assert ec.temporal_state.get("interaction_gap_hours") == 25.0
    d = ec.as_dict()
    la = d.get("learning_advice") or {}
    prefs = la.get("preferences") or {}
    assert prefs.get("celebrate", 0.0) >= 0.82, (
        f"Expected celebrate >= 0.82 for 25h gap via build_executive_context; got {prefs}"
    )
