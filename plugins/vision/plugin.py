"""
plugins/vision/plugin.py — Vision plugin (future).

Adds image understanding to eLo AI.
When an image is passed in context["image"], this plugin analyses it and
incorporates visual context into the response.

Capabilities: text_generation, vision

Future integrations:
    - Claude claude-sonnet-4-6 vision (Anthropic API + image attachment)
    - LLaVA / BakLLaVA (local multimodal model)
    - CLIP embeddings for symbolic/aesthetic analysis

Context keys used:
    image   str   file path, URL, or base64 data URI
    mode    str   as usual
    memory  dict  as usual
"""

import logging
from plugins.base import PluginBase

logger = logging.getLogger(__name__)


class VisionPlugin(PluginBase):

    NAME         = "vision"
    VERSION      = "0.1"
    CAPABILITIES = ["text_generation", "vision"]

    def is_available(self) -> bool:
        # Available when a vision-capable model is configured.
        # Requires ANTHROPIC_API_KEY (for Claude vision) or local vision model.
        import os
        return bool(os.environ.get("ANTHROPIC_API_KEY", ""))

    def generate_response(self, user_input: str, context: dict) -> str:
        image = context.get("image", "")

        if not image:
            # no image — behave like the anthropic text plugin
            from plugins.anthropic.plugin import AnthropicPlugin
            return AnthropicPlugin().generate_response(user_input, context)

        if not self.is_available():
            return self._offline_fallback(user_input, context)

        try:
            return self._vision_response(user_input, image, context)
        except Exception as exc:
            logger.error("VisionPlugin error: %s", exc)
            return self._offline_fallback(user_input, context)

    def _vision_response(self, user_input: str, image: str, context: dict) -> str:
        """
        Call Claude with image attachment.

        HARDWARE HOOK — replace with live implementation:
            import anthropic, base64, pathlib
            client = anthropic.Anthropic()
            img_data = base64.b64encode(pathlib.Path(image).read_bytes()).decode()
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=context.get("system_prompt", ""),
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64",
                         "media_type": "image/jpeg", "data": img_data}},
                        {"type": "text", "text": user_input},
                    ],
                }],
            )
            return message.content[0].text
        """
        logger.info("VisionPlugin: vision response stub — image=%s", image[:40])
        return f"[Vision stub] Image received: {image[:40]}. Connect Claude vision API to activate."

    def _offline_fallback(self, user_input: str, context: dict) -> str:
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(
            user_input,
            context.get("memory", {}),
            context.get("mode", "companion"),
        )
