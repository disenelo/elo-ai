"""
core/backend_manager.py — eLo AI backend switching system.

Single call:
    switch_backend("offline" | "claude" | "local_llm")

Effect:
    1. Updates core/api_layer.py  — governs direct generate_response() calls
    2. Registers handler in core/kernel.py's _BACKEND_REGISTRY
       so kernel.generate_response() (the public function) also routes correctly

Kernel source is NOT modified.
Routing logic is NOT modified.
Only the generation step is swapped.

Usage:
    from core.backend_manager import switch_backend, active_backend, status

    # at startup — one call switches everything
    switch_backend("offline")      # default, always works
    switch_backend("claude")       # set ANTHROPIC_API_KEY first
    switch_backend("local_llm")    # start Ollama first

    # check what's active
    print(active_backend())        # "claude"
    print(status())                # full status dict
"""

import os
import logging

logger = logging.getLogger(__name__)

_VALID_BACKENDS = ("offline", "claude", "local_llm")


# ── adapter factory ────────────────────────────────────────────────────────────

def _make_handler(name: str):
    """
    Return a callable(mode, user_input, context) → str for the named backend.
    Used to register handlers in kernel._BACKEND_REGISTRY.
    """
    if name == "claude":
        from core.api_layer import ClaudeAPIAdapter
        adapter = ClaudeAPIAdapter()
        return lambda mode, text, ctx: adapter.generate(text, mode, ctx)

    if name == "local_llm":
        from core.api_layer import LocalLLMAdapter
        adapter = LocalLLMAdapter()
        return lambda mode, text, ctx: adapter.generate(text, mode, ctx)

    # offline: let kernel._generate_placeholder handle it
    return None


# ── availability checks ────────────────────────────────────────────────────────

def _check_available(name: str) -> tuple:
    """
    Return (available: bool, reason: str) for the named backend.
    Does not attempt any connection — only checks environment variables.
    """
    if name == "offline":
        return True, "always available"

    if name == "claude":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            return True, f"ANTHROPIC_API_KEY set (model: {os.environ.get('ELO_MODEL','claude-sonnet-4-6')})"
        return False, "ANTHROPIC_API_KEY not set"

    if name == "local_llm":
        url = os.environ.get("ELO_LOCAL_MODEL_URL", "http://localhost:11434/v1/chat/completions")
        model = os.environ.get("ELO_LOCAL_MODEL_NAME", "llama3")
        return True, f"will attempt {url} with model={model} (not verified until first call)"

    return False, f"unknown backend: {name!r}"


# ── main switch ────────────────────────────────────────────────────────────────

def switch_backend(name: str) -> dict:
    """
    Switch the active generation backend.

    Updates both:
        core/api_layer.py  — direct generate_response() calls
        core/kernel.py     — kernel.generate_response() public function

    Does NOT modify any kernel source file.
    Does NOT change routing, mode selection, or cognitive behaviour.

    Args:
        name: "offline" | "claude" | "local_llm"

    Returns:
        Status dict with keys: backend, available, reason, action
    """
    name = name.lower()
    if name not in _VALID_BACKENDS:
        raise ValueError(f"Unknown backend {name!r}. Valid: {_VALID_BACKENDS}")

    available, reason = _check_available(name)

    # 1 — update api_layer (governs direct calls)
    from core.api_layer import set_active_backend as _api_set
    _api_set(name)

    # 2 — register handler in kernel (governs kernel.generate_response() public fn)
    #     kernel source is NOT modified — uses existing set_backend() API
    import core.kernel as _kernel
    handler = _make_handler(name)
    if handler is not None:
        _kernel.set_backend(name, handler=handler)
    else:
        _kernel.set_backend("offline")   # use kernel's built-in offline

    action = f"backend set to {name!r}"
    if not available:
        action += " — will fall back to offline until dependency is resolved"

    logger.info("Backend switched: %s (%s)", name, reason)

    return {
        "backend":   name,
        "available": available,
        "reason":    reason,
        "action":    action,
    }


# ── status ────────────────────────────────────────────────────────────────────

def active_backend() -> str:
    """Return the name of the currently active backend."""
    from core.api_layer import active_backend as _ab
    return _ab()


def status() -> dict:
    """
    Return availability status for all backends.
    Does not make any network calls.
    """
    current = active_backend()
    backends = {}
    for name in _VALID_BACKENDS:
        avail, reason = _check_available(name)
        backends[name] = {
            "available": avail,
            "reason":    reason,
            "active":    name == current,
        }
    return {
        "active":   current,
        "backends": backends,
    }
