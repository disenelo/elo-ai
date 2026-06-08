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
<html lang="en">
<head>
<meta charset="utf-8">
<title>eLo AI OS — Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Courier New',monospace;background:#0d0d0d;color:#c9c9c9;
     display:grid;grid-template-columns:1fr 320px;grid-template-rows:44px 1fr;
     height:100vh;overflow:hidden}

/* ── header ── */
header{grid-column:1/-1;background:#111;border-bottom:1px solid #222;
       display:flex;align-items:center;padding:0 16px;gap:16px}
header h1{color:#9cdcfe;font-size:.95em;font-weight:normal;letter-spacing:.08em}
#conn{font-size:.75em;padding:2px 8px;border-radius:3px;background:#1a2a1a;color:#4ec9b0}
#conn.err{background:#2a1a1a;color:#f44747}
#count{font-size:.75em;color:#555}

/* ── left: live feed ── */
#feed-col{overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:6px}
.card{border-left:3px solid #333;padding:8px 10px;background:#141414;border-radius:2px;
      font-size:.82em;transition:opacity .15s}
.card.new{animation:flash .4s ease}
@keyframes flash{0%{background:#1e1e1e}100%{background:#141414}}
.card.DIRECT          {border-color:#4ec9b0}
.card.GENTLE_GROUNDED {border-color:#ce9178}
.card.CREATIVE        {border-color:#c586c0}
.card.STRUCTURED      {border-color:#dcdcaa}
.card.CONVERSATIONAL  {border-color:#9cdcfe}
.card.SIMPLIFY        {border-color:#6a9955}
.card-top{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.badge{font-size:.72em;font-weight:bold;padding:1px 5px;border-radius:2px;background:#1e1e1e}
.badge.DIRECT          {color:#4ec9b0}
.badge.GENTLE_GROUNDED {color:#ce9178}
.badge.CREATIVE        {color:#c586c0}
.badge.STRUCTURED      {color:#dcdcaa}
.badge.CONVERSATIONAL  {color:#9cdcfe}
.badge.SIMPLIFY        {color:#6a9955}
.loop-tag{font-size:.7em;color:#f44747;background:#2a1111;padding:1px 5px;border-radius:2px}
.ts{font-size:.65em;color:#444;margin-left:auto}
.input-text{color:#d7ba7d;margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.reason-text{color:#555;font-size:.75em}

/* ── right: panels ── */
#right{border-left:1px solid #1e1e1e;display:flex;flex-direction:column;overflow:hidden}
.panel{padding:12px;border-bottom:1px solid #1a1a1a}
.panel h2{font-size:.72em;color:#444;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px}
.row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px;font-size:.8em}
.label{color:#555}
.val{color:#c9c9c9;text-align:right}
.val.hl{color:#9cdcfe}
.val.warn{color:#f44747}
.val.ok{color:#4ec9b0}

/* current state hero */
#hero-mode{font-size:1.4em;font-weight:bold;color:#9cdcfe;margin-bottom:6px}
#hero-input{font-size:.78em;color:#d7ba7d;overflow:hidden;
            text-overflow:ellipsis;white-space:nowrap;margin-bottom:4px}
#hero-reason{font-size:.7em;color:#555}

/* loop panel */
#loop-count{font-size:2em;font-weight:bold;color:#f44747}
#loop-none{font-size:.8em;color:#3a3a3a}
#loop-reason{font-size:.7em;color:#ce9178;margin-top:4px}
</style>
</head>
<body>

<header>
  <h1>eLo AI OS</h1>
  <span id="conn">CONNECTING</span>
  <span id="count">0 events</span>
</header>

<!-- live feed -->
<div id="feed-col"></div>

<!-- right panels -->
<div id="right">

  <div class="panel">
    <h2>Current Decision</h2>
    <div id="hero-mode">—</div>
    <div id="hero-input">waiting for input...</div>
    <div id="hero-reason"></div>
  </div>

  <div class="panel">
    <h2>State &amp; Emotion</h2>
    <div class="row"><span class="label">state</span>    <span class="val hl" id="v-state">—</span></div>
    <div class="row"><span class="label">emotion</span>  <span class="val" id="v-emotion">—</span></div>
    <div class="row"><span class="label">tone</span>     <span class="val" id="v-tone">—</span></div>
    <div class="row"><span class="label">pacing</span>   <span class="val" id="v-pacing">—</span></div>
    <div class="row"><span class="label">energy</span>   <span class="val" id="v-energy">—</span></div>
  </div>

  <div class="panel">
    <h2>Memory Influence</h2>
    <div class="row"><span class="label">tone signal</span> <span class="val" id="v-mtone">—</span></div>
    <div class="row"><span class="label">project</span>     <span class="val" id="v-project">—</span></div>
    <div class="row"><span class="label">confidence</span>  <span class="val" id="v-conf">—</span></div>
    <div class="row"><span class="label">drift</span>       <span class="val" id="v-drift">—</span></div>
    <div class="row"><span class="label">theme</span>       <span class="val" id="v-theme" style="font-size:.7em;max-width:180px;text-align:right;word-break:break-word">—</span></div>
  </div>

  <div class="panel" style="flex:1">
    <h2>Loop Status</h2>
    <div id="loop-count">0</div>
    <div id="loop-none">no loops detected</div>
    <div id="loop-reason"></div>
  </div>

</div>

<script>
let total = 0, loops = 0;
const feed  = document.getElementById('feed-col');
const conn  = document.getElementById('conn');
const cnt   = document.getElementById('count');

function $(id){ return document.getElementById(id) }
function set(id, val, cls){
  const el = $(id); el.textContent = val;
  if(cls){ el.className = 'val ' + cls }
}

function addCard(d){
  const ts = new Date(d.timestamp).toLocaleTimeString();
  const card = document.createElement('div');
  card.className = 'card new ' + d.mode;
  card.innerHTML =
    `<div class="card-top">
       <span class="badge ${d.mode}">${d.mode}</span>
       ${d.loop ? '<span class="loop-tag">⚠ LOOP</span>' : ''}
       <span class="ts">${ts}</span>
     </div>
     <div class="input-text">"${d.input}"</div>
     <div class="reason-text">${d.reason}</div>`;
  feed.prepend(card);
  if(feed.children.length > 80) feed.lastChild.remove();
}

function updatePanels(d){
  // hero
  $('hero-mode').textContent   = d.mode;
  $('hero-mode').style.color   = modeColor(d.mode);
  $('hero-input').textContent  = '"' + d.input + '"';
  $('hero-reason').textContent = d.reason;

  // state + emotion
  const st = d.state_snapshot, em = d.emotion_snapshot;
  set('v-state',   st.name,   'hl');
  set('v-emotion', em.emotion);
  set('v-tone',    em.tone);
  set('v-pacing',  st.pacing_bias);
  set('v-energy',  (st.weight * 100).toFixed(0) + '%');

  // memory
  const mem = d.memory_snapshot;
  set('v-mtone',   mem.tone || '—');
  set('v-project', mem.project || '—');
  set('v-conf',    mem.confidence != null ? (mem.confidence * 100).toFixed(0) + '%' : '—');
  const driftEl = $('v-drift');
  driftEl.textContent = mem.drift ? 'YES' : 'no';
  driftEl.className   = 'val ' + (mem.drift ? 'warn' : 'ok');
  set('v-theme',   mem.returning_theme || '—');

  // loop
  if(d.loop){
    loops++;
    $('loop-count').textContent = loops;
    $('loop-none').style.display  = 'none';
    $('loop-reason').textContent  = d.loop_reason || 'mode stagnation';
  }
}

function modeColor(m){
  return {DIRECT:'#4ec9b0',GENTLE_GROUNDED:'#ce9178',CREATIVE:'#c586c0',
          STRUCTURED:'#dcdcaa',CONVERSATIONAL:'#9cdcfe',SIMPLIFY:'#6a9955'}[m] || '#888';
}

const es = new EventSource('/stream');
es.onopen = () => { conn.textContent = 'LIVE'; conn.className = '' };
es.onmessage = e => {
  const d = JSON.parse(e.data);
  total++;
  cnt.textContent = total + ' event' + (total === 1 ? '' : 's');
  addCard(d);
  updatePanels(d);
};
es.onerror = () => { conn.textContent = 'DISCONNECTED'; conn.className = 'err' };
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
