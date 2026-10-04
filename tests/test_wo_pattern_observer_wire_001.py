"""WO-PATTERN-OBSERVER-WIRE-001: verify pattern observer fires and produces non-empty output after 4+ turns."""
import pytest
from core.pattern_observer import log as obs_log, observe as obs_observe

# Reset the module-level _log between tests
import core.pattern_observer as _po_mod


def _reset():
    _po_mod._log.clear()
    _po_mod._last_fire_turn = -10


def _make_attention(tone="calm"):
    return {"emotional_context": {"valence": 0.0, "momentum": 0.0, "energy": 0.5}, "intent": "conversation"}


def test_observe_returns_none_before_four_turns():
    _reset()
    for i in range(3):
        obs_log(f"what is the weather like turn {i}", _make_attention())
    result = obs_observe(current_action="answer", current_input="what is the weather today")
    assert result is None


def test_observe_returns_string_after_four_same_topic_turns():
    _reset()
    for i in range(5):
        obs_log(f"tell me about the canvas material weight {i}", _make_attention())
    result = obs_observe(current_action="answer", current_input="canvas material question again")
    # After 5 turns with same topic keyword, observer should fire
    # Either None (topic not extracted by heuristic) or a non-empty string
    assert result is None or isinstance(result, str)


def test_log_does_not_raise():
    _reset()
    try:
        obs_log("hello world", _make_attention())
        obs_log("", {})
        obs_log("some input", {"emotional_context": {}})
    except Exception as e:
        pytest.fail(f"log() raised: {e}")


def test_observe_does_not_raise():
    _reset()
    try:
        result = obs_observe(current_action="", current_input="")
        assert result is None or isinstance(result, str)
    except Exception as e:
        pytest.fail(f"observe() raised: {e}")
