"""
dashboard/robot_telemetry.py — eLo robot telemetry system.

Read-only streaming of robot state, motion commands, safety status, and history.
No control logic. No hardware calls. Purely observational.

Endpoints:
    GET /telemetry/stream    — SSE live stream of every simulated frame
    GET /telemetry/state     — current robot state as JSON
    GET /telemetry/safety    — safety controller status + event log
    GET /telemetry/history   — last N frames as JSON array
    GET /telemetry/status    — server health

Usage:
    sim     = RobotSimulator()
    telem   = RobotTelemetry(sim)

    # attach to an existing robot loop
    for robot_signal, motor_packet in robot_loop():
        frame = sim.step(robot_signal, motor_packet)
        telem.record(frame)     # adds frame to telemetry stream

    # start HTTP server in background
    telem.start_server(port=5052)
"""

import json
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from avatar.robot_simulator import RobotSimulator, SimFrame


# ── telemetry record ───────────────────────────────────────────────────────────

def _frame_to_dict(frame: SimFrame, sim: RobotSimulator) -> dict:
    """Convert a SimFrame + simulator state into a telemetry record."""
    ss = sim.current_state
    return {
        "timestamp":     frame.timestamp,
        "safety_state":  frame.safety_state,
        "safety_hold":   frame.safety_hold,
        "is_safe":       not frame.safety_hold and frame.safety_state == "normal",

        "current_state": {
            "head_tilt_deg":         ss.get("head_tilt_deg",         0.0),
            "head_pan_deg":          ss.get("head_pan_deg",          0.0),
            "body_lean_forward":     ss.get("body_lean_forward",     0.0),
            "body_lean_lateral":     ss.get("body_lean_lateral",     0.0),
            "left_wheel_speed":      ss.get("left_wheel_speed",      0.0),
            "right_wheel_speed":     ss.get("right_wheel_speed",     0.0),
            "base_rotation_speed":   ss.get("base_rotation_speed",   0.0),
            "orb_brightness":        ss.get("orb_brightness",        0.3),
            "orb_pulse_rate_hz":     ss.get("orb_pulse_rate_hz",     0.5),
        },

        "motion_commands": frame.motor_values,

        "robot_signal": {
            "mode":         frame.robot_signal.get("mode",         ""),
            "motion_state": frame.robot_signal.get("motion_state", ""),
            "posture":      frame.robot_signal.get("posture",      ""),
            "direction":    frame.robot_signal.get("direction",    ""),
            "energy_level": frame.robot_signal.get("energy_level", 0.0),
            "intent":       frame.robot_signal.get("intent",       ""),
        },
    }


# ── telemetry collector ────────────────────────────────────────────────────────

class RobotTelemetry:
    """
    Read-only telemetry collector for the eLo robot system.

    Attach to a RobotSimulator and call record() after each step.
    Query state, safety, and history via the HTTP server or direct properties.
    """

    def __init__(self, simulator: RobotSimulator, max_history: int = 200):
        self._sim        = simulator
        self._records    = []
        self._max_hist   = max_history
        self._listeners  = []   # SSE subscriber queues
        self._lock       = threading.Lock()
        self._server     = None
        self._frame_count = 0

    def record(self, frame: SimFrame):
        """
        Add a frame to the telemetry stream.
        Notifies all SSE subscribers.
        """
        self._frame_count += 1
        record = _frame_to_dict(frame, self._sim)

        with self._lock:
            self._records.append(record)
            if len(self._records) > self._max_hist:
                self._records.pop(0)
            # notify SSE subscribers
            for q in list(self._listeners):
                try:
                    q.put_nowait(record)
                except Exception:
                    pass

    # ── read-only properties ──────────────────────────────────────────────────

    @property
    def current_state(self) -> dict:
        """The most recent telemetry record, or empty dict."""
        with self._lock:
            return dict(self._records[-1]) if self._records else {}

    @property
    def safety_status(self) -> dict:
        """Current safety controller status + event log."""
        ctrl = self._sim.safety
        return {
            "state":      ctrl.state.value,
            "is_safe":    ctrl.is_safe,
            "event_count":len(ctrl.log),
            "events": [
                {
                    "triggered_at":   ev.triggered_at,
                    "state":          ev.state.value,
                    "trigger_source": ev.trigger_source,
                    "details":        ev.details,
                }
                for ev in ctrl.log
            ],
        }

    @property
    def history(self) -> list:
        """Copy of all telemetry records (read-only)."""
        with self._lock:
            return list(self._records)

    @property
    def frame_count(self) -> int:
        return self._frame_count

    # ── HTTP server ───────────────────────────────────────────────────────────

    def start_server(self, port: int = 5052, daemon: bool = True):
        """
        Start the telemetry HTTP server in a background thread.
        Returns the server object.
        """
        telem = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args): pass

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/telemetry/stream":
                    self._stream()
                elif path == "/telemetry/state":
                    self._json(telem.current_state)
                elif path == "/telemetry/safety":
                    self._json(telem.safety_status)
                elif path == "/telemetry/history":
                    self._json({"frames": telem.history})
                elif path == "/telemetry/status":
                    self._json({
                        "ok":          True,
                        "frame_count": telem.frame_count,
                        "history_len": len(telem.history),
                        "safety":      telem._sim.safety.state.value,
                    })
                else:
                    self._json({"error": "not found",
                                "endpoints": ["/telemetry/stream",
                                              "/telemetry/state",
                                              "/telemetry/safety",
                                              "/telemetry/history",
                                              "/telemetry/status"]}, 404)

            def _stream(self):
                import queue
                self.send_response(200)
                self.send_header("Content-Type",  "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection",    "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                q = queue.Queue(maxsize=100)
                with telem._lock:
                    telem._listeners.append(q)
                    for rec in list(telem._records)[-20:]:   # catch-up
                        q.put_nowait(rec)

                try:
                    while True:
                        try:
                            rec = q.get(timeout=2.0)
                            self.wfile.write(
                                f"data: {json.dumps(rec)}\n\n".encode()
                            )
                            self.wfile.flush()
                        except queue.Empty:
                            self.wfile.write(b": heartbeat\n\n")
                            self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    with telem._lock:
                        telem._listeners.remove(q)

            def _json(self, data: dict, code: int = 200):
                body = json.dumps(data, indent=2).encode()
                self.send_response(code)
                self.send_header("Content-Type",   "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

        server = HTTPServer(("0.0.0.0", port), Handler)
        self._server = server
        t = threading.Thread(target=server.serve_forever, daemon=daemon)
        t.start()

        print(f"eLo Robot Telemetry")
        print(f"  Stream  : http://localhost:{port}/telemetry/stream")
        print(f"  State   : http://localhost:{port}/telemetry/state")
        print(f"  Safety  : http://localhost:{port}/telemetry/safety")
        print(f"  History : http://localhost:{port}/telemetry/history")
        print(f"  Status  : http://localhost:{port}/telemetry/status")
        print()
        return server

    def stop_server(self):
        if self._server:
            self._server.shutdown()
            self._server = None
