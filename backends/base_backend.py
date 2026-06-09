"""
backends/base_backend.py — eLo AI OS backend interface contract.

Step 41 — Backend Interface Contract

Design principle: dependency inversion.

The kernel depends on an abstraction (BaseBackend), not on any concrete model.
Backends depend on the abstraction, not on kernel internals.
Neither side knows the other's implementation.

                  ┌────────────────────────────────┐
                  │  kernel / core_engine            │
                  │  calls BaseBackend.generate()   │
                  └──────────────┬─────────────────┘
                                 │  depends on
                                 ▼
                  ┌────────────────────────────────┐
                  │  BaseBackend  (this file)       │
                  │  abstract interface             │
                  └──────────────┬─────────────────┘
                                 │  implemented by
                     ┌───────────┼───────────┐
                     ▼           ▼           ▼
               Offline      Claude      LocalLLM
               Backend      Backend     Backend
               (no model)  (API)       (Ollama)

No concrete backend may import from core/kernel.py.
No kernel code may import from any specific backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict, Optional


# ── typed parameter schemas ────────────────────────────────────────────────────

class MemoryContext(TypedDict, total=False):
    """
    Memory influence signals passed to the backend.
    Derived from memory_engine.build_memory_influence().
    All fields are optional — backends use what they need.
    """
    tone_signal:        str    # dominant tone from recent history
    returning_theme:    str    # recurring concept phrase (empty if none)
    symbolic_echo:      str    # entity pattern phrase (empty if none)
    project:            str    # active project namespace
    response_style:     str    # style hint from 5-category synthesis
    key_association:    str    # cross-concept association
    future_idea:        str    # direction the work is pointing


class StateContext(TypedDict, total=False):
    """
    Conversational state snapshot passed to the backend.
    Derived from state_engine.get_style_influence().
    """
    name:        str    # exploring / building / focused / reflecting / playful / resting
    tone_bias:   str    # precise / open / grounded / soft / light / minimal
    weight:      float  # 0.0 (tight) to 1.0 (expressive)
    pacing_bias: str    # measured / unhurried / slow / quick


class IdentityContext(TypedDict, total=False):
    """
    Identity engine snapshot passed to the backend.
    Derived from identity_engine.decide().
    """
    values:        list   # 3 most active core values this turn
    perspective:   str    # how eLo frames the input (expansion / symbolic / practical / ...)
    intent:        str    # what eLo intends this turn (expand_idea / hold_space / ...)
    response_bias: str    # lean_imaginative / stay_grounded / slow_down / ...
    entities:      list   # eLo universe entities mentioned in input


class BackendResponse(TypedDict):
    """
    The only thing a backend may return.
    Strictly a response_text string — no metadata, no routing hints.
    """
    response_text: str


# ── abstract base class ────────────────────────────────────────────────────────

class BaseBackend(ABC):
    """
    Abstract base class for all eLo AI OS response backends.

    Contract:
        - Backends receive structured input from the kernel.
        - Backends return exactly one string: the response text.
        - Backends do not know which mode was selected or why.
        - Backends do not call kernel internals.
        - Backends do not modify any shared state.

    Required class attributes:
        NAME         (str)   — unique identifier, lowercase_underscore
        VERSION      (str)   — semver string
        DESCRIPTION  (str)   — one-line human-readable description
        REQUIRES_KEY (bool)  — True if an API key or server is required

    Required method:
        generate_response(...) → BackendResponse
    """

    NAME:         str  = "base"
    VERSION:      str  = "0.1.0"
    DESCRIPTION:  str  = "Abstract base — not for direct use"
    REQUIRES_KEY: bool = False

    @abstractmethod
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
        Generate a response for the given input and context.

        This is the single point of contact between the kernel and any backend.
        The kernel calls this method — it knows nothing else about the backend.

        Args:
            user_input:
                The raw text from the user. Identical to what the kernel
                used for classification and routing. Must not be modified.

            mode:
                The routing mode selected by the kernel.
                One of: DIRECT | GENTLE_GROUNDED | CREATIVE |
                        STRUCTURED | SIMPLIFY | CONVERSATIONAL
                The backend may use this to adjust system prompt injection,
                instruction framing, or generation parameters.
                The backend must NOT re-route or override this value.

            context:
                The full assembled context dict from StateBus.to_context().
                Contains all engine snapshot data flattened into a single
                dict. Backends may read any key they need.
                Must not be modified.

            memory:
                Memory influence signals (MemoryContext).
                Subset of context provided separately for backends
                that build system prompts from memory signals.
                All fields are optional — use .get(key, default) safely.

            state:
                Conversational state snapshot (StateContext).
                Indicates the style and pacing context of the conversation.
                Backends may use this to adjust tone/energy of response.

            identity:
                Identity engine snapshot (IdentityContext).
                Indicates eLo's current values, perspective, intent, and bias.
                Backends may inject this into system prompts.

        Returns:
            BackendResponse — a dict with exactly one key:
                {"response_text": str}

            response_text must be:
                - A non-empty string
                - Free of debug metadata
                - The final response exactly as it should be shown to the user
                - Deterministic given the same inputs (for offline backends)

        Raises:
            NotImplementedError:   If not overridden.
            BackendUnavailableError: If the backend cannot serve this request.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.generate_response() is not implemented."
        )

    def is_available(self) -> bool:
        """
        Return True if this backend can currently serve requests.

        Called by the registry before delegating generate_response().
        If False, the registry falls back to OfflineBackend.

        Default: True.
        Override for backends that require API keys or local servers.
        """
        return True

    def on_load(self):
        """
        Called once when this backend is activated.
        Safe to open connections, warm up models, validate keys.
        Default: no-op.
        """

    def on_unload(self):
        """
        Called once when this backend is deactivated.
        Safe to close connections, release resources.
        Default: no-op.
        """

    def describe(self) -> dict:
        """Return a status dict for logging and observability endpoints."""
        return {
            "name":         self.NAME,
            "version":      self.VERSION,
            "description":  self.DESCRIPTION,
            "requires_key": self.REQUIRES_KEY,
            "available":    self.is_available(),
        }

    def __repr__(self) -> str:
        avail = "✓" if self.is_available() else "✗"
        return f"<Backend {self.NAME} v{self.VERSION} [{avail}]>"


# ── error types ────────────────────────────────────────────────────────────────

class BackendUnavailableError(RuntimeError):
    """Raised when a backend cannot serve a request (key missing, server down, etc.)."""


class BackendResponseError(RuntimeError):
    """Raised when a backend returns an invalid or empty response."""
