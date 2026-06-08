"""
LLM_INTERFACE.py — eLo AI model interface.

Single entry point for all response generation.
Backend is swapped via ELO_BACKEND env var — the behaviour layer never changes.

Usage:
    from LLM_INTERFACE import generate_response

    response = generate_response(
        user_input="what does Chunk mean",
        context={
            "mode":       "companion",
            "memory":     {},          # from build_memory_influence()
            "system_prompt": "...",    # from personality.build_system_prompt()
        }
    )

Backends:
    offline  — deterministic rules engine (default, no API key needed)
    claude   — Anthropic Claude API (set ANTHROPIC_API_KEY)
    local    — local open-source model (set ELO_LOCAL_MODEL_URL)

Switch backend:
    export ELO_BACKEND=offline   # default
    export ELO_BACKEND=claude
    export ELO_BACKEND=local
"""

import os
import logging

logger = logging.getLogger(__name__)

# ── backend constants ──────────────────────────────────────────────────────────

BACKEND_OFFLINE = "offline"
BACKEND_CLAUDE  = "claude"
BACKEND_LOCAL   = "local"

_ACTIVE_BACKEND = os.environ.get("ELO_BACKEND", BACKEND_OFFLINE).lower()


# ── context helpers ────────────────────────────────────────────────────────────

def _extract(context: dict, key: str, default=None):
    return context.get(key, default) if isinstance(context, dict) else default


# ── adapters ───────────────────────────────────────────────────────────────────

class OfflineAdapter:
    """
    Deterministic rules-based response engine.
    No API calls. No external dependencies.
    Implements ELO_BEHAVIOUR_SPEC.md fully.
    """

    def generate(self, user_input: str, context: dict) -> str:
        from offline_engine import generate_offline_response
        mode   = _extract(context, "mode",   "companion")
        memory = _extract(context, "memory", {})
        return generate_offline_response(user_input, memory, mode)


class ClaudeAdapter:
    """
    Anthropic Claude API backend.
    Requires ANTHROPIC_API_KEY environment variable.
    Falls back to OfflineAdapter if key is missing or call fails.
    """

    _MODEL   = os.environ.get("ELO_MODEL", "claude-sonnet-4-6")
    _API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, user_input: str, context: dict) -> str:
        if not self._API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set — falling back to offline.")
            return OfflineAdapter().generate(user_input, context)

        system_prompt = _extract(context, "system_prompt", "")
        memory_str    = _extract(context, "memory_string", "")

        full_system = system_prompt
        if memory_str:
            full_system += f"\n\n[MEMORY CONTEXT]\n{memory_str}\n[/MEMORY CONTEXT]"

        try:
            import anthropic
            client  = anthropic.Anthropic(api_key=self._API_KEY)
            message = client.messages.create(
                model=self._MODEL,
                max_tokens=1024,
                system=full_system,
                messages=[{"role": "user", "content": user_input}],
            )
            return message.content[0].text

        except ImportError:
            logger.error("pip install anthropic — falling back to offline.")
            return OfflineAdapter().generate(user_input, context)

        except Exception as exc:
            logger.error("Claude API error: %s — falling back to offline.", exc)
            return OfflineAdapter().generate(user_input, context)


class LocalModelAdapter:
    """
    Local open-source LLM backend (Ollama, LM Studio, llama.cpp server, etc.)
    Requires ELO_LOCAL_MODEL_URL (default: http://localhost:11434/api/generate)
    Falls back to OfflineAdapter if unreachable.

    Expected API: OpenAI-compatible chat completions endpoint.
    """

    _URL   = os.environ.get("ELO_LOCAL_MODEL_URL", "http://localhost:11434/v1/chat/completions")
    _MODEL = os.environ.get("ELO_LOCAL_MODEL_NAME", "llama3")

    def generate(self, user_input: str, context: dict) -> str:
        system_prompt = _extract(context, "system_prompt", "")
        memory_str    = _extract(context, "memory_string", "")

        full_system = system_prompt
        if memory_str:
            full_system += f"\n\n[MEMORY CONTEXT]\n{memory_str}\n[/MEMORY CONTEXT]"

        payload = {
            "model": self._MODEL,
            "messages": [
                {"role": "system",    "content": full_system},
                {"role": "user",      "content": user_input},
            ],
            "stream": False,
        }

        try:
            import urllib.request, json as _json
            data = _json.dumps(payload).encode()
            req  = urllib.request.Request(
                self._URL,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = _json.loads(resp.read())
            return result["choices"][0]["message"]["content"]

        except Exception as exc:
            logger.error("Local model error: %s — falling back to offline.", exc)
            return OfflineAdapter().generate(user_input, context)


# ── backend registry ───────────────────────────────────────────────────────────

_ADAPTERS = {
    BACKEND_OFFLINE: OfflineAdapter,
    BACKEND_CLAUDE:  ClaudeAdapter,
    BACKEND_LOCAL:   LocalModelAdapter,
}


def _get_adapter(backend: str = None):
    key = (backend or _ACTIVE_BACKEND).lower()
    cls = _ADAPTERS.get(key)
    if cls is None:
        logger.warning("Unknown backend %r — using offline.", key)
        cls = OfflineAdapter
    return cls()


# ── public API ─────────────────────────────────────────────────────────────────

def generate_response(
    user_input: str,
    context: dict = None,
    backend: str = None,
) -> str:
    """
    Generate an eLo response using the active backend.

    Args:
        user_input: Raw text from the user.
        context:    Dict with any of:
                        mode          (str)   — "studio" | "companion" | "adventure"
                        memory        (dict)  — from build_memory_influence()
                        system_prompt (str)   — full prompt from personality.build_system_prompt()
                        memory_string (str)   — formatted memory for API injection
        backend:    Override the active backend for this call only.
                    "offline" | "claude" | "local"

    Returns:
        Response string.
    """
    adapter = _get_adapter(backend)
    return adapter.generate(user_input, context or {})


def active_backend() -> str:
    """Return the name of the currently active backend."""
    return _ACTIVE_BACKEND


def list_backends() -> list:
    """Return all registered backend names."""
    return list(_ADAPTERS.keys())
