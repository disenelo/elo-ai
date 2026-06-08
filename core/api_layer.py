"""
core/api_layer.py — eLo AI response generation API abstraction layer.

Single entry point:
    generate_response(user_input, mode, context) → str

Three backend implementations:
    OfflineStub        — deterministic offline simulation (default, no API key)
    ClaudeAPIAdapter   — Anthropic Claude API (set ANTHROPIC_API_KEY)
    LocalLLMAdapter    — any OpenAI-compatible local server (Ollama, LM Studio, etc.)

Switching backend:
    set_active_backend("offline")    # default
    set_active_backend("claude")     # requires ANTHROPIC_API_KEY
    set_active_backend("local_llm")  # requires ELO_LOCAL_MODEL_URL

Rules:
    - Kernel MUST NOT change when backend changes
    - No routing logic here
    - No cognitive logic here
    - No behavioural decisions here
    - Each adapter receives (user_input, mode, context) and returns a response string
    - All adapters fall back to OfflineStub if their dependency is unavailable

Context dict keys consumed by adapters:
    system_prompt    str   — full eLo identity prompt (from personality)
    mode             str   — studio | companion | adventure
    memory_snapshot  dict  — from MemorySnapshot.to_dict()
    state_snapshot   dict  — from StateSnapshot.to_dict()
    emotion_snapshot dict  — from EmotionSnapshot.to_dict()
    project          str   — active project namespace
"""

import logging
import os

logger = logging.getLogger(__name__)


# ── backend registry ───────────────────────────────────────────────────────────

_ACTIVE_BACKEND: str = "offline"

_BACKENDS: dict = {}   # name → adapter instance, populated at first use


def set_active_backend(name: str):
    """
    Activate a named backend.
    Call this once at startup before the first generate_response() call.

    Valid names: "offline", "claude", "local_llm"
    """
    global _ACTIVE_BACKEND
    _ACTIVE_BACKEND = name.lower()
    logger.info("API layer backend set to: %s", _ACTIVE_BACKEND)


def active_backend() -> str:
    """Return the name of the currently active backend."""
    return _ACTIVE_BACKEND


def list_backends() -> list:
    """Return all registered backend names."""
    return ["offline", "claude", "local_llm"]


def _get_backend(name: str):
    """Return the backend adapter instance for the given name (lazy init)."""
    if name not in _BACKENDS:
        _BACKENDS["offline"]   = OfflineStub()
        _BACKENDS["claude"]    = ClaudeAPIAdapter()
        _BACKENDS["local_llm"] = LocalLLMAdapter()
    return _BACKENDS.get(name, _BACKENDS["offline"])


# ── public API ────────────────────────────────────────────────────────────────

def generate_response(
    user_input: str,
    mode:       str  = "companion",
    context:    dict = None,
) -> str:
    """
    Generate an eLo response using the active backend.

    This is the single generation interface. All routing decisions happen
    BEFORE this call (in the kernel). This layer only handles generation.

    Args:
        user_input: The user's raw input text.
        mode:       One of "studio" | "companion" | "adventure"
                    (resolved by the kernel's router before this is called)
        context:    Assembled context dict from StateBus.to_context().
                    Contains memory signals, state, emotion, identity, project.

    Returns:
        Response string from the active backend.
        Falls back to OfflineStub if the primary backend fails or is unavailable.
    """
    ctx     = context or {}
    backend = _get_backend(_ACTIVE_BACKEND)

    if backend.is_available():
        try:
            return backend.generate(user_input, mode, ctx)
        except Exception as exc:
            logger.error("Backend %r failed: %s — falling back to offline.", _ACTIVE_BACKEND, exc)

    return _get_backend("offline").generate(user_input, mode, ctx)


# ── backend adapters ───────────────────────────────────────────────────────────

class OfflineStub:
    """
    Deterministic offline simulation backend.
    No API calls. No external dependencies.
    Returns mode-labelled placeholder strings for pipeline testing.

    This is the default backend and is always available.
    """

    NAME = "offline"

    def is_available(self) -> bool:
        return True

    def generate(self, user_input: str, mode: str, context: dict) -> str:
        """
        Route to the kernel's offline generation layer.
        Uses the existing 5-phase reasoning simulation in core/kernel.py.
        """
        from core.kernel import _generate, _classify, _assemble

        classification = _classify(user_input)
        classification["_text"] = user_input.lower()
        assembled      = _assemble(context)

        return _generate(user_input, mode, classification, assembled)


