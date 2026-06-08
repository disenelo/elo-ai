"""
dashboard/unity_bridge_server.py — eLo AI real-time Unity bridge.

Subscribes to the kernel event bus and:
    1. Writes avatar_signal.json on every decision (Unity file-polling path)
    2. Serves /unity/stream  — SSE for Unity's NetworkStream client
    3. Serves /unity/latest  — last signal as JSON (HTTP polling fallback)

Does NOT modify kernel, engines, or dashboard/server.py.
Reads from dashboard/event_bus.py (shared event queue).

Usage:
    # start the main dashboard server first (populates the event bus):
    python dashboard/server.py &

    # then start the Unity bridge:
    python dashboard/unity_bridge_server.py
    python dashboard/unity_bridge_server.py --port 5051 --signal-file avatar/avatar_signal.json

Unity integration options:
    A — File polling (simplest, already supported by EloSignalReceiver.cs):
        The bridge writes avatar/avatar_signal.json on every event.
        Unity polls the file at a configurable interval.

    B — SSE stream (lower latency):
        Unity reads GET http://localhost:5051/unity/stream
        Receives one JSON event per line, prefixed with "data: ".

    C — HTTP polling fallback:
        Unity polls GET http://localhost:5051/unity/latest
        Receives the most recent signal as plain JSON.

Mapping applied (avatar/unity_signal.py):
    emotion → emotion_blend   (float 0.0-1.0 for blend tree)
    state   → locomotion_state (int for Animator state machine)
    energy  → animation_speed  (float multiplier)
"""

import json
import os
import sys
import time
import argparse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.event_bus  import subscribe, recent
from dashboard.observer   import install
from avatar.unity_signal  import to_unity_signal


# ── Unity signal builder ───────────────────────────────────────────────────────

# emotion → Animator blend tree value (0.0 = baseline, 1.0 = full expression)
_EMOTION_BLEND: dict = {
    "curious":    0.70,
    "excited":    1.00,
    "calm":       0.30,
    "focused":    0.50,
    "playful":    0.85,
    "distressed": 0.10,
    "gentle":     0.25,
    "idle":       0.00,
    "neutral":    0.00,
}

# state → Animator integer parameter (maps to locomotion state machine)
_LOCOMOTION_STATE: dict = {
    "resting":   0,
    "focused":   1,
    "exploring": 2,
    "building":  3,
    "reflecting":4,
    "playful":   5,
}

# energy (0.0-1.0) → Animator speed multiplier
# range: 0.3 (resting) to 1.7 (excited)
def _energy_to_speed(energy: float) -> float:
    return round(0.3 + float(energy) * 1.4, 2)


def build_unity_signal(event: dict) -> dict:
    """
    Convert a dashboard event dict into a Unity-ready signal.

    Input:  event from dashboard/event_bus.py (kernel decision cycle)
    Output: Unity animation parameter dict

    No AI logic. No routing. Pure field mapping.
    """
    st  = event.get("state_snapshot",  {})
    em  = event.get("emotion_snapshot",{})
    cls = event.get("classification",  {})

    state_name   = st.get("name",    "exploring")
    emotion_name = em.get("emotion", "neutral")
    energy       = float(st.get("weight", 0.5))

    # run through avatar/unity_signal mapping
    base = to_unity_signal(
        mode          = event.get("mode", "CONVERSATIONAL"),
        state_name    = state_name,
        emotion       = emotion_name,
        intent        = event.get("identity_snapshot", {}).get("intent", ""),
        energy        = energy,
        loop_detected = event.get("loop", False),
    )

    return {
        "timestamp":        event.get("timestamp", ""),
        # core fields (exact required structure)
        "state":            base["state"],
        "emotion":          base["emotion"],
        "intent":           base["intent"],
        "energy":           base["energy"],
        "motion_hint":      base["motion_hint"],
        # Unity Animator parameters (derived from mapping)
        "emotion_blend":    _EMOTION_BLEND.get(base["emotion"], 0.0),
        "locomotion_state": _LOCOMOTION_STATE.get(base["state"], 2),
        "animation_speed":  _energy_to_speed(energy),
        # context
        "loop_detected":    event.get("loop", False),
        "mode":             event.get("mode", ""),
        "input":            event.get("input", ""),
    }


