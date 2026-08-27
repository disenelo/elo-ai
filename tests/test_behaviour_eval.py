"""
tests/test_behaviour_eval.py

WP_F gap: company_runtime/behaviour_eval.py — behaviour-routing evaluator.
Only the pure-Python deterministic helpers are tested here:
  _is_recall(), _recall_topic(), _make_tts_text(), _resolves_to_sit()
  PASS/FAIL/NA constants, _ASSOCIATIVE/_DIRECT_OK sets, _EVALUATORS registry.

The live routing probes (_cal_decision, _tool_routing, _eval_* family) call
runtime.executive and core.kernel under the LLM — those are verified by
the golden set run (python3 -m company_runtime.behaviour_eval) and not
duplicated here.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_behaviour_eval.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from company_runtime.behaviour_eval import (
    PASS, FAIL, NA,
    _ASSOCIATIVE, _DIRECT_OK,
    _MEMORY_QUERY_TRIGGERS, _RECALL_SKIP,
    _SIT_KEYS_MIRROR,
    _EVALUATORS,
    _is_recall,
    _recall_topic,
    _make_tts_text,
    _resolves_to_sit,
)


def test_constants_defined():
    """AT-1: PASS/FAIL/NA are non-empty strings and distinct from each other."""
    assert isinstance(PASS, str) and PASS, "AT-1: PASS must be a non-empty str"
    assert isinstance(FAIL, str) and FAIL, "AT-1: FAIL must be a non-empty str"
    assert isinstance(NA, str) and NA,     "AT-1: NA must be a non-empty str"
    assert len({PASS, FAIL, NA}) == 3,     "AT-1: PASS/FAIL/NA must be distinct"


def test_associative_and_direct_ok_sets():
    """AT-2: _ASSOCIATIVE and _DIRECT_OK are non-overlapping sets with expected members."""
    for action in ("connect", "reflect", "challenge", "witness"):
        assert action in _ASSOCIATIVE, f"AT-2: {action!r} must be in _ASSOCIATIVE"
    for action in ("answer", "celebrate", "simplify"):
        assert action in _DIRECT_OK, f"AT-2: {action!r} must be in _DIRECT_OK"
    overlap = _ASSOCIATIVE & _DIRECT_OK
    assert not overlap, f"AT-2: _ASSOCIATIVE and _DIRECT_OK must not overlap; got {overlap}"


def test_is_recall_positive_cases():
    """AT-3: _is_recall() returns True for known recall trigger phrases."""
    triggers = [
        "do you remember last time?",
        "what did you say about eLo?",
        "you said we should use sqlite",
        "what do you remember about the roadmap",
        "remind me what we decided",
        "pull something from memory",
    ]
    for phrase in triggers:
        assert _is_recall(phrase) is True, (
            f"AT-3: {phrase!r} must trigger recall; got False"
        )


def test_is_recall_negative_cases():
    """AT-4: _is_recall() returns False for plain non-recall inputs."""
    non_triggers = [
        "hello there",
        "what is eLo?",
        "let's build the module",
        "play some music",
    ]
    for phrase in non_triggers:
        assert _is_recall(phrase) is False, (
            f"AT-4: {phrase!r} must NOT trigger recall; got True"
        )


def test_recall_topic_strips_filler():
    """AT-5: _recall_topic() strips filler question words from recall phrases."""
    topic = _recall_topic("do you remember what we talked about")
    filler = {"what", "you", "remember", "tell", "do", "we", "about"}
    words = set(topic.split())
    overlap = words & filler
    assert not overlap, (
        f"AT-5: topic must not contain filler words; got topic={topic!r}, overlap={overlap}"
    )


def test_recall_topic_extracts_content_word():
    """AT-6: _recall_topic() keeps content words of >=3 chars not in _RECALL_SKIP."""
    topic = _recall_topic("what do you remember about the kickstarter plan")
    assert "kickstarter" in topic, (
        f"AT-6: 'kickstarter' must survive in recall topic; got {topic!r}"
    )


def test_make_tts_joins_all_bubbles():
    """AT-7: _make_tts_text() joins multi-paragraph response; tail sentence is present."""
    sample = ("Start by checking your OS audio output device.\n\n"
              "If that looks right, try restarting the CoreAudio daemon.")
    tts = _make_tts_text(sample)
    assert isinstance(tts, str), f"AT-7: must return str; got {type(tts)}"
    assert "CoreAudio" in tts, (
        f"AT-7: tail bubble must be present in joined TTS text; got {tts!r}"
    )


def test_make_tts_respects_max_chars():
    """AT-8: _make_tts_text() never exceeds tts_max characters."""
    long_response = "Sentence. " * 200
    tts = _make_tts_text(long_response, tts_max=200)
    assert len(tts) <= 200, f"AT-8: tts text must be <=200 chars; got {len(tts)}"


def test_resolves_to_sit_positive():
    """AT-9: _resolves_to_sit() returns True for sit-command phrases."""
    sit_phrases = [
        "come sit with me",
        "come here please",
        "sit beside me",
        "sit down with me",
        "walk to me",
    ]
    for phrase in sit_phrases:
        assert _resolves_to_sit(phrase) is True, (
            f"AT-9: {phrase!r} must resolve to sit; got False"
        )


def test_resolves_to_sit_negative():
    """AT-10: _resolves_to_sit() returns False for non-sit inputs."""
    non_sit = [
        "play some music",
        "let's build this",
        "what is the weather",
        "hello eLo",
    ]
    for phrase in non_sit:
        assert _resolves_to_sit(phrase) is False, (
            f"AT-10: {phrase!r} must NOT resolve to sit; got True"
        )


def test_evaluators_registry_has_expected_keys():
    """AT-11: _EVALUATORS registry contains all golden set case IDs."""
    expected = {
        "GS-ROUTE-01", "GS-ROUTE-02", "GS-ROUTE-03", "GS-ROUTE-04",
        "GS-LOOP-01", "GS-VOICE-01",
        "GS-MEM-01", "GS-MEM-02",
        "GS-BEHAV-01", "GS-BEHAV-02", "GS-BEHAV-03", "GS-BEHAV-04",
        "GS-SAYDO-01", "GS-SAYDO-02", "GS-SAYDO-03",
    }
    for key in expected:
        assert key in _EVALUATORS, f"AT-11: _EVALUATORS missing {key!r}"


if __name__ == "__main__":
    _tests = [
        ("AT-1",  test_constants_defined),
        ("AT-2",  test_associative_and_direct_ok_sets),
        ("AT-3",  test_is_recall_positive_cases),
        ("AT-4",  test_is_recall_negative_cases),
        ("AT-5",  test_recall_topic_strips_filler),
        ("AT-6",  test_recall_topic_extracts_content_word),
        ("AT-7",  test_make_tts_joins_all_bubbles),
        ("AT-8",  test_make_tts_respects_max_chars),
        ("AT-9",  test_resolves_to_sit_positive),
        ("AT-10", test_resolves_to_sit_negative),
        ("AT-11", test_evaluators_registry_has_expected_keys),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"behaviour_eval   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
