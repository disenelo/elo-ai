"""
tests/test_wo_simulation_001.py — WO-SIMULATION-001

Acceptance criteria:
  SIM-1: simulation_tracker.add_pending / get_pending_actions round-trip
  SIM-2: mark_executed moves action from pending → executed
  SIM-3: record_turn_actions with auto_execute=True populates executed_actions
  SIM-4: record_turn_actions with auto_execute=False populates pending_actions
  SIM-5: reset clears all state
  SIM-6: content_type field on MemoryCandidate
  SIM-7: vault_layer.write_memory accepts content_type in YAML frontmatter
  SIM-8: CognitiveState has pending_actions and executed_actions fields
"""
import os
import tempfile
import pytest
from unittest.mock import patch


# ── SIM-1: add_pending / get_pending_actions ─────────────────────────────────

def test_sim1_add_and_get_pending():
    """SIM-1: add_pending registers action; get_pending_actions returns it"""
    import runtime.simulation_tracker as st
    st.reset()
    st.add_pending("tool")
    result = st.get_pending_actions()
    assert "tool" in result


# ── SIM-2: mark_executed moves action ────────────────────────────────────────

def test_sim2_mark_executed_moves():
    """SIM-2: mark_executed removes from pending and adds to executed"""
    import runtime.simulation_tracker as st
    st.reset()
    st.add_pending("llm")
    st.mark_executed("llm")
    assert "llm" not in st.get_pending_actions()
    assert "llm" in st.get_executed_actions()


# ── SIM-3: record_turn_actions auto_execute=True ─────────────────────────────

def test_sim3_record_turn_auto_execute():
    """SIM-3: record_turn_actions with auto_execute=True populates executed"""
    import runtime.simulation_tracker as st
    st.reset()
    st.record_turn_actions(["tool", "llm", "voice"], auto_execute=True)
    executed = st.get_executed_actions()
    assert "tool" in executed
    assert "llm" in executed
    assert "voice" in executed
    assert len(st.get_pending_actions()) == 0


# ── SIM-4: record_turn_actions auto_execute=False ────────────────────────────

def test_sim4_record_turn_no_auto_execute():
    """SIM-4: record_turn_actions with auto_execute=False populates pending"""
    import runtime.simulation_tracker as st
    st.reset()
    st.record_turn_actions(["speculative_tool"], auto_execute=False)
    assert "speculative_tool" in st.get_pending_actions()
    assert "speculative_tool" not in st.get_executed_actions()


# ── SIM-5: reset clears all state ────────────────────────────────────────────

def test_sim5_reset_clears_state():
    """SIM-5: reset() empties both pending and executed"""
    import runtime.simulation_tracker as st
    st.add_pending("a")
    st.mark_executed("b")
    st.reset()
    assert len(st.get_pending_actions()) == 0
    assert len(st.get_executed_actions()) == 0


# ── SIM-6: content_type field on MemoryCandidate ─────────────────────────────

def test_sim6_memory_candidate_content_type():
    """SIM-6: MemoryCandidate accepts content_type field"""
    from memory.memory_faculty import MemoryCandidate
    mc = MemoryCandidate(
        source_faculty="interaction",
        content="test content",
        epistemic_class="conversation",
        content_type="ASSERTED",
    )
    assert mc.content_type == "ASSERTED"


# ── SIM-7: vault writes content_type to YAML frontmatter ─────────────────────

def test_sim7_vault_write_has_content_type():
    """SIM-7: write_memory writes content_type to YAML frontmatter"""
    import memory.vault_layer as vault_layer
    import memory.obsidian_loader as _ol

    with tempfile.TemporaryDirectory() as tmp:
        with (
            patch.object(vault_layer, "_SUM_DIR", os.path.join(tmp, "summary")),
            patch.object(vault_layer, "_DEEP_DIR", os.path.join(tmp, "deep")),
            patch.object(vault_layer, "_SPOT_FILE", os.path.join(tmp, "spots.csv")),
            patch.object(_ol, "invalidate_cache", lambda: None),
        ):
            os.makedirs(os.path.join(tmp, "summary"), exist_ok=True)
            os.makedirs(os.path.join(tmp, "deep"), exist_ok=True)
            vault_layer.write_memory(
                project="general",
                memory_type="conversation",
                summary="test sim",
                deep_text="test content for simulation",
                epistemic_class="conversation",
                content_type="SIMULATED",
            )
        summary_dir = os.path.join(tmp, "summary")
        files = os.listdir(summary_dir)
        assert files
        with open(os.path.join(summary_dir, files[0]), encoding="utf-8") as f:
            content = f.read()
        assert "content_type: SIMULATED" in content


# ── SIM-8: CognitiveState has pending/executed fields ────────────────────────

def test_sim8_cognitive_state_fields():
    """SIM-8: CognitiveState dataclass has pending_actions and executed_actions"""
    from runtime.contracts import CognitiveState
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(CognitiveState)}
    assert "pending_actions" in field_names
    assert "executed_actions" in field_names