# ── file writer ────────────────────────────────────────────────────────────────

_latest_signal: dict = {}


def _write_signal_file(signal: dict, path: str):
    """Write the Unity signal to disk. Called on every kernel event."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(signal, f, indent=2)


# ── SSE handler ────────────────────────────────────────────────────────────────

class UnityBridgeHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/unity/stream":
            self._handle_stream()
        elif path == "/unity/latest":
            self._handle_latest()
        elif path == "/unity/status":
            self._handle_status()
        else:
            self._send(404, "application/json",
                       json.dumps({"error": "not found",
                                   "endpoints": ["/unity/stream", "/unity/latest", "/unity/status"]}))

    def _handle_stream(self):
        """SSE endpoint — Unity reads this for low-latency real-time updates."""
        self.send_response(200)
        self.send_header("Content-Type",  "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection",    "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # send most recent signal immediately on connect (page catch-up)
        if _latest_signal:
            try:
                line = f"data: {json.dumps(_latest_signal)}\n\n".encode()
                self.wfile.write(line)
                self.wfile.flush()
            except BrokenPipeError:
                return

        for event in subscribe(timeout=2.0):
            try:
                if event is None:
                    self.wfile.write(b": heartbeat\n\n")
                else:
                    signal = build_unity_signal(event)
                    self.wfile.write(f"data: {json.dumps(signal)}\n\n".encode())
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return

    def _handle_latest(self):
        """HTTP polling endpoint — returns most recent signal as JSON."""
        body = json.dumps(_latest_signal or {"error": "no signal yet"}, indent=2)
        self._send(200, "application/json", body)

    def _handle_status(self):
        status = {
            "ok":            True,
            "has_signal":    bool(_latest_signal),
            "current_mode":  _latest_signal.get("mode", ""),
            "current_state": _latest_signal.get("state", ""),
        }
        self._send(200, "application/json", json.dumps(status))

    def _send(self, code, content_type, body):
        enc = body.encode()
        self.send_response(code)
        self.send_header("Content-Type",   content_type)
        self.send_header("Content-Length", str(len(enc)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(enc)


# ── background event pump ──────────────────────────────────────────────────────

def _pump_events(signal_file: str):
    """
    Background thread — reads events from the bus, converts to Unity signals,
    writes to disk, and updates _latest_signal for HTTP polling.
    """
    global _latest_signal
    for event in subscribe(timeout=1.0):
        if event is None:
            continue
        signal = build_unity_signal(event)
        _latest_signal = signal
        try:
            _write_signal_file(signal, signal_file)
        except OSError:
            pass   # disk write failure is non-fatal


# ── entry point ────────────────────────────────────────────────────────────────

def run(port: int = 5051, signal_file: str = "avatar/avatar_signal.json"):
    """
    Start the Unity bridge server.

    Installs the kernel observer (no kernel source changes), then:
        - pumps events to signal_file (real-time file polling for Unity)
        - serves /unity/stream for SSE (low-latency streaming)
        - serves /unity/latest for HTTP polling (fallback)
    """
    install()   # hook into kernel — no kernel source modified

    pump = threading.Thread(target=_pump_events, args=(signal_file,), daemon=True)
    pump.start()

    server = HTTPServer(("0.0.0.0", port), UnityBridgeHandler)

    print("eLo AI — Unity Bridge")
    print(f"  SSE stream : http://localhost:{port}/unity/stream")
    print(f"  Latest     : http://localhost:{port}/unity/latest")
    print(f"  Status     : http://localhost:{port}/unity/status")
    print(f"  Signal file: {os.path.abspath(signal_file)}")
    print()
    print("Unity integration:")
    print("  Option A (file polling):  point EloSignalReceiver.cs at the signal file")
    print("  Option B (SSE):           read http://localhost:{port}/unity/stream")
    print("  Option C (HTTP polling):  poll http://localhost:{port}/unity/latest")
    print()
    print("No kernel source files modified. Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nUnity bridge stopped.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eLo AI Unity Bridge Server")
    parser.add_argument("--port",        type=int, default=5051)
    parser.add_argument("--signal-file", default="avatar/avatar_signal.json")
    args = parser.parse_args()
    run(args.port, args.signal_file)
