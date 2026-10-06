"""
tests/test_wo_intentions_001.py — WO-INTENTIONS-001: active_intentions in vault + project_id

Acceptance criteria:
  INT-1: project_id field on MemoryCandidate
  INT-2: write_memory carries project_id in YAML frontmatter
  INT-3: persist_active_intentions_to_vault() returns None when no open intentions
  INT-4: persist_active_intentions_to_vault() returns spot when intentions exist
  INT-5: vault entry for intentions has source_type=INTERNAL and epistemic_class=canonical
"""
import json
import os
import tempfile
import pytest
from unittest.mock import patch


# ── INT-1: project_id on MemoryCandidate ──────────────────────────────────────

def test_int1_memory_candidate_project_id():
    """INT-1: MemoryCandidate accepts project_id field"""
    from memory.memory_faculty import MemoryCandidate
    mc = MemoryCandidate(
        source_faculty="interaction",
        content="test content",
        epistemic_class="conversation",
        project_id="elo_robot",
    )
    assert mc.project_id == "elo_robot"


# ── INT-2: write_memory carries project_id in YAML ────────────────────────────

def test_int2_vault_write_has_project_id():
    """INT-2: write_memory writes project_id to YAML frontmatter"""
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
                summary="test",
                deep_text="test content",
                epistemic_class="conversation",
                project_id="elo_planet",
            )
        summary_dir = os.path.join(tmp, "summary")
        files = os.listdir(summary_dir)
        assert files
        with open(os.path.join(summary_dir, files[0]), encoding="utf-8") as f:
            content = f.read()
        assert "project_id: elo_planet" in content


# ── INT-3: persist returns None when no open intentions ───────────────────────

def test_int3_persist_empty():
    """INT-3: persist_active_intentions_to_vault returns None with empty store"""
    from memory.intentions import persist_active_intentions_to_vault
    with patch("memory.intentions.open_intentions", return_value=[]):
        result = persist_active_intentions_to_vault()
    assert result is None


# ── INT-4: persist returns spot when intentions exist ─────────────────────────

def test_int4_persist_with_intentions():
    """INT-4: persist_active_intentions_to_vault writes vault entry and returns spot"""
    from memory.intentions import persist_active_intentions_to_vault, Intention
    mock_intent = Intention(
        intention_id="test-123",
        content="Finish eLo robot NeoPixel integration",
        status="ACTIVE",
        priority=0.8,
    )
    mock_result = {"action": "write", "spot": "TEST·SPOT·001"}

    with (
        patch("memory.intentions.open_intentions", return_value=[mock_intent]),
        patch("memory.memory_faculty.MemoryFaculty.submit", return_value=mock_result),
    ):
        result = persist_active_intentions_to_vault()
    assert result == "TEST·SPOT·001"


# ── INT-5: intentions vault entry has INTERNAL source_type ───────────────────

def test_int5_intentions_vault_source_type():
    """INT-5: intentions vault entry is written with source_type=INTERNAL and epistemic_class=canonical"""
    from memory.intentions import persist_active_intentions_to_vault, Intention
    from memory.memory_faculty import MemoryCandidate

    captured = []

    def _capture_submit(self, candidate: MemoryCandidate):
        captured.append(candidate)
        return {"action": "write", "spot": "TEST·SPOT·002"}

    mock_intent = Intention(
        intention_id="test-456",
        content="build eLo robot",
        status="ACTIVE",
        priority=0.9,
    )
    from memory.memory_faculty import MemoryFaculty
    with (
        patch("memory.intentions.open_intentions", return_value=[mock_intent]),
        patch.object(MemoryFaculty, "submit", _capture_submit),
    ):
        persist_active_intentions_to_vault()

    assert captured
    cand = captured[0]
    assert getattr(cand, "source_type", None) == "INTERNAL" or cand.tags[1] == "INTERNAL"
    assert cand.epistemic_class == "canonical"
    assert cand.source_faculty == "intentions"
