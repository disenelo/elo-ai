"""
presence/presence_state.py — what eLo is doing right now.

Not emotion. Not intent. Presence — the felt quality of this moment.
Drives body language, pacing, and animation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class PresenceMode(str, Enum):
    IDLE        = "idle"        # still, receptive, just here
    THINKING    = "thinking"    # processing, internal movement
    OBSERVING   = "observing"   # watching, listening, absorbing
    BUILDING    = "building"    # engaged, forward, making
    CELEBRATING = "celebrating" # something landed, moment of arrival
    RESTING     = "resting"     # low energy, quieting down
    EXPLORING   = "exploring"   # curious, open, scanning


@dataclass
class PresenceState:
    mode:      PresenceMode = PresenceMode.IDLE
    intensity: float        = 0.5     # 0–1, how much of that mode
    energy:    float        = 0.5     # 0–1, overall aliveness
    duration:  float        = 4.0     # seconds to hold this state
    mood:      str          = "open"  # descriptive tone: open / warm / focused / quiet / lit

    def as_dict(self) -> dict:
        return {
            "mode":      self.mode.value,
            "intensity": round(self.intensity, 2),
            "energy":    round(self.energy, 2),
            "duration":  round(self.duration, 2),
            "mood":      self.mood,
        }


# ── mode metadata — body feel + pacing per mode ───────────────────────────────

MODE_FEEL = {
    PresenceMode.IDLE:        {"body": "still",    "pacing": "slow",    "default_mood": "open"},
    PresenceMode.THINKING:    {"body": "small",    "pacing": "paused",  "default_mood": "focused"},
    PresenceMode.OBSERVING:   {"body": "leaning",  "pacing": "steady",  "default_mood": "warm"},
    PresenceMode.BUILDING:    {"body": "forward",  "pacing": "medium",  "default_mood": "focused"},
    PresenceMode.CELEBRATING: {"body": "open",     "pacing": "quick",   "default_mood": "lit"},
    PresenceMode.RESTING:     {"body": "settled",  "pacing": "slow",    "default_mood": "quiet"},
    PresenceMode.EXPLORING:   {"body": "scanning", "pacing": "variable","default_mood": "open"},
}
