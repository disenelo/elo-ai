"""
dashboard/server.py — eLo AI real-time dashboard backend.

Endpoints:
    GET /stream          Server-Sent Events — live kernel decision cycles
    GET /events          Last N events as JSON array (for initial page load)
    GET /status          Server health + event count
    GET /                Minimal HTML dashboard (browser-viewable)

Usage:
    python dashboard/server.py            # default port 5050
    python dashboard/server.py --port 8080

No external dependencies. Pure stdlib.
Does NOT modify kernel or engines.
"""

import json
import sys
import os
import threading
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.observer  import install
from dashboard.event_bus import subscribe, recent, to_sse


# ── SSE / HTTP handler ─────────────────────────────────────────────────────────

class DashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass   # silence default request logging

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/stream":
            self._handle_stream()
        elif path == "/events":
            self._handle_events()
        elif path == "/status":
            self._handle_status()
        elif path in ("/", "/index.html"):
            self._handle_html()
        else:
            self._send(404, "application/json", json.dumps({"error": "not found"}))

    # ── /stream — SSE live feed ────────────────────────────────────────────────

    def _handle_stream(self):
        self.send_response(200)
        self.send_header("Content-Type",  "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection",    "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # send all recent events immediately (page catch-up)
        for event in recent(20):
            try:
                self.wfile.write(to_sse(event).encode())
                self.wfile.flush()
            except BrokenPipeError:
                return

        # then stream new events as they arrive
        for event in subscribe(timeout=2.0):
            try:
                if event is None:
                    # heartbeat — keep connection alive
                    self.wfile.write(b": heartbeat\n\n")
                else:
                    self.wfile.write(to_sse(event).encode())
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return

    # ── /events — last N as JSON ───────────────────────────────────────────────

    def _handle_events(self):
        events = recent(50)
        self._send(200, "application/json", json.dumps(events, indent=2))

    # ── /status — health check ─────────────────────────────────────────────────

    def _handle_status(self):
        status = {
            "ok":          True,
            "event_count": len(recent(100)),
            "observer":    "DashboardObserver",
        }
        self._send(200, "application/json", json.dumps(status))

    # ── / — minimal HTML dashboard ─────────────────────────────────────────────

    def _handle_html(self):
        html = _DASHBOARD_HTML
        self._send(200, "text/html", html)

    def _send(self, code: int, content_type: str, body: str):
        encoded = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)


# ── minimal dashboard HTML ─────────────────────────────────────────────────────

_DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>eLo AI — Decision Dashboard</title>
<style>
  body { font-family: monospace; background: #0f0f0f; color: #d4d4d4; margin: 0; padding: 16px; }
  h1 { color: #9cdcfe; font-size: 1.1em; }
  #feed { max-height: 85vh; overflow-y: auto; }
  .event { border-left: 3px solid #444; padding: 8px 12px; margin: 6px 0; background: #1a1a1a; }
  .event.DIRECT          { border-color: #4ec9b0; }
  .event.GENTLE_GROUNDED { border-color: #ce9178; }
  .event.CREATIVE        { border-color: #c586c0; }
  .event.STRUCTURED      { border-color: #dcdcaa; }
  .event.CONVERSATIONAL  { border-color: #9cdcfe; }
  .event.SIMPLIFY        { border-color: #6a9955; }
  .mode  { font-weight: bold; font-size: 0.85em; }
  .input { color: #d7ba7d; margin: 2px 0; }
  .reason { color: #888; font-size: 0.8em; }
  .snaps { font-size: 0.75em; color: #666; margin-top: 4px; }
  .loop  { color: #f44747; font-size: 0.8em; }
</style>
</head>
<body>
<h1>eLo AI — Decision Stream</h1>
<div id="feed"></div>
<script>
const feed = document.getElementById('feed');
const es   = new EventSource('/stream');
es.onmessage = e => {
  const d = JSON.parse(e.data);
  const div = document.createElement('div');
  div.className = 'event ' + d.mode;
  div.innerHTML = `
    <span class="mode">[${d.mode}]</span>
    ${d.loop ? '<span class="loop"> ⚠ loop</span>' : ''}
    <div class="input">"${d.input}"</div>
    <div class="reason">${d.reason}</div>
    <div class="snaps">
      mem:tone=${d.memory_snapshot.tone}
      state:${d.state_snapshot.name}
      emotion:${d.emotion_snapshot.emotion}
      energy=${d.state_snapshot.weight}
    </div>`;
  feed.prepend(div);
  if (feed.children.length > 100) feed.lastChild.remove();
};
es.onerror = () => { console.log('stream disconnected'); };
</script>
</body>
</html>"""


# ── server runner ──────────────────────────────────────────────────────────────

def run(port: int = 5050):
    """
    Start the dashboard server.

    1. Installs the kernel observer (no kernel source changes)
    2. Starts HTTP server on the given port
    3. Streams events at /stream
    """
    install()   # hook into kernel via DashboardObserver

    server = HTTPServer(("0.0.0.0", port), DashboardHandler)

    print(f"eLo AI Dashboard")
    print(f"  Stream :  http://localhost:{port}/stream")
    print(f"  Events :  http://localhost:{port}/events")
    print(f"  Status :  http://localhost:{port}/status")
    print(f"  Browser:  http://localhost:{port}/")
    print()
    print("Observing kernel decisions. Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eLo AI Dashboard Backend")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    run(args.port)
