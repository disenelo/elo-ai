"""
tests/test_wo_rel001_intent_relationship_validation.py

WO-REL-001: §1 Build List — Intent / Relationship validation (WP_F gap closure).
Proves relationship_faculty and intent_engine are correctly implemented,
wired, and produce the correct output shapes.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_rel001_intent_relationship_validation.py -q
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────────────────────────────────────
# relationship_faculty acceptance tests
# ─────────────────────────────────────────────────────────────────────────────

def test_rel_returns_relationship_context():
    """AT-1: analyse() returns a RelationshipContext, never None."""
    from runtime.spine.relationship_faculty import analyse, RelationshipContext
    result = analyse("let's work on the game today")
    assert isinstance(result, RelationshipContext), (
        f"AT-1: expected RelationshipContext, got {type(result)}"
    )


def test_rel_south_ldn_mode_detected():
    """AT-2: SOUTH_LDN_MODE detected when south london signals present."""
    from runtime.spine.relationship_faculty import analyse
    result = analyse("wagwan bruv, that's peak innit")
    assert result.register == "SOUTH_LDN_MODE", (
        f"AT-2: expected SOUTH_LDN_MODE; got {result.register!r}"
    )


def test_rel_patois_mode_detected():
    """AT-3: PATOIS_MODE detected when patois signals present."""
    from runtime.spine.relationship_faculty import analyse
    result = analyse("jah bless, give thanks one love irie")
    assert result.register == "PATOIS_MODE", (
        f"AT-3: expected PATOIS_MODE; got {result.register!r}"
    )


def test_rel_hybrid_mode_detected():
    """AT-4: HYBRID_MODE detected when both signal sets present."""
    from runtime.spine.relationship_faculty import analyse
    result = analyse("wagwan jah bless innit rastafari bruv")
    assert result.register == "HYBRID_MODE", (
        f"AT-4: expected HYBRID_MODE; got {result.register!r}"
    )


def test_rel_active_projects_detected():
    """AT-5: Active DISENELO project names detected from input signals."""
    from runtime.spine.relationship_faculty import analyse
    result = analyse("let's work on elo os and the game today")
    assert "elo os" in result.active_projects, (
        f"AT-5: 'elo os' not in active_projects: {result.active_projects}"
    )
    assert "game" in result.active_projects, (
        f"AT-5: 'game' not in active_projects: {result.active_projects}"
    )


def test_rel_expression_posture_thresholds():
    """AT-6: expression_posture follows familiarity thresholds.
    familiarity >= 0.82 → 'close', >= 0.62 → 'warm', else → 'open'.
    """
    from runtime.spine.relationship_faculty import (
        _expression_posture as _ep,
    )
    assert _ep(0.90) == "close",  f"AT-6: 0.90 → expected 'close'; got {_ep(0.90)!r}"
    assert _ep(0.70) == "warm",   f"AT-6: 0.70 → expected 'warm'; got {_ep(0.70)!r}"
    assert _ep(0.50) == "open",   f"AT-6: 0.50 → expected 'open'; got {_ep(0.50)!r}"


def test_rel_familiarity_grows_with_sessions():
    """AT-7: familiarity increases as session count grows."""
    from runtime.spine.relationship_faculty import _compute_familiarity as _cf
    f_0   = _cf(0, {})
    f_10  = _cf(10, {})
    f_50  = _cf(50, {})
    assert f_0 < f_10 < f_50 <= 0.98, (
        f"AT-7: familiarity must grow with sessions and cap at 0.98; "
        f"got {f_0:.3f} / {f_10:.3f} / {f_50:.3f}"
    )


def test_rel_flows_into_cognitive_plan():
    """AT-8: relationship context flows into CognitivePlan via enrich().
    relationship_type, familiarity, trust, expression_posture present on plan.
    """
    from runtime.spine.relationship_faculty import analyse
    from runtime.spine.executive_faculty import enrich
    from runtime.spine.plan import CognitivePlan

    plan = CognitivePlan()
    rel  = analyse("let's build something today")
    enriched = enrich(plan, rel, attention=None)

    assert enriched.relationship_type  == "creator",  f"AT-8: relationship_type missing"
    assert isinstance(enriched.familiarity, float),   f"AT-8: familiarity not float"
    assert isinstance(enriched.trust, float),         f"AT-8: trust not float"
    assert enriched.expression_posture in ("close", "warm", "open"), (
        f"AT-8: expression_posture invalid: {enriched.expression_posture!r}"
    )
    assert isinstance(enriched.emotional_vector, dict), f"AT-8: emotional_vector not dict"


# ─────────────────────────────────────────────────────────────────────────────
# intent_engine acceptance tests
# ─────────────────────────────────────────────────────────────────────────────

def test_intent_returns_required_keys():
    """AT-9: detect() returns dict with intent, confidence, category keys."""
    from runtime.router.intent_engine import detect
    result = detect("what were we working on yesterday")
    assert isinstance(result, dict), f"AT-9: detect() must return dict"
    for key in ("intent", "confidence", "category"):
        assert key in result, f"AT-9: missing key '{key}' in detect() result"


def test_intent_memory_category():
    """AT-10: memory-related input maps to memory intent."""
    from runtime.router.intent_engine import detect
    result = detect("what were we working on last time")
    assert result.get("intent") == "memory" or result.get("category") in ("Reflect", "memory"), (
        f"AT-10: expected memory intent for recall input; got {result}"
    )


def test_intent_file_ops_category():
    """AT-11: file-operation input maps to file_ops intent."""
    from runtime.router.intent_engine import detect
    result = detect("move this file to the desktop folder")
    assert result.get("intent") == "file_ops", (
        f"AT-11: expected file_ops intent; got intent={result.get('intent')!r}"
    )


def test_intent_confidence_is_float_in_range():
    """AT-12: confidence is a float in [0.0, 1.0]."""
    from runtime.router.intent_engine import detect
    result = detect("let's continue")
    conf = result.get("confidence", -1)
    assert isinstance(conf, (int, float)), f"AT-12: confidence must be numeric"
    assert 0.0 <= conf <= 1.0, f"AT-12: confidence out of range: {conf}"
