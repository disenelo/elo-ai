"""
runtime/lifecycle.py — eLo Cognitive Lifecycle

Canonical lifecycle for the One Brain. eLo is not a service that starts and
stops. He moves through states of attention, engagement, rest, consolidation,
dreaming, and return.

The document that established this:
    Four-Layer Identity Model (David / Chief Architect, 2026-08-31)
    Source: docs/architecture/_intake/SOURCE_2026-08-31_...

Lifecycle states (canonical order, one direction):

    AWAKE        — present, loaded, ready. State at boot or after RESTORED.
    ENGAGED      — active interaction underway. Entered on every user turn.
    PROCESSING   — cognitive cycle running between input and output.
    LOW_LOAD     — interaction ended; recent activity; no active input.
    RECHARGING   — extended idle. NREM consolidation eligible (≥ 10 min idle).
    CONSOLIDATING — actively running memory consolidation (NREM phase).
    DREAMING     — REM analogue: recombination, imagination, narrative.
    RESTORED     — dream complete, ready to wake.

The cycle re-enters from RESTORED → AWAKE on the next turn.

The critical distinction (from the founding document):

    REAL EXPERIENCE
        → episodic trace
        → significance assessment
        → memory candidate
        → consolidation
        → long-term memory

    DREAM / SIMULATION
        → internally generated experience
        → reflection
        → optional retention ONLY if it earns significance

A dream entry MUST NOT automatically become factual memory.
"""
from __future__ import annotations

import time
from enum import Enum


class LifecycleState(str, Enum):
    AWAKE         = "awake"
    ENGAGED       = "engaged"
    PROCESSING    = "processing"
    LOW_LOAD      = "low_load"
    RECHARGING    = "recharging"
    CONSOLIDATING = "consolidating"
    DREAMING      = "dreaming"
    RESTORED      = "restored"


# Idle-time thresholds (seconds)
_LOW_LOAD_IDLE    = 120   # 2 min → LOW_LOAD
_RECHARGING_IDLE  = 600   # 10 min → RECHARGING (mirrors dream DREAM_IDLE_THRESHOLD)


class LifecycleManager:
    """
    Tracks eLo's lifecycle state across turns and idle periods.

    Usage:
        manager = LifecycleManager()
        # --- per user turn ---
        manager.on_turn()
        # --- per ambient tick ---
        state = manager.tick()
        # --- when dream starts ---
        manager.enter_dream()
        # --- after dream ---
        manager.exit_dream()
        # --- to get current state string ---
        s = manager.state_value    # "dreaming" | "recharging" | etc.
    """

    def __init__(self) -> None:
        self._state            = LifecycleState.AWAKE
        self._last_activity_ts = time.time()

    # ── Turn hooks ────────────────────────────────────────────────────────────

    def on_turn(self) -> None:
        """Call at the start of every user turn."""
        self._last_activity_ts = time.time()
        if self._state not in (LifecycleState.DREAMING, LifecycleState.CONSOLIDATING):
            self._state = LifecycleState.ENGAGED

    def on_processing_start(self) -> None:
        """Call when the cognitive cycle begins (after input, before output)."""
        if self._state not in (LifecycleState.DREAMING, LifecycleState.CONSOLIDATING):
            self._state = LifecycleState.PROCESSING

    def on_processing_end(self) -> None:
        """Call when the cognitive cycle completes."""
        if self._state == LifecycleState.PROCESSING:
            self._state = LifecycleState.ENGAGED

    # ── Idle tick ─────────────────────────────────────────────────────────────

    def tick(self) -> LifecycleState:
        """
        Call periodically during idle (e.g. every ambient_thought() cycle).
        Applies idle-time transitions; never interrupts DREAMING or CONSOLIDATING.
        Returns the current state after transition.
        """
        if self._state in (LifecycleState.DREAMING,
                           LifecycleState.CONSOLIDATING,
                           LifecycleState.RESTORED):
            return self._state

        idle = time.time() - self._last_activity_ts

        if idle >= _RECHARGING_IDLE:
            self._state = LifecycleState.RECHARGING
        elif idle >= _LOW_LOAD_IDLE:
            self._state = LifecycleState.LOW_LOAD

        return self._state

    # ── Dream / consolidation transitions ────────────────────────────────────

    def enter_consolidating(self) -> None:
        """Enter NREM consolidation phase (runs during RECHARGING)."""
        self._state = LifecycleState.CONSOLIDATING

    def exit_consolidating(self) -> None:
        """Return to RECHARGING after consolidation completes."""
        self._state = LifecycleState.RECHARGING

    def enter_dream(self) -> None:
        """Enter REM dream phase."""
        self._state = LifecycleState.DREAMING

    def exit_dream(self) -> None:
        """Mark dream complete; caller should call mark_awake() on next turn."""
        self._state = LifecycleState.RESTORED

    def mark_awake(self) -> None:
        """Explicitly return to AWAKE (e.g. after RESTORED, before first turn)."""
        self._state = LifecycleState.AWAKE

    # ── Accessors ─────────────────────────────────────────────────────────────

    @property
    def state(self) -> LifecycleState:
        return self._state

    @property
    def state_value(self) -> str:
        return self._state.value

    @property
    def idle_seconds(self) -> float:
        return time.time() - self._last_activity_ts
