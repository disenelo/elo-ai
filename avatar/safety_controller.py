"""
avatar/safety_controller.py — eLo robot safety shutdown system.

Handles emergency stop, motion freeze, and fallback to safe idle posture.

Safety events are triggered by:
    1. safety_flag=False in incoming robot_signal   (automatic)
    2. SafetyController.trigger_emergency_stop()    (manual override)

States (in order of severity, highest survives transitions):
    NORMAL      — robot may operate
    FREEZE      — hold current position, no new motion
    IDLE_POSTURE — return to safe default posture, then hold
    EMERGENCY   — all actuators off, require explicit reset to recover

No AI logic. No routing. Pure state machine + fallback command generation.
"""

import enum
from dataclasses import dataclass
from datetime import datetime
from avatar.motor_abstraction import (
    CommandPacket, MotorCommand, CHANNELS, build_command_packet
)
from avatar.robot_signal import to_robot_signal


# ── safety states ──────────────────────────────────────────────────────────────

class SafetyState(enum.Enum):
    NORMAL       = "normal"         # all clear — pass commands through
    FREEZE       = "freeze"         # hold position — block new motion
    IDLE_POSTURE = "idle_posture"   # move to safe default, then hold
    EMERGENCY    = "emergency"      # all actuators off — manual reset required


# ── fallback idle posture command packet ──────────────────────────────────────
# This is the safe physical position the robot returns to on safety event.
# All values are conservative: upright, centred, still, dim orb.

def _build_idle_posture_packet() -> CommandPacket:
    """
    Return the pre-computed safe idle posture CommandPacket.
    Derived from robot_signal of a resting/neutral state — no AI logic.
    """
    signal = to_robot_signal(
        mode          = "SIMPLIFY",
        state_name    = "resting",
        emotion       = "neutral",
        intent        = "hold_space",
        energy        = 0.0,
        loop_detected = False,
    )
    # override safety_flag=True to allow this one specific move
    signal = dict(signal)
    signal["safety_flag"] = True
    signal["energy_level"] = 0.05   # just enough to actuate the posture move
    return build_command_packet(signal)

_IDLE_POSTURE_PACKET: CommandPacket = _build_idle_posture_packet()

# Emergency stop — identical packet but with safety_hold=True (zero all motors)
_EMERGENCY_STOP_PACKET: CommandPacket = CommandPacket(
    timestamp   = "emergency",
    safety_hold = True,
    motors      = _IDLE_POSTURE_PACKET.motors,
)


# ── safety controller ──────────────────────────────────────────────────────────

@dataclass
class SafetyEvent:
    """Record of a safety event for logging."""
    triggered_at:  str
    state:         SafetyState
    trigger_source: str   # "signal_flag" | "manual_override" | "manual_reset"
    details:       str


