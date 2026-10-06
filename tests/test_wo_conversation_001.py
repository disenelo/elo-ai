"""
tests/test_wo_conversation_001.py — WO-CONVERSATION-001: conversation context in vault

Acceptance criteria:
  CONV-1: conversation_state.get_last_elo_response() returns what was set
  CONV-2: update_after_response() updates active_topic
  CONV-3: topic_changed() fires correctly on topic shift
  CONV-4: MemoryCandidate accepts active_topic, referents, author, thread_history
  CONV-5: vault write carries active_topic in YAML frontmatter
  CONV-6: CognitiveState has last_elo_response field
"""
import pytest


# ── CONV-1: last_elo_response round-trip ──────────────────────────────────────

def test_conv1_last_elo_response():
    """CONV-1: update_after_response stores truncated response correctly"""
    from runtime.conversation_state import update_after_response, get_last_elo_response, reset
    reset()
    update_after_response(elo_response="hello world", active_topic="greeting")
    assert get_last_elo_response() == "hello world"


# ── CONV-2: active_topic tracking ─────────────────────────────────────────────

def test_conv2_active_topic_updates():
    """CONV-2: active_topic tracks current conversation topic"""
    from runtime.conversation_state import update_after_response, get_active_topic, reset
    reset()
    update_after_response(elo_response="yes", active_topic="elo_robot")
    assert get_active_topic() == "elo_robot"
    update_after_response(elo_response="ok", active_topic="elo_game")
    assert get_active_topic() == "elo_game"


# ── CONV-3: topic_changed detection ───────────────────────────────────────────

def test_conv3_topic_changed():
    """CONV-3: topic_changed() is True after a topic shift"""
    from runtime.conversation_state import update_after_response, topic_changed, reset
    reset()
    update_after_response(elo_response="one", active_topic="elo_robot")
    assert not topic_changed()  # first topic — no previous to compare
    update_after_response(elo_response="two", active_topic="elo_game")
    assert topic_changed()


# ── CONV-4: MemoryCandidate accepts new fields ────────────────────────────────

def test_conv4_memory_candidate_fields():
    """CONV-4: MemoryCandidate accepts active_topic, referents, author, thread_history"""
    from memory.memory_faculty import MemoryCandidate
    mc = MemoryCandidate(
        source_faculty="interaction",
        content="David talked about eLo robot barkcloth",
        active_topic="elo_robot",
        referents={"it": "eLo robot", "that": "barkcloth"},
        author="elo",
        thread_history=({"topic": "elo_game", "turns": 2},),
        epistemic_class="conversation",
    )
    assert mc.active_topic == "elo_robot"
    assert mc.referents == {"it": "eLo robot", "that": "barkcloth"}
    assert mc.author == "elo"
    assert len(mc.thread_history) == 1


# ── CONV-5: vault write carries active_topic ──────────────────────────────────

def test_conv5_vault_write_has_active_topic():
    """CONV-5: write_memory writes active_topic to YAML frontmatter"""
    import os, tempfile
    from unittest.mock import patch
    from memory import vault_layer

    # Write to a temp vault and check the summary note
    with tempfile.TemporaryDirectory() as tmp:
        with (
            patch.object(vault_layer, "_SUM_DIR", os.path.join(tmp, "summary")),
            patch.object(vault_layer, "_DEEP_DIR", os.path.join(tmp, "deep")),
            patch.object(vault_layer, "_SPOT_FILE", os.path.join(tmp, "spots.csv")),
        ):
            os.makedirs(os.path.join(tmp, "summary"), exist_ok=True)
            os.makedirs(os.path.join(tmp, "deep"), exist_ok=True)
            # Patch obsidian_loader.invalidate_cache to no-op
            import memory.obsidian_loader as _ol
            with patch.object(_ol, "invalidate_cache", lambda: None):
                spot = vault_layer.write_memory(
                    project="general",
                    memory_type="conversation",
                    summary="test summary",
                    deep_text="test content",
                    epistemic_class="conversation",
                    active_topic="elo_robot",
                    author="elo",
                )
        # Find the written summary note
        summary_dir = os.path.join(tmp, "summary")
        files = os.listdir(summary_dir)
        assert files, "No summary file written"
        with open(os.path.join(summary_dir, files[0]), encoding="utf-8") as f:
            content = f.read()
        assert "active_topic: elo_robot" in content
        assert "author: elo" in content


# ── CONV-6: CognitiveState has last_elo_response ──────────────────────────────

def test_conv6_cognitive_state_last_elo_response():
    """CONV-6: CognitiveState dataclass has last_elo_response field"""
    from runtime.contracts import CognitiveState
    cs = CognitiveState()
    assert hasattr(cs, "last_elo_response")
    assert cs.last_elo_response == ""
    cs2 = CognitiveState(last_elo_response="previous response")
    assert cs2.last_elo_response == "previous response"
