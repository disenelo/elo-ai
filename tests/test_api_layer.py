"""
tests/test_api_layer.py

WP_F gap: core/api_layer.py — eLo AI response generation API abstraction layer.
Covers offline stub, backend registry, system prompt assembly, and memory block
construction. LocalLLMAdapter.is_available() is excluded — it makes a live network
call (2s timeout) that is not appropriate for a CI-level AT.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_api_layer.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.api_layer import (
    OfflineStub,
    ClaudeAPIAdapter,
    set_active_backend,
    active_backend,
    list_backends,
    generate_response,
)


def test_offline_stub_always_available():
    """AT-1: OfflineStub.is_available() is always True — no external deps."""
    stub = OfflineStub()
    assert stub.is_available() is True, "AT-1: OfflineStub must always be available"


def test_offline_stub_generate_returns_string():
    """AT-2: OfflineStub.generate() returns a non-empty string for any input."""
    stub = OfflineStub()
    result = stub.generate("hello", "companion", {})
    assert isinstance(result, str), f"AT-2: generate must return str; got {type(result)}"
    assert result, "AT-2: generate must return non-empty string"


def test_claude_adapter_unavailable_without_key():
    """AT-3: ClaudeAPIAdapter.is_available() returns False when ANTHROPIC_API_KEY is unset."""
    old = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        adapter = ClaudeAPIAdapter()
        assert adapter.is_available() is False, (
            "AT-3: ClaudeAPIAdapter must be unavailable without ANTHROPIC_API_KEY"
        )
    finally:
        if old is not None:
            os.environ["ANTHROPIC_API_KEY"] = old


def test_claude_adapter_available_with_key():
    """AT-4: ClaudeAPIAdapter.is_available() returns True when ANTHROPIC_API_KEY is set."""
    os.environ["ANTHROPIC_API_KEY"] = "sk-test-dummy"
    try:
        adapter = ClaudeAPIAdapter()
        assert adapter.is_available() is True, (
            "AT-4: ClaudeAPIAdapter must report available when ANTHROPIC_API_KEY is set"
        )
    finally:
        del os.environ["ANTHROPIC_API_KEY"]


def test_build_system_prompt_contains_mode_overlay():
    """AT-5: _build_system_prompt() injects the correct [MODE:] overlay for each mode."""
    adapter = ClaudeAPIAdapter()
    ctx = {"system_prompt": "You are eLo."}
    for mode, keyword in [
        ("studio",    "STUDIO"),
        ("companion", "COMPANION"),
        ("adventure", "ADVENTURE"),
    ]:
        sp = adapter._build_system_prompt(ctx, mode)
        assert keyword in sp, f"AT-5: mode={mode!r} must inject [{keyword}] into system prompt"


def test_build_system_prompt_uses_base_prompt():
    """AT-6: _build_system_prompt() includes context['system_prompt'] as the base."""
    adapter = ClaudeAPIAdapter()
    ctx = {"system_prompt": "UNIQUE_BASE_PROMPT_X7Z"}
    sp = adapter._build_system_prompt(ctx, "companion")
    assert "UNIQUE_BASE_PROMPT_X7Z" in sp, (
        f"AT-6: system_prompt from context must appear in built prompt; got {sp[:200]}"
    )


def test_memory_block_non_neutral_tone():
    """AT-7: _memory_block() includes [MEMORY] block when tone_signal is non-neutral."""
    adapter = ClaudeAPIAdapter()
    block = adapter._memory_block({
        "tone_signal":     "warm",
        "returning_theme": "creativity",
        "project":         "elo_planet",
    })
    assert block.startswith("[MEMORY]"), f"AT-7: block must start with [MEMORY]; got {block!r}"
    assert "warm" in block, f"AT-7: tone signal must appear; got {block!r}"


def test_memory_block_neutral_tone_returns_empty():
    """AT-8: _memory_block() returns empty string when tone=neutral and no theme/project."""
    adapter = ClaudeAPIAdapter()
    block = adapter._memory_block({"tone_signal": "neutral", "project": "elo_core"})
    assert block == "", f"AT-8: neutral tone + default project must return empty block; got {block!r}"


def test_list_backends_returns_all_three():
    """AT-9: list_backends() returns exactly the three valid backend names."""
    backends = list_backends()
    for name in ("offline", "claude", "local_llm"):
        assert name in backends, f"AT-9: '{name}' must be in list_backends(); got {backends}"


def test_set_and_read_active_backend():
    """AT-10: set_active_backend() persists and active_backend() reads it back."""
    set_active_backend("offline")
    assert active_backend() == "offline", (
        f"AT-10: active_backend() must return 'offline' after setting; got {active_backend()!r}"
    )


def test_generate_response_offline_returns_string():
    """AT-11: generate_response() with offline backend returns a non-empty string."""
    set_active_backend("offline")
    result = generate_response("tell me something", "companion", {})
    assert isinstance(result, str), f"AT-11: generate_response must return str; got {type(result)}"
    assert result, "AT-11: generate_response must return non-empty string"


if __name__ == "__main__":
    _tests = [
        ("AT-1",  test_offline_stub_always_available),
        ("AT-2",  test_offline_stub_generate_returns_string),
        ("AT-3",  test_claude_adapter_unavailable_without_key),
        ("AT-4",  test_claude_adapter_available_with_key),
        ("AT-5",  test_build_system_prompt_contains_mode_overlay),
        ("AT-6",  test_build_system_prompt_uses_base_prompt),
        ("AT-7",  test_memory_block_non_neutral_tone),
        ("AT-8",  test_memory_block_neutral_tone_returns_empty),
        ("AT-9",  test_list_backends_returns_all_three),
        ("AT-10", test_set_and_read_active_backend),
        ("AT-11", test_generate_response_offline_returns_string),
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
    print(f"api_layer   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
