"""
tests/test_wo_degradation_001.py — WO-DEGRADATION-001

Acceptance criteria:
  DEG-1: CognitiveState has memory_unavailable field (bool, default False)
  DEG-2: CognitiveState has wkg_unavailable field (bool, default False)
  DEG-3: CognitiveState has failed_faculties field (tuple, default empty)
  DEG-4: assemble_cognitive_state sets memory_unavailable=True when memory/wkg both return empty
  DEG-5: assemble_cognitive_state sets wkg_unavailable=True when wkg_context is empty
  DEG-6: assemble_cognitive_state populates failed_faculties with names of failed faculties
"""
import dataclasses
import pytest
from unittest.mock import patch, MagicMock


# ── DEG-1: memory_unavailable on CognitiveState ──────────────────────────────

def test_deg1_memory_unavailable_field():
    """DEG-1: CognitiveState has memory_unavailable bool field defaulting to False"""
    from runtime.contracts import CognitiveState
    field_names = {f.name: f for f in dataclasses.fields(CognitiveState)}
    assert "memory_unavailable" in field_names
    cs = CognitiveState(raw_input="hi")
    assert cs.memory_unavailable is False


# ── DEG-2: wkg_unavailable on CognitiveState ─────────────────────────────────

def test_deg2_wkg_unavailable_field():
    """DEG-2: CognitiveState has wkg_unavailable bool field defaulting to False"""
    from runtime.contracts import CognitiveState
    field_names = {f.name for f in dataclasses.fields(CognitiveState)}
    assert "wkg_unavailable" in field_names
    cs = CognitiveState(raw_input="hi")
    assert cs.wkg_unavailable is False


# ── DEG-3: failed_faculties on CognitiveState ────────────────────────────────

def test_deg3_failed_faculties_field():
    """DEG-3: CognitiveState has failed_faculties tuple field defaulting to empty"""
    from runtime.contracts import CognitiveState
    cs = CognitiveState(raw_input="hi")
    assert isinstance(cs.failed_faculties, tuple)
    assert len(cs.failed_faculties) == 0


# ── DEG-4: memory_unavailable=True when both memory faculties are empty ───────

def test_deg4_memory_unavailable_when_empty():
    """DEG-4: assemble_cognitive_state sets memory_unavailable=True when working_memory=None
    and attention has no high_priority_memory"""
    from runtime.spine.spine import assemble_cognitive_state

    cs = assemble_cognitive_state(
        language={"original": "test", "intent": "test"},
        memory_result=None,
        attention={"high_priority_memory": []},    # empty → no high-priority memories
        capabilities=[],
        vault_result=None,
        prior_state=None,
        working_memory=None,
    )
    assert cs.memory_unavailable is True
    assert "memory" in cs.failed_faculties


# ── DEG-5: wkg_unavailable=True when wkg_context is empty ───────────────────

def test_deg5_wkg_unavailable_when_empty():
    """DEG-5: assemble_cognitive_state sets wkg_unavailable=True when WKG returns empty"""
    from runtime.spine.spine import assemble_cognitive_state

    # With no intent, WKG context stays empty
    cs = assemble_cognitive_state(
        language={"original": "test", "intent": ""},
        memory_result=None,
        attention={"high_priority_memory": []},
        capabilities=[],
        vault_result=None,
        prior_state=None,
        working_memory=None,
    )
    assert cs.wkg_unavailable is True
    assert "wkg" in cs.failed_faculties


# ── DEG-6: failed_faculties names ────────────────────────────────────────────

def test_deg6_failed_faculties_populated():
    """DEG-6: failed_faculties contains 'memory' and 'wkg' when both are empty"""
    from runtime.spine.spine import assemble_cognitive_state

    cs = assemble_cognitive_state(
        language={"original": "test", "intent": ""},
        memory_result=None,
        attention={"high_priority_memory": []},
        capabilities=[],
        vault_result=None,
        prior_state=None,
        working_memory=None,
    )
    assert "memory" in cs.failed_faculties
    assert "wkg" in cs.failed_faculties
    assert isinstance(cs.failed_faculties, tuple)
