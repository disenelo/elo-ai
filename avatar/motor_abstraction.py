"""
avatar/motor_abstraction.py — eLo AI robot motor abstraction layer.

Translates robot_signal.py output into hardware-agnostic motor commands.
No AI logic. Only mapping tables and arithmetic.

Motor groups:
    HEAD      — head_tilt (degrees), head_pan (degrees)
    BODY      — body_lean_forward (normalized), body_lean_lateral (normalized)
    BASE      — left_wheel (normalized), right_wheel (normalized), base_rotation (normalized)
    ORB       — orb_brightness (0.0-1.0), orb_pulse_rate (Hz)

All motor values are normalised floats unless stated otherwise.
Actual hardware drivers plug in at HARDWARE HOOK points.

Entry point:
    build_command_packet(robot_signal) → CommandPacket

HARDWARE HOOK pattern:
    Each MotorCommand carries a channel index.
    Hardware adapter reads the index and calls the appropriate driver.
    The abstraction layer never calls hardware directly.

Usage:
    from avatar.robot_signal     import to_robot_signal
    from avatar.motor_abstraction import build_command_packet, apply_commands

    robot_sig = to_robot_signal(mode="CREATIVE", state_name="exploring", ...)
    packet    = build_command_packet(robot_sig)
    apply_commands(packet)   # HARDWARE HOOK — plug in real driver here
"""

import math
from dataclasses import dataclass, field
from datetime import datetime


# ── data types ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MotorCommand:
    """
    A single motor command.

    channel: int   — hardware channel index (servo number, motor ID, etc.)
    value:   float — target value in the motor's native unit
    unit:    str   — "degrees" | "normalized" | "hz" | "rpm"
    speed:   float — 0.0 (instant) to 1.0 (slowest) transition rate
    """
    channel: int
    value:   float
    unit:    str   = "normalized"   # "degrees" | "normalized" | "hz"
    speed:   float = 0.5            # transition speed (hardware-interpreted)


@dataclass
class CommandPacket:
    """
    A complete set of motor commands for one signal cycle.
    Passed to the hardware adapter's apply_commands() function.
    """
    timestamp:   str
    safety_hold: bool                         # if True, all motors freeze
    motors:      dict = field(default_factory=dict)   # name → MotorCommand

    def motor_values(self) -> dict:
        """Flat dict of {motor_name: value} — convenience for hardware adapters."""
        if self.safety_hold:
            return {name: 0.0 for name in self.motors}
        return {name: cmd.value for name, cmd in self.motors.items()}


# ── motor channel registry ────────────────────────────────────────────────────
# Channel indices. Modify to match your hardware pin/ID layout.

CHANNELS = {
    "head_tilt":          0,    # servo: head pitch (degrees, 0 = level)
    "head_pan":           1,    # servo: head yaw   (degrees, 0 = centre)
    "body_lean_forward":  2,    # servo/actuator: forward lean (normalized)
    "body_lean_lateral":  3,    # servo/actuator: side lean (normalized)
    "left_wheel":         4,    # motor: left drive wheel (normalized)
    "right_wheel":        5,    # motor: right drive wheel (normalized)
    "base_rotation":      6,    # motor: in-place rotation (normalized)
    "orb_brightness":     7,    # LED: orb glow intensity (normalized)
    "orb_pulse_rate":     8,    # LED: orb pulse frequency (Hz)
}


# ── posture → body + head angles ──────────────────────────────────────────────

_POSTURE_MAP: dict = {
    #                       head_tilt  head_pan  lean_fwd  lean_lat
    "upright":         (  0.0,       0.0,       0.00,     0.00),
    "lean_forward":    ( 10.0,       0.0,       0.30,     0.00),
    "open":            ( -5.0,       0.0,      -0.10,     0.00),
    "contracted":      (-10.0,       0.0,      -0.20,     0.00),
    "settled":         (  0.0,       0.0,       0.00,     0.00),
    "look_upward":     (-15.0,       0.0,      -0.10,     0.00),
    "head_tilt_left":  (  0.0,     -12.0,       0.00,     0.00),
}

_DEFAULT_POSTURE = (0.0, 0.0, 0.0, 0.0)


# ── direction → wheel differential speeds ─────────────────────────────────────

_DIRECTION_MAP: dict = {
    #                      left   right  rotation
    "stationary":    (0.00,  0.00,  0.00),
    "forward":       (0.50,  0.50,  0.00),
    "backward":      (-0.35, -0.35, 0.00),
    "rotating":      (0.30, -0.30,  1.00),
    "scanning":      (0.10, -0.10,  0.40),
}

_DEFAULT_DIRECTION = (0.0, 0.0, 0.0)


