"""
backends/claude_backend.py — eLo AI OS Claude API backend.

Step 43 — ClaudeBackend

Calls the Anthropic Claude API to generate responses.
Reads API key from ANTHROPIC_API_KEY environment variable.
Falls back to OfflineBackend on failure.

Does not alter:
    routing, memory retrieval, state transitions,
    emotion mapping, identity decisions, loop detection.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

from backends.base_backend import (
    BaseBackend, BackendResponse,
    MemoryContext, StateContext, IdentityContext,
    BackendUnavailableError, BackendResponseError,
)

logger = logging.getLogger(__name__)

_DEFAULT_MODEL   = "claude-sonnet-4-6"
_DEFAULT_TIMEOUT = 30    # seconds
_MAX_TOKENS      = 1024
_RETRY_DELAY     = 1.0   # seconds between retry attempts


class ClaudeBackend(BaseBackend):
    """
    Anthropic Claude API backend.

    Receives context assembled by the kernel, builds a system prompt,
    calls the Claude API, and returns the response text.

    Failures:
        - Missing API key    → BackendUnavailableError
        - Timeout            → logs warning, retries once, then raises
        - API error          → logs error, retries once on transient, raises
        - Empty response     → BackendResponseError

    All failures are caught by BackendRegistry which falls back to OfflineBackend.
    """

    NAME         = "claude"
    VERSION      = "1.0.0"
    DESCRIPTION  = "Anthropic Claude API — set ANTHROPIC_API_KEY to activate"
    REQUIRES_KEY = True

    def __init__(self, model: str = None, timeout: int = None):
        """
        Args:
            model:   Claude model ID. Defaults to ELO_MODEL env var or claude-sonnet-4-6.
            timeout: Request timeout in seconds. Defaults to 30.
        """
        self._model   = model   or os.environ.get("ELO_MODEL", _DEFAULT_MODEL)
        self._timeout = timeout or _DEFAULT_TIMEOUT

    def is_available(self) -> bool:
        """Return True if ANTHROPIC_API_KEY is set."""
        return bool(os.environ.get("ANTHROPIC_API_KEY", ""))

    def on_load(self):
        """Verify the API key is present at activation time."""
        if not self.is_available():
            logger.warning("ClaudeBackend: ANTHROPIC_API_KEY not set.")

    def generate_response(
        self,
        user_input: str,
        mode:       str,
        context:    dict,
        memory:     MemoryContext,
        state:      StateContext,
        identity:   IdentityContext,
    ) -> BackendResponse:
        """
        Call the Claude API and return the response.

        Args:
            user_input: Raw user text.
            mode:       Routing mode from the kernel (used to build system prompt).
            context:    Full context dict — not modified.
            memory:     Memory signals — used to inject memory context.
            state:      State snapshot — used for pacing hint.
            identity:   Identity snapshot — used for system prompt framing.

        Returns:
            BackendResponse with response_text from Claude.

        Raises:
            BackendUnavailableError: If API key is missing.
            BackendResponseError:    If Claude returns an empty response.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise BackendUnavailableError(
                "ClaudeBackend: ANTHROPIC_API_KEY is not set."
            )

        system_prompt = self._build_system_prompt(mode, memory, state, identity)
        response_text = self._call_with_retry(api_key, system_prompt, user_input)

        if not response_text or not response_text.strip():
            raise BackendResponseError("ClaudeBackend: received empty response.")

        return {"response_text": response_text.strip()}

    # ── prompt builder ─────────────────────────────────────────────────────────

    def _build_system_prompt(
        self,
        mode:     str,
        memory:   MemoryContext,
        state:    StateContext,
        identity: IdentityContext,
    ) -> str:
        """
        Build the system prompt from mode + memory + state + identity.

        Reads config/system_prompt.txt for the base identity layer.
        Appends mode overlay, memory context, and state pacing hint.
        Does not call any kernel function — reads files only.
        """
        parts = []

        # base identity layer
        base = self._load_base_prompt()
        if base:
            parts.append(base)

        # mode overlay
        _MODE_OVERLAYS = {
            "DIRECT":          "[MODE: DIRECT] Answer the question directly and factually first.",
            "GENTLE_GROUNDED": "[MODE: GENTLE_GROUNDED] Acknowledge the emotional state before anything else. No abstraction.",
            "CREATIVE":        "[MODE: CREATIVE] Expand before naming. Follow the symbol. Let imagination lead.",
            "STRUCTURED":      "[MODE: STRUCTURED] Lead with the next concrete step. Stay inside the project context.",
            "SIMPLIFY":        "[MODE: SIMPLIFY] Respond simply. One sentence if possible.",
            "CONVERSATIONAL":  "[MODE: CONVERSATIONAL] Hold tension without resolving it. One question at most.",
        }
        if mode in _MODE_OVERLAYS:
            parts.append(_MODE_OVERLAYS[mode])

        # memory context
        memory_lines = []
        if memory.get("tone_signal") and memory["tone_signal"] != "neutral":
            memory_lines.append(f"Tone pattern: {memory['tone_signal']}")
        if memory.get("returning_theme"):
            memory_lines.append(f"Recurring: {memory['returning_theme']}")
        if memory.get("project") and memory.get("project") != "elo_core":
            memory_lines.append(f"Active project: {memory['project']}")
        if memory_lines:
            parts.append("[MEMORY]\n" + "\n".join(memory_lines))

        # identity intent
        intent = identity.get("intent", "")
        if intent:
            parts.append(f"[INTENT] {intent}")

        return "\n\n".join(p for p in parts if p)

    def _load_base_prompt(self) -> str:
        """Read config/system_prompt.txt — returns empty string if absent."""
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "system_prompt.txt"
        )
        if os.path.exists(path):
            with open(path) as f:
                return f.read().strip()
        return ""

    # ── API call with retry ────────────────────────────────────────────────────

    def _call_with_retry(
        self,
        api_key:       str,
        system_prompt: str,
        user_input:    str,
        attempts:      int = 2,
    ) -> str:
        """
        Call Claude API with one retry on transient failures.

        Args:
            api_key:       Anthropic API key.
            system_prompt: Full system prompt.
            user_input:    User message.
            attempts:      Max attempts (default 2 — one retry).

        Returns:
            Response text string.

        Raises:
            RuntimeError on exhausted retries.
        """
        last_exc: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                return self._call_api(api_key, system_prompt, user_input)
            except Exception as exc:
                last_exc = exc
                is_transient = self._is_transient(exc)

                if attempt < attempts and is_transient:
                    logger.warning(
                        "ClaudeBackend: transient error on attempt %d/%d — retrying. %s",
                        attempt, attempts, exc,
                    )
                    time.sleep(_RETRY_DELAY)
                else:
                    logger.error(
                        "ClaudeBackend: failed after %d attempt(s). %s",
                        attempt, exc,
                    )
                    raise

        raise RuntimeError(f"ClaudeBackend: exhausted {attempts} attempts. Last: {last_exc}")

    def _call_api(self, api_key: str, system_prompt: str, user_input: str) -> str:
        """
        Single Claude API call.

        Raises:
            ImportError if anthropic SDK is not installed.
            anthropic.APITimeoutError on timeout.
            anthropic.APIError on API failure.
        """
        import anthropic   # local import — not required at class level

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model      = self._model,
            max_tokens = _MAX_TOKENS,
            timeout    = self._timeout,
            system     = system_prompt,
            messages   = [{"role": "user", "content": user_input}],
        )
        return message.content[0].text

    @staticmethod
    def _is_transient(exc: Exception) -> bool:
        """Return True for errors that are worth retrying (rate limit, timeout, 5xx)."""
        name = type(exc).__name__.lower()
        return any(keyword in name for keyword in
                   ("timeout", "ratelimit", "serviceunavailable", "internalserver"))
