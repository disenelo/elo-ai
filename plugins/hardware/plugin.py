"""
plugins/hardware/plugin.py — Hardware I/O plugin.

Drives physical eLo hardware: Core Orb (NeoPixel), sensors, actuators.
Does NOT generate responses — runs deliver_output() alongside whatever text plugin is active.

Capabilities: hardware_output

Currently: simulation mode (prints to terminal).
Future: NeoPixel via rpi_ws281x, GPIO via RPi.GPIO.

Environment:
    ELO_HARDWARE_MODE   "simulate" (default) | "neopixel" | "gpio"
"""

import logging
import os
from plugins.base import PluginBase

logger = logging.getLogger(__name__)

_MODE = os.environ.get("ELO_HARDWARE_MODE", "simulate")


class HardwarePlugin(PluginBase):

    NAME         = "hardware"
    VERSION      = "0.1"
    CAPABILITIES = ["hardware_output"]

    def is_available(self) -> bool:
        # Simulation mode is always available.
        # Hardware mode requires rpi_ws281x or RPi.GPIO.
        if _MODE == "simulate":
            return True
        try:
            import rpi_ws281x   # noqa: F401
            return True
        except ImportError:
            return False

    def generate_response(self, user_input: str, context: dict) -> str:
        # Hardware plugin does not generate responses — it handles physical output only.
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(
            user_input,
            context.get("memory", {}),
            context.get("mode", "companion"),
        )

    def deliver_output(self, response: str, context: dict):
        """
        Update hardware state based on response context.

        Reads context["state"] from the state engine to determine the Orb animation.
        In simulation mode: prints. In hardware mode: drives NeoPixel.

        HARDWARE HOOK — replace simulate block with:
            from rpi_ws281x import PixelStrip, Color
            strip = PixelStrip(LED_COUNT, LED_PIN, ...)
            strip.begin()
            _set_orb_color(strip, state_to_color(state))
        """
        state = context.get("state", "exploring")

        _STATE_VISUALS = {
            "exploring":  "○ ~  (soft blue pulse)",
            "building":   "●●  (warm amber glow)",
            "focused":    "◉   (bright point)",
            "reflecting": "◌   (slow dim pulse)",
            "playful":    "✦✧  (rapid colour shift)",
            "resting":    "·   (minimal glow)",
        }

        visual = _STATE_VISUALS.get(state, "○")

        if _MODE == "simulate":
            print(f"[ORB] {visual}")
        else:
            # HARDWARE HOOK
            pass

    def on_load(self):
        logger.info("HardwarePlugin loaded — mode: %s", _MODE)
