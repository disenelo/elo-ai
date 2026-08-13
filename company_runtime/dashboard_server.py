"""
company_runtime/dashboard_server.py — serve the live CEO dashboard + handle real approvals.

A standalone HTML file in a browser can't write to disk, so "Approve" can't do anything.
This tiny stdlib server bridges that: it serves the dashboard, serves fresh company_state.json,
and accepts approve/action POSTs → routes them through the SAME company_runtime pipeline
(process_action → L3 + safety gate → flips the board WO → re-emits state). Observer→Executive
(EA-3 §7): the browser REQUESTS, the server (Executive stand-in) acts.

Run:  python -m company_runtime.dashboard_server         # http://localhost:8770
      python -m company_runtime.dashboard_server 9000    # custom port
"""
from __future__ import annotations
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from company_runtime import company_state_writer as csw

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE = os.path.join(_ROOT, "blender", "company_state.json")
# dashboard HTML lives in the user's Output folder (the prototype we built)
_HTML_CANDIDATES = [
    os.path.expanduser("~/Desktop/Output/DISENELO_Presence_Dashboard.html"),
    os.path.join(_ROOT, "dashboard", "DISENELO_Presence_Dashboard.html"),
]


def _html_path():
    for p in _HTML_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self._send(204, "")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            p = _html_path()
            if not p:
                return self._send(404, "dashboard HTML not found", "text/plain")
            with open(p, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if self.path.startswith("/company_state.json") or self.path.startswith("/state"):
            csw.publish()  # regenerate from the live board every fetch → always current
            with open(_STATE, "rb") as f:
                return self._send(200, f.read())
        return self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path not in ("/action", "/approve"):
            return self._send(404, "not found", "text/plain")
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            action = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, json.dumps({"ok": False, "reason": "bad JSON"}))
        if self.path == "/approve" and "type" not in action:
            action["type"] = "approval_request"
        action.setdefault("actor", "David")   # this dashboard IS David's L3 surface
        result = csw.process_action(action)   # same pipeline: L3 + safety gate → flip → re-emit
        return self._send(200, json.dumps(result))

    def log_message(self, *a):  # quiet
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    csw.publish()  # prime the state file
    # continuation loop: on board change, run tests + auto-close 🟢 AUTO greens (David's policy)
    if os.environ.get("DISENELO_NO_AUTOLOOP") != "1":
        try:
            from company_runtime import continuation
            continuation.start_thread(interval=5.0)
            print("  continuation loop: ON — auto-closes AUTO greens on board change (DISENELO_NO_AUTOLOOP=1 to disable)")
        except Exception as exc:
            print(f"  continuation loop: OFF ({exc})")
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"DISENELO CEO Dashboard  →  http://localhost:{port}")
    print(f"  serving: {_html_path()}")
    print("  approvals write through company_runtime (L3 + safety gate). Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
