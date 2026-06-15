"""
avatar_runtime/animation_brain.py — decides what to play and when to change.

Input:  command dict from avatar_controller
Output: AvatarRuntimeState

Rules:
    - Slow transitions — minimum 1.5s before a clip switch is allowed
    - Energy gates motion — below 0.15, stay in idle
    - CELEBRATE never cuts short — holds until duration expires
    - Mode changes blend from previous clip, not hard-cut
"""
from __future__ import annotations
import time

from avatar_runtime.avatar_state import AvatarRuntimeState


_MIN_HOLD = 1.5   # minimum seconds before a clip switch


class AnimationBrain:
    def __init__(self):
        self._state: AvatarRuntimeState = AvatarRuntimeState()
        self._last_tick: float = time.monotonic()

    def update(self, command: dict) -> AvatarRuntimeState:
        """
        Update animation state from a new command.
        Returns the (possibly unchanged) current state.
        """
        now     = time.monotonic()
        delta   = now - self._last_tick
        self._last_tick = now
        self._state.elapsed += delta

        # energy gate
        if command.get("energy", 0.5) < 0.15:
            command = dict(command)
            command["animation"] = "idle"
            command["speed"]     = 0.3

        incoming_clip = command.get("animation", "idle")
        can_switch    = (
            self._state.elapsed >= _MIN_HOLD
            and not (self._state.mode == "celebrating" and not self._state.is_expired())
        )

        if incoming_clip != self._state.clip and can_switch:
            self._state.blend_from = self._state.clip
            self._state.blending   = True
            self._state.clip       = incoming_clip
            self._state.elapsed    = 0.0
        elif incoming_clip == self._state.clip:
            self._state.blending = False

        # always update non-clip fields
        self._state.speed     = command.get("speed",     self._state.speed)
        self._state.intensity = command.get("intensity", self._state.intensity)
        self._state.mode      = command.get("mode",      self._state.mode)
        self._state.energy    = command.get("energy",    self._state.energy)
        self._state.mood      = command.get("mood",      self._state.mood)
        self._state.duration  = command.get("duration",  self._state.duration)

        return self._state

    def current(self) -> AvatarRuntimeState:
        return self._state
