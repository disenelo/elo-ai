"""
llm_client.py — eLo AI LLM interface.

Wraps the Anthropic Claude API.
Injects system prompt + memory context on every call.
Swap the model via ELO_MODEL env var.
Runs in placeholder mode if ANTHROPIC_API_KEY is not set.
"""

import os
import logging

logger = logging.getLogger(__name__)

_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
_MODEL   = os.environ.get("ELO_MODEL", "claude-sonnet-4-6")


def call_llm(
    prompt: str,
    system_prompt: str = "",
    memory: str = "",
    max_tokens: int = 1024,
) -> str:
    """
    Send a user prompt to the LLM and return the response.

    Args:
        prompt:        The current user input.
        system_prompt: eLo identity + mode overlay (from core_engine).
        memory:        Pre-formatted memory context string (from memory_engine).
        max_tokens:    Response length cap.

    Returns:
        LLM response as a plain string.

    Runtime injection order inside the API call:
        system_prompt
            → [LONG-TERM MEMORY] block  (export_memory.md)
            → [SESSION MEMORY] block    (retrieved interactions)
        user message: prompt
    """
    full_system = _build_system(system_prompt, memory)

    if not _API_KEY:
        from offline_engine import generate_offline_response
        return generate_offline_response(prompt, {}, "companion")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=_API_KEY)
        message = client.messages.create(
            model=_MODEL,
            max_tokens=max_tokens,
            system=full_system,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except ImportError:
        logger.error("Run: pip install anthropic")
        from offline_engine import generate_offline_response
        return generate_offline_response(prompt, {}, "companion")

    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return f"[eLo encountered an error: {exc}]"


def _build_system(system_prompt: str, memory: str) -> str:
    parts = [system_prompt.strip()]
    if memory.strip():
        parts.append(f"[MEMORY CONTEXT]\n{memory.strip()}\n[/MEMORY CONTEXT]")
    return "\n\n".join(filter(None, parts))


def _placeholder(prompt: str) -> str:
    return (
        f"[eLo AI — placeholder mode]\n"
        f"Received: {prompt!r}\n"
        f"Set ANTHROPIC_API_KEY to connect the live model."
    )
