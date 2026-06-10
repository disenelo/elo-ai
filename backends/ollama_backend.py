"""
backends/ollama_backend.py — Ollama local LLM backend for eLo OS.

Connects to a locally running Ollama instance at http://localhost:11434.
Uses the /api/chat endpoint so system prompts are supported natively.

Setup:
    1. curl -fsSL https://ollama.com/install.sh | sh
    2. ollama pull mistral          (recommended — best instruction following)
       ollama pull llama3.1         (larger, slower)
       ollama pull qwen2.5          (good multilingual)
    3. Ollama starts automatically — no further setup needed.

Environment variables (optional overrides):
    ELO_OLLAMA_MODEL  — model name (default: mistral)
    ELO_OLLAMA_HOST   — base URL   (default: http://localhost:11434)
"""

from __future__ import annotations
import json
import os
import logging

from backends.base_backend import (
    BaseBackend, BackendResponse,
    MemoryContext, StateContext, IdentityContext,
    BackendUnavailableError, BackendResponseError,
)

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

_DEFAULT_MODEL = "mistral"
_DEFAULT_HOST  = "http://localhost:11434"


class OllamaBackend(BaseBackend):
    """
    Local Ollama LLM backend.

    No API key required. Requires Ollama running on localhost.
    Falls back gracefully if Ollama is not available.
    """

    NAME         = "ollama"
    VERSION      = "1.0.0"
    DESCRIPTION  = "Local Ollama backend — no API key, no internet required"
    REQUIRES_KEY = False

    def __init__(self):
        self._host  = os.environ.get("ELO_OLLAMA_HOST",  _DEFAULT_HOST).rstrip("/")
        self._model = os.environ.get("ELO_OLLAMA_MODEL", _DEFAULT_MODEL)

    def is_available(self) -> bool:
        """Return True if Ollama is running and reachable."""
        try:
            import requests
            r = requests.get(f"{self._host}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def generate_response(
        self,
        user_input: str,
        mode:       str,
        context:    dict,
        memory:     MemoryContext,
        state:      StateContext,
        identity:   IdentityContext,
    ) -> BackendResponse:
        if not self.is_available():
            raise BackendUnavailableError("Ollama is not running on localhost:11434")

        system_prompt = self._build_system_prompt()
        response_text = self._call(system_prompt, user_input)

        if not response_text or not response_text.strip():
            raise BackendResponseError("Ollama returned an empty response.")

        return {"response_text": response_text.strip()}

    def _build_system_prompt(self) -> str:
        """Load the Living Presence spec as the system prompt."""
        try:
            spec_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "prompts", "living_presence_spec.txt"
            )
            with open(spec_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "You are eLo — a stable, grounded conversational presence. Be concise and human."

    def _call(self, system_prompt: str, user_input: str) -> str:
        """POST to Ollama /api/chat and return the assistant message."""
        import requests

        payload = {
            "model":    self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "stream":  False,
            "options": {
                "temperature": 0.7,
                "num_predict": 256,
            },
        }

        try:
            r = requests.post(
                f"{self._host}/api/chat",
                json=payload,
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "").strip()
        except Exception as exc:
            _logger.error("OllamaBackend: call failed — %s", exc)
            raise
