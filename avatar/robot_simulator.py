"""
avatar/robot_simulator.py — eLo robot simulation mode.

Simulates robot movement without hardware.
Mirrors real signal output exactly.
Allows testing before physical deployment.

Usage:
    sim = RobotSimulator()
    sim.step(robot_signal, motor_packet)   # simulate one turn
    sim.report()                           # print state summary
    sim.history                            # list of simulated frames

The simulator is a drop-in replacement for apply_commands() in motor_abstraction.py.
It produces identical logs to what real hardware would receive.
No AI logic. No hardware calls. Pure state tracking.

Switching between simulation and hardware:
    if SIMULATION_MODE:
        sim.step(robot_signal, motor_packet)
    else:
        apply_commands(motor_packet)   # real hardware
"""

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from avatar.motor_abstraction import CommandPacket
from avatar.safety_controller import SafetyController, SafetyState

_SIMULATION_MODE = os.environ.get("ELO_ROBOT_SIM", "1") == "1"


# ── simulated frame ────────────────────────────────────────────────────────────

@dataclass
class SimFrame:
    """One simulated robot state at a point in time."""
    timestamp:    str
    safety_state: str
    safety_hold:  bool
    motor_values: dict
    robot_signal: dict


# ── simulator ──────────────────────────────────────────────────────────────────

