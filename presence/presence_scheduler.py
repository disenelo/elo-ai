"""
presence/presence_scheduler.py — smooth transitions between presence states.

Holds current state and manages transitions:
- Hard transitions (immediate mode shift)
- Soft transitions (blend over time)
- Post-response settle (THINKING → OBSERVING after response delivered)
"""
from __future__ import annotations
import time

from presence.presence_state import PresenceMode, PresenceState


class PresenceScheduler:
    def __init__(self):
        self._current: PresenceState = PresenceState()  # starts idle
        self._previous: PresenceState | None = None
        self._queued:   PresenceState | None = None
        self._transition_start: float = time.monotonic()

    # ── public interface ──────────────────────────────────────────────────────

    def set(self, state: PresenceState, hard: bool = False) -> None:
        """
        Schedule a new presence state.
        hard=True  — immediate switch (no blend)
        hard=False — queue for after current state expires or on next tick
        """
        if hard:
            self._previous = self._current
            self._current  = state
            self._queued   = None
        else:
            self._queued = state

    def tick(self) -> PresenceState:
        """
        Returns current presence state. Advances if current state has expired.
        Call once per conversation turn or on a timer.
        """
        now = time.monotonic()
        elapsed = now - self._transition_start

        if elapsed >= self._current.duration and self._queued is not None:
            self._previous       = self._current
            self._current        = self._queued
            self._queued         = None
            self._transition_start = now

        return self._current

    def post_response_settle(self) -> None:
        """
        After eLo delivers a response, queue a gentle settle into OBSERVING.
        Doesn't fire if currently CELEBRATING — that should breathe.
        """
        if self._current.mode in (PresenceMode.CELEBRATING, PresenceMode.RESTING):
            return
        settle = PresenceState(
            mode      = PresenceMode.OBSERVING,
            intensity = 0.45,
            energy    = self._current.energy * 0.85,
            duration  = 3.0,
            mood      = "warm",
        )
        self.set(settle, hard=False)

    def current(self) -> PresenceState:
        return self._current

    def previous(self) -> PresenceState | None:
        return self._previous
