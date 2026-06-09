"""
backends/offline_backend.py — eLo AI OS offline backend.

Step 42 — OfflineBackend

Deterministic offline simulation.
No API calls. No networking. No randomness.
Identical input always produces identical output.

Uses the existing 5-phase response generation in core/behavior_engine.py.
Does not modify routing, memory, state, emotion, or identity logic.
"""

from __future__ import annotations

from backends.base_backend import BaseBackend, BackendResponse, MemoryContext, StateContext, IdentityContext


class OfflineBackend(BaseBackend):
    """
    Deterministic offline response backend.

    Uses the kernel's existing offline generation layer (behavior_engine).
    No model. No API. No network. Always available.

    Guarantees:
        - Identical input + mode + context → identical response_text
        - No external calls
        - No shared mutable state written
        - Falls back to a safe minimal response if generation fails
    """

    NAME         = "offline"
    VERSION      = "1.0.0"
    DESCRIPTION  = "Deterministic offline simulation — 5-phase reasoning engine"
    REQUIRES_KEY = False

    def is_available(self) -> bool:
        """Always True — no dependencies."""
        return True

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
        Generate a deterministic response using the offline reasoning engine.

        Delegates to core/kernel._generate() via core/behavior_engine.
        The caller (kernel or BackendRegistry) provides all context —
        this method only performs generation, not routing.

        Args:
            user_input: Raw user text.
            mode:       Routing mode from the kernel.
            context:    Full assembled context dict.
            memory:     Memory influence signals.
            state:      Conversational state snapshot.
            identity:   Identity engine snapshot.

        Returns:
            BackendResponse with response_text from offline engine.
        """
        try:
            response_text = self._generate(user_input, mode, context)
        except Exception:
            # safe fallback — never raise from offline backend
            response_text = self._fallback(mode)

        return {"response_text": response_text}

    def _generate(self, user_input: str, mode: str, context: dict) -> str:
        """
        Delegate to the kernel's offline generation layer.

        Imports are local to prevent circular dependencies at module load time.
        core/kernel is never imported at class level.
        """
        from core.kernel import _generate, _classify, _assemble

        classification          = _classify(user_input)
        classification["_text"] = user_input.lower()
        assembled               = _assemble(context)
        return _generate(user_input, mode, classification, assembled)

    def _fallback(self, mode: str) -> str:
        """
        Minimal safe response when the offline engine raises unexpectedly.
        Deterministic — same mode always produces same fallback.
        """
        _FALLBACKS = {
            "DIRECT":          "That's a real question. Let me think about it.",
            "GENTLE_GROUNDED": "That makes sense. Nothing needs to happen right now.",
            "CREATIVE":        "Follow that.",
            "STRUCTURED":      "Let's take this step by step.",
            "SIMPLIFY":        "Okay.",
            "CONVERSATIONAL":  "What's the thing underneath that?",
        }
        return _FALLBACKS.get(mode, "I'm here.")
