"""
core/base_backend.py — eLo AI OS backend interface.

The kernel never imports any specific backend.
It only knows about BaseBackend and calls generate_response().

Every backend receives exactly:
    mode        str   — routing mode (DIRECT, CREATIVE, etc.) from kernel
    context     dict  — assembled context from StateBus.to_context()
    memory      dict  — memory snapshot signals
    state       dict  — state snapshot (name, tone_bias, weight, pacing)
    user_input  str   — raw text from the user

Every backend returns exactly:
    response_text str — the response string, nothing else

The kernel is unaware of which model is running.
Model selection happens at the application layer via BackendRegistry.
"""

import os
import logging

logger = logging.getLogger(__name__)


# ── base contract ──────────────────────────────────────────────────────────────

class BaseBackend:
    """
    Abstract base class for all eLo AI OS response backends.

    Every concrete backend must implement generate_response().
    No other method is required — no routing, no cognitive logic,
    no kernel interaction.

    The kernel calls generate_response() and receives a string.
    It does not know or care which backend is running.

    Subclass contract:
        NAME:         str   — unique backend identifier
        DESCRIPTION:  str   — one-line description
        REQUIRES_KEY: bool  — True if an API key must be set

    Safety rule:
        Backends may not import from core/kernel.py.
        Backends may not call decide_response() or route().
        Backends may not modify kernel state.
    """

    NAME:         str  = "base"
    DESCRIPTION:  str  = "Abstract base backend — not for direct use"
    REQUIRES_KEY: bool = False

    def generate_response(
        self,
        mode:       str,
        context:    dict,
        memory:     dict,
        state:      dict,
        user_input: str,
    ) -> str:
        """
        Generate a response for the given input and context.

        Args:
            mode:       The routing mode selected by the kernel.
                        One of: DIRECT, GENTLE_GROUNDED, CREATIVE,
                                STRUCTURED, SIMPLIFY, CONVERSATIONAL.

            context:    Full context dict from StateBus.to_context().
                        Contains all engine snapshots (emotion, identity, etc.)
                        and memory signals.

            memory:     Memory snapshot signals specifically.
                        Subset of context — provided separately for
                        backends that use memory-only context injection.
                        Keys: tone_signal, returning_theme, project, etc.

            state:      State snapshot dict.
                        Keys: name, tone_bias, weight, pacing_bias.

            user_input: Raw text from the user. Same string the kernel
                        used for classification and routing.

        Returns:
            response_text: The response string.
                           Must be a non-empty string.
                           Must not contain debug metadata.
                           Must not modify any external state.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.generate_response() is not implemented. "
            f"Subclass BaseBackend and implement this method."
        )

    def is_available(self) -> bool:
        """
        Return True if this backend can currently serve requests.
        Checked before calling generate_response().
        Default: True (always available).
        Override for backends that require API keys or local servers.
        """
        return True

    def describe(self) -> dict:
        """Return a description dict for logging and status endpoints."""
        return {
            "name":         self.NAME,
            "description":  self.DESCRIPTION,
            "requires_key": self.REQUIRES_KEY,
            "available":    self.is_available(),
        }

    def __repr__(self) -> str:
        avail = "✓" if self.is_available() else "✗"
        return f"<Backend {self.NAME} [{avail}]>"


# ── offline stub ───────────────────────────────────────────────────────────────

class OfflineBackend(BaseBackend):
    """
    Offline simulation backend.
    Uses the existing 5-phase deterministic reasoning engine.
    No API key required. Always available.

    This is the default backend and the safety fallback.
    """

    NAME         = "offline"
    DESCRIPTION  = "Deterministic offline simulation — no model required"
    REQUIRES_KEY = False

    def generate_response(
        self,
        mode:       str,
        context:    dict,
        memory:     dict,
        state:      dict,
        user_input: str,
    ) -> str:
        from core.kernel import _generate, _classify, _assemble
        classification             = _classify(user_input)
        classification["_text"]    = user_input.lower()
        assembled                  = _assemble(context)
        return _generate(user_input, mode, classification, assembled)


# ── placeholder backends ───────────────────────────────────────────────────────

class ClaudeBackend(BaseBackend):
    """
    Anthropic Claude API backend.
    Not connected — implement generate_response() when ready.
    Requires: ANTHROPIC_API_KEY environment variable.
    """

    NAME         = "claude"
    DESCRIPTION  = "Anthropic Claude API — set ANTHROPIC_API_KEY to activate"
    REQUIRES_KEY = True

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY", ""))

    def generate_response(
        self,
        mode:       str,
        context:    dict,
        memory:     dict,
        state:      dict,
        user_input: str,
    ) -> str:
        """
        IMPLEMENTATION HOOK — connect Claude API here.

        Suggested implementation:
            import anthropic
            client = anthropic.Anthropic()
            system = _build_system_prompt(mode, memory)
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user_input}],
            )
            return msg.content[0].text
        """
        raise NotImplementedError("ClaudeBackend.generate_response() not yet connected.")


class LocalLLMBackend(BaseBackend):
    """
    Local open-source LLM backend (Ollama, LM Studio, llama.cpp).
    Not connected — implement generate_response() when ready.
    Requires: ELO_LOCAL_MODEL_URL (default: http://localhost:11434/...)
    """

    NAME         = "local_llm"
    DESCRIPTION  = "Local LLM via OpenAI-compatible endpoint"
    REQUIRES_KEY = False

    def is_available(self) -> bool:
        """Always True — availability verified only on first call."""
        return True

    def generate_response(
        self,
        mode:       str,
        context:    dict,
        memory:     dict,
        state:      dict,
        user_input: str,
    ) -> str:
        """
        IMPLEMENTATION HOOK — connect local model here.

        Suggested implementation:
            url   = os.environ.get("ELO_LOCAL_MODEL_URL", "http://localhost:11434/...")
            model = os.environ.get("ELO_LOCAL_MODEL_NAME", "llama3")
            payload = {"model": model, "messages": [{"role": "user", "content": user_input}]}
            resp  = requests.post(url, json=payload, timeout=30)
            return resp.json()["choices"][0]["message"]["content"]
        """
        raise NotImplementedError("LocalLLMBackend.generate_response() not yet connected.")


# ── backend registry ───────────────────────────────────────────────────────────

class BackendRegistry:
    """
    Registry of available backends.
    The kernel never touches this — it is called from core_engine or main.py.
    """

    def __init__(self):
        self._backends: dict = {}
        self._active:   str  = "offline"
        # register defaults
        self.register(OfflineBackend())
        self.register(ClaudeBackend())
        self.register(LocalLLMBackend())

    def register(self, backend: BaseBackend):
        self._backends[backend.NAME] = backend

    def activate(self, name: str) -> bool:
        """
        Set the active backend. Falls back to offline if unavailable.
        Returns True if the named backend was activated.
        """
        if name not in self._backends:
            logger.warning("Backend %r not registered. Using offline.", name)
            self._active = "offline"
            return False
        b = self._backends[name]
        if not b.is_available():
            logger.warning("Backend %r not available. Using offline.", name)
            self._active = "offline"
            return False
        self._active = name
        return True

    def generate_response(
        self,
        mode:       str,
        context:    dict,
        memory:     dict,
        state:      dict,
        user_input: str,
    ) -> str:
        """
        Delegate to the active backend. Falls back to offline on failure.
        """
        backend = self._backends.get(self._active, self._backends["offline"])
        try:
            return backend.generate_response(mode, context, memory, state, user_input)
        except NotImplementedError:
            logger.warning("Backend %r not implemented — falling back to offline.", self._active)
            return self._backends["offline"].generate_response(mode, context, memory, state, user_input)
        except Exception as exc:
            logger.error("Backend %r failed: %s — falling back to offline.", self._active, exc)
            return self._backends["offline"].generate_response(mode, context, memory, state, user_input)

    @property
    def active(self) -> str:
        return self._active

    def status(self) -> dict:
        return {
            "active":   self._active,
            "backends": {name: b.describe() for name, b in self._backends.items()},
        }


# module-level default registry
registry = BackendRegistry()
