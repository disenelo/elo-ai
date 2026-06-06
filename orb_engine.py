"""
orb_engine.py — Core Orb state simulator.

State machine: idle → listening → thinking → insight → error → idle
Hardware hook points marked with # HARDWARE HOOK for NeoPixel / Raspberry Pi GPIO.
"""

from enum import Enum


class OrbState(Enum):
    IDLE      = "idle"       # soft pulse — waiting
    LISTENING = "listening"  # active glow — capturing input
    THINKING  = "thinking"   # cycling animation — processing
    INSIGHT   = "insight"    # bright flash — idea arrived
    ERROR     = "error"      # flicker — something went wrong


_VISUALS = {
    OrbState.IDLE:      "○  (soft pulse)",
    OrbState.LISTENING: "●  (active glow)",
    OrbState.THINKING:  "◌◌ (cycling...)",
    OrbState.INSIGHT:   "★  (flash!)",
    OrbState.ERROR:     "✗  (flicker)",
}


class OrbEngine:

    def __init__(self, silent: bool = False):
        self._state = OrbState.IDLE
        self._silent = silent
        self._listeners: list = []

    @property
    def state(self) -> OrbState:
        return self._state

    def set_state(self, new_state: OrbState):
        if new_state == self._state:
            return
        old = self._state
        self._state = new_state
        self._render(new_state)
        for fn in self._listeners:
            try:
                fn(old, new_state)
            except Exception:
                pass

    def on_change(self, callback):
        self._listeners.append(callback)

    def _render(self, state: OrbState):
        if not self._silent:
            print(f"[ORB] {_VISUALS.get(state, state.value)}")
        # HARDWARE HOOK — replace print with NeoPixel animation:
        # from neopixel import NeoPixel
        # _animate(state, strip=self._strip)

    # convenience transitions
    def listen(self):   self.set_state(OrbState.LISTENING)
    def think(self):    self.set_state(OrbState.THINKING)
    def insight(self):  self.set_state(OrbState.INSIGHT)
    def idle(self):     self.set_state(OrbState.IDLE)
    def error(self):    self.set_state(OrbState.ERROR)


def run_orb_cli():
    """Standalone CLI simulator for dev and demos."""
    orb = OrbEngine()
    commands = {"idle": orb.idle, "listen": orb.listen, "think": orb.think,
                "insight": orb.insight, "error": orb.error}

    print("Core Orb CLI —", ", ".join(commands), ", status, quit")
    orb.idle()

    while True:
        try:
            cmd = input("orb > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nOrb going dark.")
            break
        if cmd in ("quit", "q"):
            break
        elif cmd == "status":
            print(f"[ORB] state: {orb.state.value}")
        elif cmd in commands:
            commands[cmd]()
        else:
            print(f"Unknown: {cmd!r}")
