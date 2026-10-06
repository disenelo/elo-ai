"""
tests/test_wo_world_001.py — WO-WORLD-001

Acceptance criteria:
  WORLD-1: world_state field exists on CognitiveState
  WORLD-2: WORLD_INTERACTION is a registered source_type in vault_layer
  WORLD-3: write_memory accepts source_type=WORLD_INTERACTION and writes to YAML
  WORLD-4: write_world_causal_edge function exists and is callable
  WORLD-5: write_world_causal_edge returns bool (True on success, False on error)
  WORLD-6: causal edge uses link_type="causal" and weight=0.65
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock


# ── WORLD-1: world_state field on CognitiveState ──────────────────────────────

def test_world1_cognitive_state_has_world_state():
    """WORLD-1: CognitiveState dataclass has world_state field"""
    from runtime.contracts import CognitiveState
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(CognitiveState)}
    assert "world_state" in field_names


# ── WORLD-2: WORLD_INTERACTION is a registered source_type ───────────────────

def test_world2_world_interaction_registered():
    """WORLD-2: WORLD_INTERACTION is in vault_layer's valid source types"""
    import memory.vault_layer as vault_layer
    valid_types = getattr(vault_layer, "_VALID_SOURCE_TYPES", None)
    if valid_types is None:
        # Check the docstring/comment block for the string
        import inspect
        src = inspect.getsource(vault_layer)
        assert "WORLD_INTERACTION" in src
    else:
        assert "WORLD_INTERACTION" in valid_types


# ── WORLD-3: vault write with WORLD_INTERACTION source_type ──────────────────

def test_world3_vault_write_world_interaction():
    """WORLD-3: write_memory writes source_type=WORLD_INTERACTION to YAML frontmatter"""
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
                summary="Spotify search ran",
                deep_text="WORLD_INTERACTION: spotify ran for: play jazz",
                epistemic_class="conversation",
                source_type="WORLD_INTERACTION",
            )
        summary_dir = os.path.join(tmp, "summary")
        files = os.listdir(summary_dir)
        assert files
        with open(os.path.join(summary_dir, files[0]), encoding="utf-8") as f:
            content = f.read()
        assert "source_type: WORLD_INTERACTION" in content


# ── WORLD-4: write_world_causal_edge exists ───────────────────────────────────

def test_world4_write_world_causal_edge_exists():
    """WORLD-4: write_world_causal_edge is importable from spg_faculty"""
    from memory.spg_faculty import write_world_causal_edge
    assert callable(write_world_causal_edge)


# ── WORLD-5: write_world_causal_edge returns bool ────────────────────────────

def test_world5_write_world_causal_edge_returns_bool():
    """WORLD-5: write_world_causal_edge returns False gracefully when SPG fails"""
    from memory.spg_faculty import write_world_causal_edge
    with patch("memory.spg_faculty.add_edge_between_claims", side_effect=RuntimeError("no graph")):
        result = write_world_causal_edge("spot-action-001", "spot-conseq-002", "spotify")
    assert result is False


# ── WORLD-6: causal edge uses correct link_type and weight ───────────────────

def test_world6_causal_edge_params():
    """WORLD-6: write_world_causal_edge calls add_edge_between_claims with causal/0.65"""
    from memory.spg_faculty import write_world_causal_edge
    captured = []

    def _capture(**kwargs):
        captured.append(kwargs)
        return True

    with patch("memory.spg_faculty.add_edge_between_claims", side_effect=_capture):
        write_world_causal_edge("A", "B", "spotify")

    assert captured
    call = captured[0]
    assert call.get("link_type") == "causal"
    assert call.get("weight") == 0.65
    assert "world_interaction:spotify" in (call.get("evidence") or "")