class SafetyController:
    """
    Robot safety state machine.

    Usage:
        ctrl = SafetyController()

        # in each turn
        packet = ctrl.process(robot_signal, motor_packet)

        # manual override
        ctrl.trigger_emergency_stop(reason="operator button pressed")
        ctrl.trigger_freeze(reason="obstacle detected")
        ctrl.trigger_idle_posture(reason="thermal warning")

        # reset (manual, intentional)
        ctrl.reset(reason="operator cleared")
    """

    def __init__(self):
        self._state: SafetyState = SafetyState.NORMAL
        self._log:   list        = []

    # ── state queries ─────────────────────────────────────────────────────────

    @property
    def state(self) -> SafetyState:
        return self._state

    @property
    def is_safe(self) -> bool:
        """True when robot may operate normally."""
        return self._state == SafetyState.NORMAL

    @property
    def log(self) -> list:
        """Immutable copy of safety event log."""
        return list(self._log)

    # ── main entry point ──────────────────────────────────────────────────────

    def process(self, robot_signal: dict, motor_packet: CommandPacket) -> CommandPacket:
        """
        Apply safety logic to an incoming motor command packet.

        Args:
            robot_signal:  Output of avatar/robot_signal.to_robot_signal().
            motor_packet:  Output of avatar/motor_abstraction.build_command_packet().

        Returns:
            CommandPacket — either the original (NORMAL), a freeze (FREEZE),
            the idle posture (IDLE_POSTURE), or emergency stop (EMERGENCY).

        No decision logic. Only: check flag → select packet.
        """
        # automatic trigger: safety_flag=False in signal
        if not robot_signal.get("safety_flag", True):
            if self._state == SafetyState.NORMAL:
                self._transition(SafetyState.FREEZE, "signal_flag",
                                 "safety_flag=False received from robot_signal")

        return self._current_packet(motor_packet)

    # ── manual triggers ───────────────────────────────────────────────────────

    def trigger_emergency_stop(self, reason: str = "manual override"):
        """Immediately cut all actuators. Requires explicit reset() to recover."""
        self._transition(SafetyState.EMERGENCY, "manual_override", reason)

    def trigger_freeze(self, reason: str = "manual override"):
        """Hold current position. Reset clears this state."""
        if self._state in (SafetyState.NORMAL, SafetyState.IDLE_POSTURE):
            self._transition(SafetyState.FREEZE, "manual_override", reason)

    def trigger_idle_posture(self, reason: str = "manual override"):
        """Return to safe default posture. Reset clears this state."""
        if self._state == SafetyState.NORMAL:
            self._transition(SafetyState.IDLE_POSTURE, "manual_override", reason)

    def reset(self, reason: str = "manual reset"):
        """
        Return to NORMAL state. Only valid from FREEZE or IDLE_POSTURE.
        EMERGENCY state requires explicit reset with reason.
        """
        if self._state == SafetyState.EMERGENCY and "emergency" not in reason.lower():
            # require deliberate acknowledgment to clear emergency
            return
        self._transition(SafetyState.NORMAL, "manual_reset", reason)

    # ── packet selection ──────────────────────────────────────────────────────

    def _current_packet(self, normal_packet: CommandPacket) -> CommandPacket:
        """Return the appropriate packet for the current safety state."""
        if self._state == SafetyState.NORMAL:
            return normal_packet
        if self._state == SafetyState.FREEZE:
            # freeze: send zero-motion packet (all motion motors = 0, orb dim)
            return _freeze_packet(normal_packet)
        if self._state == SafetyState.IDLE_POSTURE:
            return _IDLE_POSTURE_PACKET
        # EMERGENCY
        return _EMERGENCY_STOP_PACKET

    # ── state machine ─────────────────────────────────────────────────────────

    def _transition(self, new_state: SafetyState, source: str, details: str):
        """Record the transition and update state."""
        event = SafetyEvent(
            triggered_at   = datetime.utcnow().isoformat() + "Z",
            state          = new_state,
            trigger_source = source,
            details        = details,
        )
        self._log.append(event)
        self._state = new_state

    def status(self) -> dict:
        """Return current safety status as a plain dict."""
        return {
            "state":    self._state.value,
            "is_safe":  self.is_safe,
            "events":   len(self._log),
            "last":     self._log[-1].details if self._log else "",
        }


# ── freeze packet builder ─────────────────────────────────────────────────────

def _freeze_packet(original: CommandPacket) -> CommandPacket:
    """
    Build a freeze packet: zero all motion motors, keep orb dim.
    Preserves posture motors (hold current angles) but stops all locomotion.
    """
    frozen_motors = {}
    MOTION_MOTORS = {"left_wheel", "right_wheel", "base_rotation"}
    for name, cmd in original.motors.items():
        if name in MOTION_MOTORS:
            frozen_motors[name] = MotorCommand(
                cmd.channel, 0.0, cmd.unit, 1.0   # decelerate gently
            )
        elif name == "orb_brightness":
            # pulse orb slowly to indicate freeze state
            frozen_motors[name] = MotorCommand(cmd.channel, 0.15, cmd.unit, 1.0)
        elif name == "orb_pulse_rate":
            frozen_motors[name] = MotorCommand(cmd.channel, 0.5, "hz", 1.0)
        else:
            # posture motors: hold current position
            frozen_motors[name] = cmd

    return CommandPacket(
        timestamp   = datetime.utcnow().isoformat() + "Z",
        safety_hold = False,   # freeze holds posture — it is NOT a full stop
        motors      = frozen_motors,
    )
