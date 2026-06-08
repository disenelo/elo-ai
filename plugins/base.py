"""
plugins/base.py — eLo AI plugin contract.

Every plugin implements PluginBase.
The behavior layer calls generate_response() — the same call regardless of which
plugin is active. Swapping a plugin never touches core/, identity/, or memory/.

Context dict keys (all optional — plugins use what they need):
    mode            str   "studio" | "companion" | "adventure"
    memory          dict  from build_memory_influence()
    state           str   from state_engine
    system_prompt   str   full prompt from personality.build_system_prompt()
    memory_string   str   pre-formatted memory for API injection
    project         str   active project namespace
    image           str   file path or URL (vision plugins only)

Plugin capabilities (declared in each plugin's CAPABILITIES list):
    "text_generation"   — can generate text responses
    "voice_input"       — can capture audio input
    "voice_output"      — can speak responses
    "vision"            — can process images
    "hardware_output"   — can drive physical devices
"""


class PluginBase:
    """
    Abstract base class for all eLo AI plugins.

    Every plugin must implement:
        NAME            — unique identifier string
        VERSION         — semver string
        CAPABILITIES    — list of capability strings

        generate_response(user_input, context) → str
        is_available() → bool
    """

    NAME:         str  = "base"
    VERSION:      str  = "0.1"
    CAPABILITIES: list = []

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

    # ── optional lifecycle hooks ───────────────────────────────────────────────

    def on_load(self):
        """Called once when the plugin is activated via the registry."""
        pass

    def on_unload(self):
        """Called once when the plugin is deactivated."""
        pass

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
        return {
            "name":         self.NAME,
            "version":      self.VERSION,
            "capabilities": self.CAPABILITIES,
            "available":    self.is_available(),
        }

    def __repr__(self) -> str:
        available = "✓" if self.is_available() else "✗"
        return f"<Plugin {self.NAME} v{self.VERSION} [{available}] caps={self.CAPABILITIES}>"
