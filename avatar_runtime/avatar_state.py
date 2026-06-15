"""
avatar_runtime/avatar_state.py — canonical runtime state for eLo's body.

Single source of truth for what eLo is doing physically at any moment.
Consumed by animation_brain, presence_driver, and the Blender/Unity bridges.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class AvatarRuntimeState:
    # current animation
    clip:       str   = "idle"
    speed:      float = 0.6
    intensity:  float = 0.5

    # presence layer
    mode:       str   = "idle"   # presence mode name
    energy:     float = 0.5
    mood:       str   = "open"

    # timing
    duration:   float = 4.0     # seconds to hold this state
    elapsed:    float = 0.0     # seconds spent in this state

    # transitions
    blending:   bool  = False   # True during a cross-fade
    blend_from: str   = ""      # clip being blended away from

    def is_expired(self) -> bool:
        return self.elapsed >= self.duration

    def as_dict(self) -> dict:
        return {
            "clip":       self.clip,
            "speed":      round(self.speed, 3),
            "intensity":  round(self.intensity, 3),
            "mode":       self.mode,
            "energy":     round(self.energy, 3),
            "mood":       self.mood,
            "duration":   round(self.duration, 3),
            "blending":   self.blending,
        }
