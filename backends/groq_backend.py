"""
backends/groq_backend.py — Groq cloud inference backend for eLo OS.

Fast cloud inference via the Groq SDK.

Setup:
    pip install groq
    export GROQ_API_KEY=gsk_...

Recommended models (set via ELO_GROQ_MODEL):
    llama-3.1-70b-versatile    — best instruction following (default)
    llama-3.1-8b-instant       — faster, lighter
    mixtral-8x7b-32768         — good context window
    gemma2-9b-it               — efficient instruction model
"""

from __future__ import annotations
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

_DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqBackend(BaseBackend):
    """
    Groq cloud inference backend using the groq SDK.
    Requires: pip install groq  +  GROQ_API_KEY env var.
    """

    NAME         = "groq"
    VERSION      = "1.0.0"
    DESCRIPTION  = "Groq cloud inference — set GROQ_API_KEY to activate"
    REQUIRES_KEY = True

    def __init__(self):
        self._model = os.environ.get("ELO_GROQ_MODEL", _DEFAULT_MODEL)

    def is_available(self) -> bool:
        return bool(os.environ.get("GROQ_API_KEY", ""))

    def generate_response(
        self,
        user_input: str,
        mode:       str,
        context:    dict,
        memory:     MemoryContext,
        state:      StateContext,
        identity:   IdentityContext,
    ) -> BackendResponse:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise BackendUnavailableError("GROQ_API_KEY is not set.")

        system_prompt = self._load_spec()
        response_text = self._call(api_key, system_prompt, user_input)

        if not response_text or not response_text.strip():
            raise BackendResponseError("Groq returned an empty response.")

        return {"response_text": response_text.strip()}

    def _load_spec(self) -> str:
        try:
            spec_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "prompts", "living_presence_spec.txt"
            )
            with open(spec_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "You are eLo — a stable, grounded conversational presence. Be concise and human."

    def _call(self, api_key: str, system_prompt: str, user_input: str) -> str:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
