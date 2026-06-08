"""
plugins/ — swappable backend adapters for eLo AI.

All plugins implement PluginBase from plugins/base.py.
All plugins expose generate_response(user_input, context) → str.
The behavior layer never imports plugins directly — it uses the registry.

Usage:
    from plugins.registry import registry
    registry.register_all_defaults()
    registry.activate("anthropic")   # or "offline", "local_llm", etc.
    response = registry.generate_response(user_input, context)
"""

from plugins.base     import PluginBase
from plugins.registry import registry

__all__ = ["PluginBase", "registry"]
