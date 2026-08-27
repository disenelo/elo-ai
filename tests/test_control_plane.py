"""
tests/test_control_plane.py

WP_F gap: runtime/spine/control_plane.py — Memory Arbitration Layer.
L1→L2→L3 memory hierarchy, session mode detection, speak-mode contract.
Pure Python — no LLM calls. Deterministic and testable in isolation.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_control_plane.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.spine.control_plane import (
    ControlPlaneResult,
    SESSION_CREATION, SESSION_RESEARCH, SESSION_FLOW, SESSION_STANDARD,
    run,
    _detect_session_mode,
    _is_memory_query,
    _compress_l2,
    _speak_mode_for,
)


def test_session_mode_creation_detected():
    """AT-1: CREATION_SIGNALS → SESSION_CREATION."""
    assert _detect_session_mode("let's build this module") == SESSION_CREATION
    assert _detect_session_mode("how do we wire the router") == SESSION_CREATION


def test_session_mode_research_detected():
    """AT-2: RESEARCH_SIGNALS → SESSION_RESEARCH."""
    assert _detect_session_mode("what if we tried a different approach") == SESSION_RESEARCH
    assert _detect_session_mode("could we explore an alternative") == SESSION_RESEARCH


def test_session_mode_flow_detected():
    """AT-3: FLOW_SIGNALS → SESSION_FLOW (priority over creation)."""
    assert _detect_session_mode("never mind, ignore that") == SESSION_FLOW


def test_session_mode_standard_default():
    """AT-4: no signals → SESSION_STANDARD."""
    assert _detect_session_mode("hello there") == SESSION_STANDARD


def test_memory_query_detection():
    """AT-5: MEMORY_SIGNALS → is_memory_query returns True."""
    assert _is_memory_query("do you remember last time?") is True
    assert _is_memory_query("you said we should use X") is True
    assert _is_memory_query("what was the approach we took?") is True
    assert _is_memory_query("just hello") is False


def test_l2_compress_strips_blank_and_dividers():
    """AT-6: _compress_l2 returns max 7 non-blank, non-divider lines."""
    vault = "line one\n---\nline two\n\nline three\n===\nline four"
    compressed = _compress_l2(vault)
    lines = compressed.split("\n")
    for ln in lines:
        assert not ln.startswith("---") and not ln.startswith("==="), (
            f"AT-6: compressed must not contain dividers; got {compressed!r}"
        )
    assert len(lines) <= 7, f"AT-6: must have <=7 lines; got {len(lines)}"


def test_speak_mode_flow_is_silent():
    """AT-7: SESSION_FLOW → speak_mode = 'silent'."""
    assert _speak_mode_for(SESSION_FLOW, True) == "silent"
    assert _speak_mode_for(SESSION_FLOW, False) == "silent"


def test_speak_mode_creation_no_memory_is_step_back():
    """AT-8: SESSION_CREATION + no memory → speak_mode = 'step_back'."""
    assert _speak_mode_for(SESSION_CREATION, False) == "step_back"


def test_speak_mode_creation_with_memory_is_speak():
    """AT-9: SESSION_CREATION + memory → speak_mode = 'speak'."""
    assert _speak_mode_for(SESSION_CREATION, True) == "speak"


def test_run_returns_controlplane_result():
    """AT-10: run() returns ControlPlaneResult with session_mode populated."""
    result = run("let's build the pipeline")
    assert isinstance(result, ControlPlaneResult), (
        f"AT-10: run() must return ControlPlaneResult; got {type(result)}"
    )
    assert result.session_mode == SESSION_CREATION, (
        f"AT-10: 'build' input must yield SESSION_CREATION; got {result.session_mode!r}"
    )


def test_run_no_vault_no_l1():
    """AT-11: run() without vault_text → l1_match is None."""
    result = run("hello", vault_text="")
    assert result.l1_match is None, (
        f"AT-11: no vault → l1_match must be None; got {result.l1_match!r}"
    )


def test_run_vault_with_memory_query_produces_l3():
    """AT-12: vault + memory query → l3_byte is populated."""
    result = run(
        "do you remember what we built last time?",
        vault_text="We built the WKG system for eLo. It resolves world knowledge claims.",
    )
    assert result.l3_byte is not None, (
        "AT-12: vault + memory query must produce l3_byte"
    )
    assert "CP-" in result.l3_byte, (
        f"AT-12: l3_byte must contain 'CP-' id prefix; got {result.l3_byte!r}"
    )


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_session_mode_creation_detected),
        ("AT-2", test_session_mode_research_detected),
        ("AT-3", test_session_mode_flow_detected),
        ("AT-4", test_session_mode_standard_default),
        ("AT-5", test_memory_query_detection),
        ("AT-6", test_l2_compress_strips_blank_and_dividers),
        ("AT-7", test_speak_mode_flow_is_silent),
        ("AT-8", test_speak_mode_creation_no_memory_is_step_back),
        ("AT-9", test_speak_mode_creation_with_memory_is_speak),
        ("AT-10", test_run_returns_controlplane_result),
        ("AT-11", test_run_no_vault_no_l1),
        ("AT-12", test_run_vault_with_memory_query_produces_l3),
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
    print(f"control_plane   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
