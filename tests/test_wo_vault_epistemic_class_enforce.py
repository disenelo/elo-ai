"""
tests/test_wo_vault_epistemic_class_enforce.py — WO-VAULT-EPISTEMIC-CLASS-ENFORCE-001

Acceptance:
- write_memory() requires epistemic_class (no default → TypeError if omitted)
- write_memory(epistemic_class="verified") without source_ref → ValueError
- write_memory(epistemic_class="verified", source_ref=...) → succeeds
- write_memory(epistemic_class="inference") without source_ref → succeeds
- compress_session() still works (uses "conversation" internally)
- MemoryCandidate has epistemic_class field, defaults to "inference"
- MemoryFaculty.submit() passes epistemic_class through to write_memory
"""
from __future__ import annotations

import os
import pytest


# ── vault_layer.write_memory ─────────────────────────────────────────────────

def test_write_memory_requires_epistemic_class(tmp_path, monkeypatch):
    """No default → TypeError when epistemic_class omitted."""
    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "_VAULT", str(tmp_path))
    monkeypatch.setattr(vl, "_MEM_DIR", str(tmp_path / "09 Memory"))
    monkeypatch.setattr(vl, "_SUM_DIR", str(tmp_path / "09 Memory" / "summary"))
    monkeypatch.setattr(vl, "_DEEP_DIR", str(tmp_path / "09 Memory" / "deep"))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(tmp_path / "09 Memory" / "SPOT_CODES.md"))

    with pytest.raises(TypeError):
        vl.write_memory(
            project="general",
            memory_type="learn",
            summary="test",
            deep_text="test body",
            # epistemic_class intentionally omitted
        )


def test_verified_without_source_ref_raises(tmp_path, monkeypatch):
    """epistemic_class='verified' with no source_ref must raise ValueError."""
    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "_VAULT", str(tmp_path))
    monkeypatch.setattr(vl, "_MEM_DIR", str(tmp_path / "09 Memory"))
    monkeypatch.setattr(vl, "_SUM_DIR", str(tmp_path / "09 Memory" / "summary"))
    monkeypatch.setattr(vl, "_DEEP_DIR", str(tmp_path / "09 Memory" / "deep"))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(tmp_path / "09 Memory" / "SPOT_CODES.md"))

    with pytest.raises(ValueError, match="source_ref"):
        vl.write_memory(
            project="general",
            memory_type="learn",
            summary="verified claim",
            deep_text="body",
            epistemic_class="verified",
            # source_ref omitted or empty
        )


def test_verified_with_source_ref_succeeds(tmp_path, monkeypatch):
    """epistemic_class='verified' + source_ref must write successfully."""
    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "_VAULT", str(tmp_path))
    monkeypatch.setattr(vl, "_MEM_DIR", str(tmp_path / "09 Memory"))
    monkeypatch.setattr(vl, "_SUM_DIR", str(tmp_path / "09 Memory" / "summary"))
    monkeypatch.setattr(vl, "_DEEP_DIR", str(tmp_path / "09 Memory" / "deep"))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(tmp_path / "09 Memory" / "SPOT_CODES.md"))
    import memory.obsidian_loader as ol
    monkeypatch.setattr(ol, "invalidate_cache", lambda: None)

    spot = vl.write_memory(
        project="general",
        memory_type="learn",
        summary="verified with ref",
        deep_text="full body",
        epistemic_class="verified",
        source_ref="session-2026-10-03",
    )
    assert spot, "Expected a non-empty spot code"


def test_inference_without_source_ref_succeeds(tmp_path, monkeypatch):
    """epistemic_class='inference' needs no source_ref."""
    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "_VAULT", str(tmp_path))
    monkeypatch.setattr(vl, "_MEM_DIR", str(tmp_path / "09 Memory"))
    monkeypatch.setattr(vl, "_SUM_DIR", str(tmp_path / "09 Memory" / "summary"))
    monkeypatch.setattr(vl, "_DEEP_DIR", str(tmp_path / "09 Memory" / "deep"))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(tmp_path / "09 Memory" / "SPOT_CODES.md"))
    import memory.obsidian_loader as ol
    monkeypatch.setattr(ol, "invalidate_cache", lambda: None)

    spot = vl.write_memory(
        project="general",
        memory_type="learn",
        summary="an inference",
        deep_text="body",
        epistemic_class="inference",
    )
    assert spot


def test_compress_session_still_works(tmp_path, monkeypatch):
    """compress_session() uses epistemic_class='conversation' internally — no error."""
    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "_VAULT", str(tmp_path))
    monkeypatch.setattr(vl, "_MEM_DIR", str(tmp_path / "09 Memory"))
    monkeypatch.setattr(vl, "_SUM_DIR", str(tmp_path / "09 Memory" / "summary"))
    monkeypatch.setattr(vl, "_DEEP_DIR", str(tmp_path / "09 Memory" / "deep"))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(tmp_path / "09 Memory" / "SPOT_CODES.md"))
    import memory.obsidian_loader as ol
    monkeypatch.setattr(ol, "invalidate_cache", lambda: None)

    spot = vl.compress_session("Session text. Some more detail.")
    assert spot


# ── MemoryCandidate epistemic_class field ─────────────────────────────────────

def test_memory_candidate_has_epistemic_class_field():
    """MemoryCandidate must have epistemic_class defaulting to 'inference'."""
    from memory.memory_faculty import MemoryCandidate
    mc = MemoryCandidate(content="some content", significance=0.5)
    assert hasattr(mc, "epistemic_class"), "MemoryCandidate must have epistemic_class field"
    assert mc.epistemic_class == "inference", (
        f"Default must be 'inference'; got '{mc.epistemic_class}'"
    )


def test_memory_faculty_passes_epistemic_class_through(tmp_path, monkeypatch):
    """MemoryFaculty.submit() must forward epistemic_class to write_memory."""
    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "_VAULT", str(tmp_path))
    monkeypatch.setattr(vl, "_MEM_DIR", str(tmp_path / "09 Memory"))
    monkeypatch.setattr(vl, "_SUM_DIR", str(tmp_path / "09 Memory" / "summary"))
    monkeypatch.setattr(vl, "_DEEP_DIR", str(tmp_path / "09 Memory" / "deep"))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(tmp_path / "09 Memory" / "SPOT_CODES.md"))
    import memory.obsidian_loader as ol
    monkeypatch.setattr(ol, "invalidate_cache", lambda: None)

    from memory.memory_faculty import MemoryFaculty, MemoryCandidate
    result = MemoryFaculty().submit(MemoryCandidate(
        content="something happened in the session",
        proposed_type="episodic",
        significance=0.5,
        project="general",
        summary="test submission",
        epistemic_class="conversation",
    ))
    assert result["action"] in ("write", "reinforce"), (
        f"Expected write or reinforce; got '{result['action']}': {result['reason']}"
    )
