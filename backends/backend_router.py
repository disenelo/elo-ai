"""
backends/backend_router.py — eLo AI OS backend resilience layer.

Unified interface with automatic failover and feel-testing support.

Modes:
    auto   — try Claude, fall back to mock on any failure (default)
    claude — force Claude API (errors still caught gracefully)
    mock   — force mock backend (offline feel-testing)

Entry point:
    get_response(user_input, mode, context, ...) → str

Rules:
    - NEVER expose raw API errors to the user
    - NEVER break the response chain
    - ALWAYS return a string

Kernel is not touched. Routing is not touched.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

# Suppress backend error logs from reaching the terminal.
# All failures are caught silently — the user never sees API errors.
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False   # never reaches root logger / terminal

# Separate debug logger for feel-test mode (only active when explicitly enabled)
_feel_logger = logging.getLogger("elo.feel_test")

# ── backend mode ───────────────────────────────────────────────────────────────

BACKEND_AUTO   = "auto"
BACKEND_CLAUDE = "claude"
BACKEND_MOCK   = "mock"
BACKEND_LOCAL  = "local"   # placeholder for future local LLM

_active_mode: str = BACKEND_AUTO
_feel_test_mode: bool = False

_SAFE_FALLBACK = "I'm having a moment of connection issues — say that again?"


def set_backend_mode(mode: str):
    """
    Set the active backend mode.
    Valid: "auto" | "claude" | "mock" | "local"
    """
    global _active_mode
    mode = mode.lower().strip()
    if mode in (BACKEND_AUTO, BACKEND_CLAUDE, BACKEND_MOCK, BACKEND_LOCAL):
        _active_mode = mode


def get_backend_mode() -> str:
    return _active_mode


def set_feel_test_mode(enabled: bool):
    """Enable feel-test logging: mode, backend, latency, response length."""
    global _feel_test_mode
    _feel_test_mode = enabled


# ── lazy backend instances ─────────────────────────────────────────────────────

_claude_backend  = None
_mock_backend    = None


def _get_claude():
    global _claude_backend
    if _claude_backend is None:
        from backends.claude_backend import ClaudeBackend
        _claude_backend = ClaudeBackend()
    return _claude_backend


def _get_mock():
    global _mock_backend
    if _mock_backend is None:
        from backends.mock_backend import MockBackend
        _mock_backend = MockBackend()
    return _mock_backend


# ── unified get_response ───────────────────────────────────────────────────────

def get_response(
    user_input: str,
    mode:       str  = "CONVERSATIONAL",
    context:    dict = None,
    memory:     dict = None,
    state:      dict = None,
    identity:   dict = None,
) -> str:
    """
    Get a response using the active backend with automatic failover.

    Flow:
        auto:   try Claude → on failure → mock → on failure → safe string
        claude: try Claude → on failure → safe string (no mock)
        mock:   use mock directly → on failure → safe string
        local:  stub → mock fallback

    Args:
        user_input: Raw user text.
        mode:       Kernel routing mode (DIRECT, CONVERSATIONAL, etc.)
        context:    Full context dict.
        memory:     Memory signals.
        state:      State snapshot.
        identity:   Identity snapshot.

    Returns:
        Response string — guaranteed, never raises.
    """
    ctx = context  or {}
    mem = memory   or {}
    st  = state    or {}
    id_ = identity or {}

    t_start = time.perf_counter()
    response, backend_used = _dispatch(user_input, mode, ctx, mem, st, id_)
    elapsed_ms = int((time.perf_counter() - t_start) * 1000)

    if _feel_test_mode:
        _log_feel(mode, backend_used, elapsed_ms, response)

    return response


def _dispatch(
    user_input: str, mode: str,
    ctx: dict, mem: dict, st: dict, id_: dict,
) -> tuple:
    """
    Dispatch to the correct backend. Returns (response_text, backend_name).
    Never raises.
    """
    if _active_mode == BACKEND_MOCK:
        return _try_mock(user_input, mode, ctx, mem, st, id_), "mock"

    if _active_mode == BACKEND_CLAUDE:
        result = _try_claude(user_input, mode, ctx, mem, st, id_)
        if result is not None:
            return result, "claude"
        return _SAFE_FALLBACK, "fallback"

    if _active_mode == BACKEND_LOCAL:
        return _try_mock(user_input, mode, ctx, mem, st, id_), "mock(local-stub)"

    # auto: Claude → mock → safe string
    claude_result = _try_claude(user_input, mode, ctx, mem, st, id_)
    if claude_result is not None:
        return claude_result, "claude"

    mock_result = _try_mock(user_input, mode, ctx, mem, st, id_)
    return mock_result, "mock(auto-fallback)"


def _try_claude(
    user_input: str, mode: str,
    ctx: dict, mem: dict, st: dict, id_: dict,
) -> Optional[str]:
    """
    Attempt a Claude API call.
    Returns response string on success, None on ANY failure.
    All errors are caught and suppressed — nothing reaches the terminal.
    Failure output boundary: returns None immediately, no downstream calls.
    """
    try:
        backend = _get_claude()
        if not backend.is_available():
            return None
        result = backend.generate_response(user_input, mode, ctx, mem, st, id_)
        text = result.get("response_text", "").strip()
        return text if text else None
    except Exception:
        # HARD FAILSAFE — catch everything, return None, execute nothing further
        return None


def _try_mock(
    user_input: str, mode: str,
    ctx: dict, mem: dict, st: dict, id_: dict,
) -> str:
    """
    Generate a mock response.
    Returns _SAFE_FALLBACK on any failure.
    Never raises. Never passes output back through cognitive layers.
    """
    try:
        backend = _get_mock()
        result  = backend.generate_response(user_input, mode, ctx, mem, st, id_)
        return result["response_text"]
    except Exception:
        return _SAFE_FALLBACK


# ── feel-test logging ──────────────────────────────────────────────────────────

def _log_feel(mode: str, backend: str, ms: int, response: str):
    """Minimal feel-test output — mode, backend, latency, length only."""
    print(f"  [feel]  mode={mode:<16} backend={backend:<20} {ms}ms  {len(response)}ch", flush=True)
