"""
tests/test_backend_manager.py

WP_F gap: core/backend_manager.py — backend switching for eLo AI response generation.
Covers availability checks, invalid-name guard, switch contract, and status shape.
No network calls are made — _check_available is env-var only; switch_backend("offline")
routes through the kernel's built-in offline handler.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_backend_manager.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.backend_manager import (
    _VALID_BACKENDS,
    _check_available,
    switch_backend,
    active_backend,
    status,
)


def test_valid_backends_constant():
    """AT-1: _VALID_BACKENDS contains exactly the three canonical names."""
    for name in ("offline", "claude", "local_llm"):
        assert name in _VALID_BACKENDS, f"AT-1: '{name}' missing from _VALID_BACKENDS"
    assert len(_VALID_BACKENDS) == 3, f"AT-1: expected 3 backends; got {len(_VALID_BACKENDS)}"


def test_offline_always_available():
    """AT-2: _check_available('offline') returns (True, reason) unconditionally."""
    avail, reason = _check_available("offline")
    assert avail is True, f"AT-2: offline must always be available; got avail={avail}"
    assert isinstance(reason, str) and reason, f"AT-2: reason must be non-empty str"


def test_claude_unavailable_without_api_key():
    """AT-3: _check_available('claude') returns False when ANTHROPIC_API_KEY is unset."""
    old = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        avail, reason = _check_available("claude")
        assert avail is False, f"AT-3: claude must be unavailable without key; got {avail}"
        assert "ANTHROPIC_API_KEY" in reason, f"AT-3: reason must name the missing key; got {reason!r}"
    finally:
        if old is not None:
            os.environ["ANTHROPIC_API_KEY"] = old


def test_claude_available_with_api_key():
    """AT-4: _check_available('claude') returns True when ANTHROPIC_API_KEY is set."""
    os.environ["ANTHROPIC_API_KEY"] = "sk-test-dummy"
    try:
        avail, reason = _check_available("claude")
        assert avail is True, f"AT-4: claude must be available with key; got {avail}"
    finally:
        del os.environ["ANTHROPIC_API_KEY"]


def test_local_llm_available_without_connection():
    """AT-5: _check_available('local_llm') returns True — availability is not verified until first call."""
    avail, reason = _check_available("local_llm")
    assert avail is True, f"AT-5: local_llm must report available (not verified); got {avail}"
    assert isinstance(reason, str) and reason, f"AT-5: reason must be non-empty str"


def test_switch_backend_invalid_name_raises():
    """AT-6: switch_backend() with an unknown name raises ValueError."""
    raised = False
    try:
        switch_backend("not_a_backend")
    except ValueError:
        raised = True
    assert raised, "AT-6: unknown backend must raise ValueError"


def test_switch_backend_offline_returns_dict():
    """AT-7: switch_backend('offline') returns dict with expected keys."""
    result = switch_backend("offline")
    for key in ("backend", "available", "reason", "action"):
        assert key in result, f"AT-7: result must contain '{key}'; got {list(result)}"
    assert result["backend"] == "offline", f"AT-7: backend must be 'offline'; got {result['backend']}"
    assert result["available"] is True, f"AT-7: offline must always be available"


def test_active_backend_reflects_switch():
    """AT-8: active_backend() returns the backend most recently set by switch_backend()."""
    switch_backend("offline")
    assert active_backend() == "offline", f"AT-8: active_backend must be 'offline' after switch"


def test_status_shape():
    """AT-9: status() returns dict with 'active' and 'backends' covering all 3 backends."""
    result = status()
    assert "active" in result, f"AT-9: status must have 'active'; got {list(result)}"
    assert "backends" in result, f"AT-9: status must have 'backends'; got {list(result)}"
    backends = result["backends"]
    for name in ("offline", "claude", "local_llm"):
        assert name in backends, f"AT-9: backends must include '{name}'; got {list(backends)}"
        entry = backends[name]
        for key in ("available", "reason", "active"):
            assert key in entry, f"AT-9: backends['{name}'] missing '{key}'; got {list(entry)}"


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_valid_backends_constant),
        ("AT-2", test_offline_always_available),
        ("AT-3", test_claude_unavailable_without_api_key),
        ("AT-4", test_claude_available_with_api_key),
        ("AT-5", test_local_llm_available_without_connection),
        ("AT-6", test_switch_backend_invalid_name_raises),
        ("AT-7", test_switch_backend_offline_returns_dict),
        ("AT-8", test_active_backend_reflects_switch),
        ("AT-9", test_status_shape),
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
    print(f"backend_manager   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