# ── energy level → orb parameters ────────────────────────────────────────────
# orb_brightness = energy directly
# orb_pulse_rate: low energy → slow pulse, high energy → fast pulse (Hz)

def _orb_pulse_rate(energy: float) -> float:
    """Map 0.0-1.0 energy to 0.3-2.0 Hz pulse rate."""
    return round(0.3 + energy * 1.7, 2)


# ── main builder ───────────────────────────────────────────────────────────────

def build_command_packet(robot_signal: dict) -> CommandPacket:
    """
    Convert a robot_signal dict into a CommandPacket.

    Input: output of avatar/robot_signal.to_robot_signal()
    Output: CommandPacket with all motor commands set

    If safety_flag=False: packet is created with safety_hold=True.
    All motors in a safety_hold packet return 0.0 from motor_values().
    Hardware adapters must check safety_hold before actuating.

    No decision logic. All values derived from lookup tables + arithmetic.
    """
    safety     = robot_signal.get("safety_flag",  True)
    posture    = robot_signal.get("posture",       "upright")
    direction  = robot_signal.get("direction",     "stationary")
    energy     = float(robot_signal.get("energy_level", 0.5))

    # transition speed: lower energy → slower transitions (smoother when calm)
    speed = round(0.2 + energy * 0.6, 2)

    # posture → head + body angles
    h_tilt, h_pan, lean_fwd, lean_lat = _POSTURE_MAP.get(posture, _DEFAULT_POSTURE)

    # direction → wheel speeds (scaled by energy)
    l_raw, r_raw, rot_raw = _DIRECTION_MAP.get(direction, _DEFAULT_DIRECTION)
    l_wheel   = round(l_raw   * energy, 3)
    r_wheel   = round(r_raw   * energy, 3)
    rotation  = round(rot_raw * energy, 3)

    motors = {
        "head_tilt":         MotorCommand(CHANNELS["head_tilt"],         round(h_tilt,  2), "degrees",    speed),
        "head_pan":          MotorCommand(CHANNELS["head_pan"],          round(h_pan,   2), "degrees",    speed),
        "body_lean_forward": MotorCommand(CHANNELS["body_lean_forward"], round(lean_fwd,3), "normalized", speed),
        "body_lean_lateral": MotorCommand(CHANNELS["body_lean_lateral"], round(lean_lat,3), "normalized", speed),
        "left_wheel":        MotorCommand(CHANNELS["left_wheel"],        l_wheel,           "normalized", 0.4),
        "right_wheel":       MotorCommand(CHANNELS["right_wheel"],       r_wheel,           "normalized", 0.4),
        "base_rotation":     MotorCommand(CHANNELS["base_rotation"],     rotation,          "normalized", 0.4),
        "orb_brightness":    MotorCommand(CHANNELS["orb_brightness"],    round(energy, 2),  "normalized", 1.0),
        "orb_pulse_rate":    MotorCommand(CHANNELS["orb_pulse_rate"],    _orb_pulse_rate(energy), "hz",  1.0),
    }

    return CommandPacket(
        timestamp   = datetime.utcnow().isoformat() + "Z",
        safety_hold = not safety,
        motors      = motors,
    )


# ── hardware adapter hook ──────────────────────────────────────────────────────

def apply_commands(packet: CommandPacket):
    """
    Apply a CommandPacket to the hardware.

    HARDWARE HOOK — replace this function's body with your hardware driver calls.

    Current behaviour: print a debug summary (safe for development).

    Raspberry Pi + Adafruit servo driver example:
        from adafruit_servokit import ServoKit
        kit = ServoKit(channels=16)
        for name, cmd in packet.motors.items():
            if cmd.unit == "degrees":
                kit.servo[cmd.channel].angle = cmd.value + 90  # offset to centre
            # ... (wheels via motor driver)

    Safety contract:
        ALWAYS check packet.safety_hold first.
        If True, send zero/hold to ALL actuators before returning.
    """
    if packet.safety_hold:
        # HARDWARE HOOK — send stop/hold to all actuators
        print(f"[MOTORS] SAFETY HOLD — all motors frozen  ts={packet.timestamp[-8:-1]}")
        return

    vals = packet.motor_values()
    print(
        f"[MOTORS]"
        f"  head=({vals['head_tilt']:+.1f}°,{vals['head_pan']:+.1f}°)"
        f"  lean=({vals['body_lean_forward']:+.2f},{vals['body_lean_lateral']:+.2f})"
        f"  wheels=({vals['left_wheel']:+.2f},{vals['right_wheel']:+.2f})"
        f"  rot={vals['base_rotation']:+.2f}"
        f"  orb={vals['orb_brightness']:.2f}@{vals['orb_pulse_rate']:.1f}Hz"
    )
    # HARDWARE HOOK — replace print with actual driver calls