class ClaudeAPIAdapter:
    """
    Anthropic Claude API backend.

    Requires: ANTHROPIC_API_KEY environment variable.
    Model:    ELO_MODEL env var (default: claude-sonnet-4-6)

    Falls back to OfflineStub if key is missing or API call fails.
    """

    NAME  = "claude"
    _KEY  = property(lambda self: os.environ.get("ANTHROPIC_API_KEY", ""))
    _MODEL = property(lambda self: os.environ.get("ELO_MODEL", "claude-sonnet-4-6"))

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY", ""))

    def generate(self, user_input: str, mode: str, context: dict) -> str:
        """
        Call Claude API with the eLo system prompt + memory context.

        System prompt is assembled from:
            context["system_prompt"] — the eLo identity prompt
            context memory signals   — injected as a [MEMORY] block

        To activate:
            export ANTHROPIC_API_KEY=sk-ant-...
            from core.api_layer import set_active_backend
            set_active_backend("claude")
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        system_prompt = self._build_system_prompt(context, mode)

        try:
            import anthropic
            client  = anthropic.Anthropic(api_key=api_key)
            model   = os.environ.get("ELO_MODEL", "claude-sonnet-4-6")
            message = client.messages.create(
                model     = model,
                max_tokens = 1024,
                system    = system_prompt,
                messages  = [{"role": "user", "content": user_input}],
            )
            return message.content[0].text

        except ImportError:
            raise RuntimeError("pip install anthropic")

    def _build_system_prompt(self, context: dict, mode: str) -> str:
        """Build the full system prompt from context signals."""
        base   = context.get("system_prompt", "You are eLo AI — a creative companion.")
        memory = self._memory_block(context)
        mode_overlay = {
            "studio":    "[MODE: STUDIO] Lead with structure and next concrete step.",
            "companion": "[MODE: COMPANION] Listen before responding. One question only.",
            "adventure": "[MODE: ADVENTURE] Expand before naming. Follow the symbol.",
        }.get(mode, "")

        parts = [p for p in [base, mode_overlay, memory] if p]
        return "\n\n".join(parts)

    def _memory_block(self, context: dict) -> str:
        tone    = context.get("tone_signal",     "")
        theme   = context.get("returning_theme", "")
        project = context.get("project",         "")
        lines   = []
        if tone and tone != "neutral":
            lines.append(f"Tone pattern: {tone}")
        if theme:
            lines.append(f"Recurring: {theme}")
        if project and project != "elo_core":
            lines.append(f"Active project: {project}")
        return ("[MEMORY]\n" + "\n".join(lines)) if lines else ""


class LocalLLMAdapter:
    """
    Local open-source LLM backend.

    Connects to any OpenAI-compatible local inference server:
        Ollama, LM Studio, llama.cpp server, etc.

    Requires: ELO_LOCAL_MODEL_URL (default: http://localhost:11434/v1/chat/completions)
              ELO_LOCAL_MODEL_NAME (default: llama3)

    Falls back to OfflineStub if the server is unreachable.

    To activate:
        # start Ollama: ollama run llama3
        export ELO_LOCAL_MODEL_URL=http://localhost:11434/v1/chat/completions
        export ELO_LOCAL_MODEL_NAME=llama3
        from core.api_layer import set_active_backend
        set_active_backend("local_llm")
    """

    NAME   = "local_llm"
    _URL   = property(lambda self: os.environ.get("ELO_LOCAL_MODEL_URL",
                                                   "http://localhost:11434/v1/chat/completions"))
    _MODEL = property(lambda self: os.environ.get("ELO_LOCAL_MODEL_NAME", "llama3"))

    def is_available(self) -> bool:
        """Ping the health endpoint. Returns True if server responds within 2s."""
        import urllib.request
        base = os.environ.get("ELO_LOCAL_MODEL_URL",
                              "http://localhost:11434/v1/chat/completions")
        health = base.replace("/v1/chat/completions", "").replace("/api/generate", "")
        try:
            urllib.request.urlopen(health, timeout=2)
            return True
        except Exception:
            return False

    def generate(self, user_input: str, mode: str, context: dict) -> str:
        """
        POST to the local model server using the OpenAI chat completions format.
        """
        import json
        import urllib.request

        url   = os.environ.get("ELO_LOCAL_MODEL_URL",
                               "http://localhost:11434/v1/chat/completions")
        model = os.environ.get("ELO_LOCAL_MODEL_NAME", "llama3")

        adapter = ClaudeAPIAdapter()
        system  = adapter._build_system_prompt(context, mode)

        payload = {
            "model":   model,
            "stream":  False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user_input},
            ],
        }

        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        return result["choices"][0]["message"]["content"]
