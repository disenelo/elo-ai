"""
plugins/registry.py — eLo AI plugin registry.

Manages plugin registration, activation, and the fallback chain.
The behavior layer never imports plugins directly — it always calls the registry.

Usage:
    from plugins.registry import registry

    # activate a plugin by name
    registry.activate("anthropic")

    # generate a response — same call regardless of active plugin
    response = registry.generate_response(user_input, context)

    # list what's registered and available
    registry.status()

Fallback chain:
    active_plugin → offline (always available, no API key needed)

Environment:
    ELO_PLUGIN    — name of the plugin to activate on startup
                    (default: "offline", falls back to "offline" if named plugin unavailable)
"""

import logging
import os

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Singleton registry for all eLo AI plugins."""

    def __init__(self):
        self._plugins: dict   = {}      # name → PluginBase instance
        self._active_name: str = None

    # ── registration ───────────────────────────────────────────────────────────

    def register(self, plugin) -> None:
        """
        Register a plugin instance. Must implement PluginBase.
        Later registrations with the same NAME replace earlier ones.
        """
        name = plugin.NAME

        # safety validation — reject plugins that violate constraints
        if hasattr(plugin, "validate"):
            violations = plugin.validate()
            if violations:
                logger.error(
                    "Plugin %r failed safety validation — NOT registered:\n  %s",
                    name, "\n  ".join(violations)
                )
                return   # refuse to register unsafe plugin

        self._plugins[name] = plugin
        logger.debug("Plugin registered: %s", name)

    def register_all_defaults(self):
        """
        Register the built-in eLo plugin set.
        Call once at startup before activating.
        """
        from plugins.anthropic.plugin  import AnthropicPlugin
        from plugins.local_llm.plugin  import LocalLLMPlugin
        from plugins.voice.plugin      import VoicePlugin
        from plugins.hardware.plugin   import HardwarePlugin
        from plugins.vision.plugin     import VisionPlugin

        # offline is always registered — it has no dependencies
        from core.behavior_engine import generate_offline_response
        self.register(_OfflinePlugin(generate_offline_response))

        self.register(AnthropicPlugin())
        self.register(LocalLLMPlugin())
        self.register(VoicePlugin())
        self.register(HardwarePlugin())
        self.register(VisionPlugin())

    # ── activation ─────────────────────────────────────────────────────────────

    def activate(self, name: str) -> bool:
        """
        Activate a registered plugin by name.
        Returns True if activated, False if not found or not available.
        """
        if name not in self._plugins:
            logger.warning("Plugin not registered: %s", name)
            return False

        plugin = self._plugins[name]
        if not plugin.is_available():
            logger.warning("Plugin not available: %s", name)
            return False

        # unload previous
        if self._active_name and self._active_name in self._plugins:
            self._plugins[self._active_name].on_unload()

        plugin.on_load()
        self._active_name = name
        logger.info("Plugin activated: %s", name)
        return True

    def activate_from_env(self):
        """
        Activate the plugin named in ELO_PLUGIN env var.
        Falls back to offline if the named plugin is unavailable.
        """
        name = os.environ.get("ELO_PLUGIN", "offline").lower()
        if not self.activate(name):
            logger.info("Falling back to offline plugin.")
            self.activate("offline")

    # ── response generation ────────────────────────────────────────────────────

    def generate_response(self, user_input: str, context: dict = None) -> str:
        """
        Generate a response using the active plugin.

        Falls back to offline if the active plugin fails or is unavailable.
        The behavior layer always calls this — never a plugin directly.
        """
        ctx = context or {}

        plugin = self._active_plugin()
        try:
            if plugin.is_available():
                return plugin.generate_response(user_input, ctx)
        except Exception as exc:
            logger.error("Plugin %s failed: %s — falling back to offline.", plugin.NAME, exc)

        # fallback
        offline = self._plugins.get("offline")
        if offline:
            return offline.generate_response(user_input, ctx)

        return f"[eLo: no plugin available for input: {user_input!r}]"

    # ── I/O hooks ──────────────────────────────────────────────────────────────

    def capture_input(self) -> str:
        """
        Capture input from the active plugin's input channel.
        Returns empty string if the active plugin has no input capability.
        Falls back to stdin.
        """
        plugin = self._active_plugin()
        if plugin.has_capability("voice_input"):
            captured = plugin.capture_input()
            if captured:
                return captured
        return input("You: ").strip()

    def deliver_output(self, response: str, context: dict = None):
        """
        Deliver response through all active output plugins.
        Runs deliver_output() on every registered plugin that has output capability
        and is available.
        """
        ctx = context or {}
        for plugin in self._plugins.values():
            if plugin.has_capability("voice_output") or plugin.has_capability("hardware_output"):
                if plugin.is_available():
                    try:
                        plugin.deliver_output(response, ctx)
                    except Exception as exc:
                        logger.error("Output plugin %s failed: %s", plugin.NAME, exc)

    # ── introspection ──────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return status of all registered plugins."""
        return {
            "active": self._active_name,
            "plugins": {name: p.describe() for name, p in self._plugins.items()},
        }

    def list_available(self) -> list:
        return [name for name, p in self._plugins.items() if p.is_available()]

    @property
    def active_name(self) -> str:
        return self._active_name or "none"

    def _active_plugin(self):
        if self._active_name and self._active_name in self._plugins:
            return self._plugins[self._active_name]
        # no active plugin — use offline if registered
        if "offline" in self._plugins:
            return self._plugins["offline"]
        from plugins.base import PluginBase
        return PluginBase()  # returns NotImplementedError if called

    def __repr__(self) -> str:
        return f"<PluginRegistry active={self._active_name} registered={list(self._plugins)}>"


# ── built-in offline plugin ────────────────────────────────────────────────────

class _OfflinePlugin:
    """
    The always-available offline plugin — wraps behavior_engine directly.
    Registered internally; not importable as a standalone plugin.
    """

    NAME         = "offline"
    VERSION      = "1.0"
    CAPABILITIES = ["text_generation"]

    def __init__(self, generate_fn):
        self._generate = generate_fn

    def generate_response(self, user_input: str, context: dict) -> str:
        mode   = context.get("mode",   "companion")
        memory = context.get("memory", {})
        return self._generate(user_input, memory, mode)

    def is_available(self) -> bool:
        return True   # no dependencies, always works

    def on_load(self):     pass
    def on_unload(self):   pass
    def capture_input(self): return ""
    def deliver_output(self, response, context): pass
    def has_capability(self, cap): return cap in self.CAPABILITIES

    def describe(self) -> dict:
        return {
            "name": self.NAME, "version": self.VERSION,
            "capabilities": self.CAPABILITIES, "available": True,
        }

    def __repr__(self):
        return f"<Plugin offline v{self.VERSION} [✓]>"


# ── global singleton ───────────────────────────────────────────────────────────

registry = PluginRegistry()
