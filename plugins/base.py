"""
plugins/base.py — eLo AI plugin contract.

Every plugin implements PluginBase.
Plugins extend OUTPUT LAYERS ONLY. They may never modify kernel logic,
routing decisions, or cognitive behaviour.

Safety constraints (class-level declarations every plugin must set):
    LAYER         str   "output" | "input" | "observability"
    KERNEL_SAFE   bool  True = plugin makes no kernel calls, no routing changes

Allowed layers:
    "output"        — generates or delivers responses (TTS, hardware, API)
    "input"         — captures raw input (STT, vision, sensor)
    "observability" — reads system state for monitoring (no side effects)

Plugin capabilities (declared in CAPABILITIES list):
    "text_generation"   — can generate text responses
    "voice_input"       — can capture audio input
    "voice_output"      — can speak responses
    "vision"            — can process images
    "hardware_output"   — can drive physical devices
    "observability"     — reads system events for monitoring

Context dict keys (all optional — plugins use what they need):
    mode            str   kernel routing mode
    system_prompt   str   full eLo identity prompt
    memory          dict  from memory_engine
    state           str   current state engine name
    project         str   active project namespace
    image           str   file path or URL (vision plugins only)
"""

import logging

logger = logging.getLogger(__name__)

# Valid layer declarations
_VALID_LAYERS = ("output", "input", "observability")


class PluginBase:
    """
    Abstract base class for all eLo AI plugins.

    Safety contract (class attributes — every plugin must declare):
        LAYER       — must be "output", "input", or "observability"
        KERNEL_SAFE — must be True (plugins may not modify kernel state)

    Required methods:
        generate_response(user_input, context) → str
        is_available() → bool
    """

    NAME:         str  = "base"
    VERSION:      str  = "0.1"
    CAPABILITIES: list = []

    # ── safety declarations (required) ────────────────────────────────────────
    LAYER:       str  = "output"   # "output" | "input" | "observability"
    KERNEL_SAFE: bool = True       # plugin does NOT modify kernel state

    # ── required ───────────────────────────────────────────────────────────────

    def generate_response(self, user_input: str, context: dict) -> str:
        """
        Generate a text response for user_input given context.

        This is the single shared interface across all plugins.
        The behavior layer always calls this method — never plugin internals.

        Args:
            user_input: Raw text from the user.
            context:    Dict with mode, memory, state, system_prompt, etc.

        Returns:
            Response string.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.generate_response() not implemented")

    def is_available(self) -> bool:
        """
        Return True if this plugin can currently run.

        Checks: API keys present, hardware connected, model loaded, etc.
        The registry calls this before delegating — if False, falls back to next.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.is_available() not implemented")

    # ── lifecycle hooks ───────────────────────────────────────────────────────

    def on_load(self):
        """Called once when plugin is activated. Safe to run setup here."""
        pass

    def on_unload(self):
        """Called once when plugin is deactivated. Release resources here."""
        pass

    def on_health_check(self) -> bool:
        """
        Periodic health check. Called by registry to verify the plugin is
        still operational. Returns True if healthy. Default: delegates to is_available().
        """
        return self.is_available()

    # ── safety constraint enforcement ─────────────────────────────────────────

    def validate(self) -> list:
        """
        Validate that the plugin meets safety constraints.
        Returns a list of violation strings. Empty list = valid.

        Called by registry on register(). A plugin with violations is registered
        but marked as unsafe and will not be activated automatically.
        """
        violations = []
        if self.LAYER not in _VALID_LAYERS:
            violations.append(
                f"LAYER={self.LAYER!r} is not valid. Must be one of {_VALID_LAYERS}."
            )
        if not self.KERNEL_SAFE:
            violations.append(
                "KERNEL_SAFE=False is not allowed. Plugins must not modify kernel state."
            )
        if not self.NAME or self.NAME == "base":
            violations.append("NAME must be set to a unique non-empty string.")
        if not self.VERSION:
            violations.append("VERSION must be set.")
        return violations

    # ── optional I/O hooks (voice, hardware) ──────────────────────────────────

    def capture_input(self) -> str:
        """
        Capture raw input from this plugin's source (microphone, camera, sensor).
        Only relevant for input plugins (voice, vision).
        Returns empty string if not supported.
        """
        return ""

    def deliver_output(self, response: str, context: dict):
        """
        Deliver the generated response through this plugin's output channel.
        Only relevant for output plugins (voice, hardware display).
        Default: no-op.
        """
        pass

    # ── introspection ──────────────────────────────────────────────────────────

    def has_capability(self, capability: str) -> bool:
        return capability in self.CAPABILITIES

    def describe(self) -> dict:
        violations = self.validate()
        return {
            "name":         self.NAME,
            "version":      self.VERSION,
            "layer":        self.LAYER,
            "kernel_safe":  self.KERNEL_SAFE,
            "capabilities": self.CAPABILITIES,
            "available":    self.is_available(),
            "valid":        len(violations) == 0,
            "violations":   violations,
        }

    def __repr__(self) -> str:
        available = "✓" if self.is_available() else "✗"
        return f"<Plugin {self.NAME} v{self.VERSION} [{available}] caps={self.CAPABILITIES}>"
