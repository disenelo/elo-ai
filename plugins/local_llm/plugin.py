"""
plugins/local_llm/plugin.py — Local open-source LLM plugin.

Connects to any OpenAI-compatible local inference server:
    Ollama, LM Studio, llama.cpp server, etc.

Environment:
    ELO_LOCAL_MODEL_URL   default: http://localhost:11434/v1/chat/completions
    ELO_LOCAL_MODEL_NAME  default: llama3

Capabilities: text_generation
"""

import logging
import os
from plugins.base import PluginBase

logger = logging.getLogger(__name__)

_URL   = os.environ.get("ELO_LOCAL_MODEL_URL",  "http://localhost:11434/v1/chat/completions")
_MODEL = os.environ.get("ELO_LOCAL_MODEL_NAME", "llama3")


class LocalLLMPlugin(PluginBase):

    NAME         = "local_llm"
    VERSION      = "0.1"
    CAPABILITIES = ["text_generation"]

    def is_available(self) -> bool:
        """Return True if the local server responds to a health check."""
        import urllib.request
        base = os.environ.get("ELO_LOCAL_MODEL_URL", _URL)
        health = base.replace("/v1/chat/completions", "/").replace("/api/generate", "/")
        try:
            with urllib.request.urlopen(health, timeout=2):
                return True
        except Exception:
            return False

    def generate_response(self, user_input: str, context: dict) -> str:
        import json, urllib.request

        system_prompt = context.get("system_prompt", "")
        memory_str    = context.get("memory_string", "")
        model         = os.environ.get("ELO_LOCAL_MODEL_NAME", _MODEL)
        url           = os.environ.get("ELO_LOCAL_MODEL_URL",  _URL)

        full_system = system_prompt
        if memory_str:
            full_system += f"\n\n[MEMORY CONTEXT]\n{memory_str}\n[/MEMORY CONTEXT]"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user",   "content": user_input},
            ],
            "stream": False,
        }

        try:
            data = json.dumps(payload).encode()
            req  = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]

        except Exception as exc:
            logger.error("LocalLLMPlugin error: %s", exc)
            from core.behavior_engine import generate_offline_response
            return generate_offline_response(
                user_input,
                context.get("memory", {}),
                context.get("mode", "companion"),
            )
