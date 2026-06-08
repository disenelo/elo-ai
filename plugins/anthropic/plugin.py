"""
plugins/anthropic/plugin.py — Anthropic Claude API plugin.

Wraps the Claude API via the Anthropic SDK.
Falls back to the offline plugin if ANTHROPIC_API_KEY is not set.

Capabilities: text_generation
"""

import os
import logging
from plugins.base import PluginBase

logger = logging.getLogger(__name__)

_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
_MODEL   = os.environ.get("ELO_MODEL", "claude-sonnet-4-6")


class AnthropicPlugin(PluginBase):

    NAME         = "anthropic"
    VERSION      = "1.0"
    CAPABILITIES = ["text_generation"]

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY", ""))

    def generate_response(self, user_input: str, context: dict) -> str:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            logger.warning("AnthropicPlugin: ANTHROPIC_API_KEY not set.")
            return self._offline_fallback(user_input, context)

        system_prompt = context.get("system_prompt", "")
        memory_str    = context.get("memory_string", "")

        full_system = system_prompt
        if memory_str:
            full_system += f"\n\n[MEMORY CONTEXT]\n{memory_str}\n[/MEMORY CONTEXT]"

        try:
            import anthropic
            client  = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=os.environ.get("ELO_MODEL", "claude-sonnet-4-6"),
                max_tokens=1024,
                system=full_system,
                messages=[{"role": "user", "content": user_input}],
            )
            return message.content[0].text

        except ImportError:
            logger.error("Run: pip install anthropic")
            return self._offline_fallback(user_input, context)

        except Exception as exc:
            logger.error("AnthropicPlugin error: %s", exc)
            return self._offline_fallback(user_input, context)

    def _offline_fallback(self, user_input: str, context: dict) -> str:
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(
            user_input,
            context.get("memory", {}),
            context.get("mode", "companion"),
        )