class RobotSimulator:
    """
    Simulates robot movement without hardware.

    Mirrors the real signal pipeline exactly:
        robot_signal → SafetyController → CommandPacket → motor_values

    State is tracked across frames — the simulator accumulates a history
    of all simulated positions for inspection and playback.
    """

    def __init__(self, max_history: int = 500, verbose: bool = True):
        self._safety    = SafetyController()
        self._history:  list = []
        self._max_hist  = max_history
        self._verbose   = verbose
        self._frame_num = 0

        # simulated physical state (angles and positions)
        self._sim_state = {
            "head_tilt_deg":         0.0,
            "head_pan_deg":          0.0,
            "body_lean_forward":     0.0,
            "body_lean_lateral":     0.0,
            "left_wheel_speed":      0.0,
            "right_wheel_speed":     0.0,
            "base_rotation_speed":   0.0,
            "orb_brightness":        0.3,
            "orb_pulse_rate_hz":     0.5,
        }

    # ── main step ─────────────────────────────────────────────────────────────

    def step(self, robot_signal: dict, motor_packet: CommandPacket) -> SimFrame:
        """
        Simulate one turn.

        Args:
            robot_signal:  Output of avatar/robot_signal.to_robot_signal()
            motor_packet:  Output of avatar/motor_abstraction.build_command_packet()

        Returns:
            SimFrame — the simulated state for this turn.
        """
        self._frame_num += 1

        # run through safety controller (same as real path)
        safe_packet = self._safety.process(robot_signal, motor_packet)
        vals        = safe_packet.motor_values()

        # update simulated physical state
        self._update_sim_state(vals, safe_packet.safety_hold)

        frame = SimFrame(
            timestamp    = datetime.utcnow().isoformat() + "Z",
            safety_state = self._safety.state.value,
            safety_hold  = safe_packet.safety_hold,
            motor_values = dict(vals),
            robot_signal = dict(robot_signal),
        )

        self._history.append(frame)
        if len(self._history) > self._max_hist:
            self._history.pop(0)

        if self._verbose:
            self._print_frame(frame)

        return frame

    # ── simulated state update ────────────────────────────────────────────────

    def _update_sim_state(self, motor_values: dict, safety_hold: bool):
        """
        Update the simulated physical state from motor values.
        Uses simple linear interpolation — not physics, just readability.
        """
        lerp = lambda current, target, rate=0.3: current + (target - current) * rate

        if safety_hold:
            # safety hold: decelerate all motion, hold posture
            self._sim_state["left_wheel_speed"]    = lerp(self._sim_state["left_wheel_speed"],    0.0, 0.5)
            self._sim_state["right_wheel_speed"]   = lerp(self._sim_state["right_wheel_speed"],   0.0, 0.5)
            self._sim_state["base_rotation_speed"] = lerp(self._sim_state["base_rotation_speed"], 0.0, 0.5)
            self._sim_state["orb_brightness"]      = lerp(self._sim_state["orb_brightness"],      0.0, 0.2)
            return

        mv = motor_values
        self._sim_state["head_tilt_deg"]       = lerp(self._sim_state["head_tilt_deg"],       mv.get("head_tilt", 0.0))
        self._sim_state["head_pan_deg"]        = lerp(self._sim_state["head_pan_deg"],        mv.get("head_pan",  0.0))
        self._sim_state["body_lean_forward"]   = lerp(self._sim_state["body_lean_forward"],   mv.get("body_lean_forward", 0.0))
        self._sim_state["body_lean_lateral"]   = lerp(self._sim_state["body_lean_lateral"],   mv.get("body_lean_lateral", 0.0))
        self._sim_state["left_wheel_speed"]    = lerp(self._sim_state["left_wheel_speed"],    mv.get("left_wheel", 0.0))
        self._sim_state["right_wheel_speed"]   = lerp(self._sim_state["right_wheel_speed"],   mv.get("right_wheel", 0.0))
        self._sim_state["base_rotation_speed"] = lerp(self._sim_state["base_rotation_speed"], mv.get("base_rotation", 0.0))
        self._sim_state["orb_brightness"]      = lerp(self._sim_state["orb_brightness"],      mv.get("orb_brightness", 0.3))
        self._sim_state["orb_pulse_rate_hz"]   = mv.get("orb_pulse_rate", 0.5)

    # ── display ───────────────────────────────────────────────────────────────

    def _print_frame(self, frame: SimFrame):
        ss  = self._sim_state
        sig = frame.robot_signal
        hold_tag = " [HOLD]" if frame.safety_hold else ""
        print(
            f"[SIM #{self._frame_num:03d}]"
            f"{hold_tag}"
            f"  {frame.safety_state:12}"
            f"  mode={sig.get('mode','?'):<16}"
            f"  state={sig.get('state_name',sig.get('motion_state','?'))}"
        )
        if not frame.safety_hold:
            print(
                f"           "
                f"  head=({ss['head_tilt_deg']:+.1f}°,{ss['head_pan_deg']:+.1f}°)"
                f"  lean=({ss['body_lean_forward']:+.2f},{ss['body_lean_lateral']:+.2f})"
                f"  wheels=({ss['left_wheel_speed']:+.2f},{ss['right_wheel_speed']:+.2f})"
                f"  orb={ss['orb_brightness']:.2f}@{ss['orb_pulse_rate_hz']:.1f}Hz"
            )

    def report(self):
        """Print a summary of the simulation history."""
        print()
        print("=" * 60)
        print(f"  eLo Robot Simulation — {self._frame_num} frames")
        print("=" * 60)
        print(f"  Safety state:   {self._safety.state.value}")
        print(f"  Safety events:  {len(self._safety.log)}")
        print()
        print("  Final simulated state:")
        for key, val in self._sim_state.items():
            print(f"    {key:<28} {val:+.3f}")
        if self._safety.log:
            print()
            print("  Safety log:")
            for ev in self._safety.log:
                print(f"    [{ev.state.value:12}] {ev.details[:50]}")
        print("=" * 60)

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def history(self) -> list:
        """All simulated frames (list of SimFrame)."""
        return list(self._history)

    @property
    def current_state(self) -> dict:
        """Current simulated physical state."""
        return dict(self._sim_state)

    @property
    def safety(self) -> SafetyController:
        """The safety controller instance (for manual overrides)."""
        return self._safety

    def export_json(self, path: str):
        """Export simulation history to a JSON file for analysis."""
        data = [
            {
                "frame":        i + 1,
                "timestamp":    f.timestamp,
                "safety_state": f.safety_state,
                "safety_hold":  f.safety_hold,
                "motor_values": f.motor_values,
                "signal_mode":  f.robot_signal.get("mode", ""),
                "signal_state": f.robot_signal.get("motion_state", ""),
            }
            for i, f in enumerate(self._history)
        ]
        with open(path, "w") as fp:
            json.dump({"frames": data}, fp, indent=2)
        return path


# ── module-level helpers ───────────────────────────────────────────────────────

def is_simulation_mode() -> bool:
    """Return True if ELO_ROBOT_SIM=1 (default)."""
    return _SIMULATION_MODE


def simulation_or_hardware(sim: RobotSimulator, robot_signal: dict, motor_packet: CommandPacket):
    """
    Route to simulator or real hardware based on ELO_ROBOT_SIM env var.

    Usage:
        sim = RobotSimulator()
        simulation_or_hardware(sim, robot_signal, motor_packet)
    """
    if _SIMULATION_MODE:
        sim.step(robot_signal, motor_packet)
    else:
        from avatar.motor_abstraction import apply_commands
        apply_commands(motor_packet)    # HARDWARE HOOK
