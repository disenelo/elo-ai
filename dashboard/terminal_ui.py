"""
dashboard/terminal_ui.py — eLo AI OS terminal dashboard.

Reads the SSE stream from dashboard/server.py and renders a live
terminal view. No external dependencies beyond Python stdlib.

Usage:
    # start the server first
    python dashboard/server.py &

    # then run the terminal UI
    python dashboard/terminal_ui.py
    python dashboard/terminal_ui.py --url http://localhost:5050

Display:
    ┌─ header bar (mode, state, emotion, energy) ─────────────┐
    │ live decision feed (most recent at top)                  │
    │ memory influence + loop status (right column)            │
    └──────────────────────────────────────────────────────────┘
"""

import sys
import os
import json
import time
import shutil
import argparse
import urllib.request
from collections import deque

# ── ANSI codes ─────────────────────────────────────────────────────────────────

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_CLEAR  = "\033[2J\033[H"          # clear screen + move to top-left
_EL     = "\033[K"                 # erase to end of line

def _c(r, g, b):  return f"\033[38;2;{r};{g};{b}m"
def _bg(r, g, b): return f"\033[48;2;{r};{g};{b}m"

_TEAL    = _c(78,  201, 176)
_ORANGE  = _c(206, 145, 120)
_PURPLE  = _c(197, 134, 192)
_YELLOW  = _c(220, 220, 170)
_BLUE    = _c(156, 220, 254)
_GREEN   = _c(106, 153, 85)
_RED     = _c(244,  71,  71)
_GREY    = _c(100, 100, 100)
_WHITE   = _c(201, 201, 201)
_GOLD    = _c(215, 186, 125)

_MODE_COLORS = {
    "DIRECT":          _TEAL,
    "GENTLE_GROUNDED": _ORANGE,
    "CREATIVE":        _PURPLE,
    "STRUCTURED":      _YELLOW,
    "CONVERSATIONAL":  _BLUE,
    "SIMPLIFY":        _GREEN,
}


# ── state ──────────────────────────────────────────────────────────────────────

class DashState:
    def __init__(self, history: int = 12):
        self.events:   deque = deque(maxlen=history)
        self.current:  dict  = {}
        self.loops:    int   = 0
        self.total:    int   = 0
        self.connected: bool = False

    def ingest(self, event: dict):
        self.events.appendleft(event)
        self.current = event
        self.total  += 1
        if event.get("loop"):
            self.loops += 1


# ── render ─────────────────────────────────────────────────────────────────────

def _term_width() -> int:
    return shutil.get_terminal_size((120, 40)).columns

def _pad(s: str, n: int) -> str:
    """Pad/truncate string to exactly n visible chars (ignores ANSI codes)."""
    import re
    plain = re.sub(r"\033\[[0-9;]*m", "", s)
    if len(plain) >= n:
        return s[:n - len(plain) + len(s)]
    return s + " " * (n - len(plain))

def _bar(val: float, width: int = 10) -> str:
    filled = int(val * width)
    return _TEAL + "█" * filled + _DIM + "░" * (width - filled) + _RESET

def mode_color(mode: str) -> str:
    return _MODE_COLORS.get(mode, _GREY)


def render(state: DashState):
    W = _term_width()
    lines = []

    def L(s=""):
        lines.append((s + _EL)[:W + 50])   # extra for ANSI codes

    # ── header ──
    L(_bg(17, 17, 17) + _BOLD + _BLUE +
      f" eLo AI OS " + _RESET + _bg(17, 17, 17) +
      _DIM + " dashboard " + _RESET +
      (_TEAL + " ● LIVE " if state.connected else _RED + " ○ WAIT ") + _RESET +
      _GREY + f" {state.total} events  loops:{state.loops} " + _RESET)
    L(_GREY + "─" * W + _RESET)

    # ── current decision ──
    cur = state.current
    if cur:
        mode = cur.get("mode", "—")
        mc   = mode_color(mode)
        loop_tag = f" {_RED}⚠ LOOP{_RESET}" if cur.get("loop") else ""
        L(f" {mc}{_BOLD}[{mode}]{_RESET}{loop_tag}  "
          f"{_GOLD}\"{cur.get('input','')[:W-30]}\"{_RESET}")
        L(f"  {_GREY}{cur.get('reason','')[:W-4]}{_RESET}")
    else:
        L(f" {_GREY}waiting for first event...{_RESET}")

    L(_GREY + "─" * W + _RESET)

    # ── two-column body ──
    RIGHT_W = 36
    FEED_W  = W - RIGHT_W - 3

    # collect right column lines
    right = []
    if cur:
        st  = cur.get("state_snapshot",  {})
        em  = cur.get("emotion_snapshot",{})
        mem = cur.get("memory_snapshot", {})

        right.append(f"{_GREY}STATE & EMOTION{_RESET}")
        right.append(f" state   {_BLUE}{st.get('name','—')}{_RESET}")
        right.append(f" emotion {_WHITE}{em.get('emotion','—')}{_RESET}")
        right.append(f" pacing  {_GREY}{st.get('pacing_bias','—')}{_RESET}")
        energy = st.get('weight', 0)
        right.append(f" energy  {_bar(energy, 8)} {_GREY}{energy:.0%}{_RESET}")
        right.append("")
        right.append(f"{_GREY}MEMORY{_RESET}")
        right.append(f" tone    {_WHITE}{mem.get('tone','—')}{_RESET}")
        right.append(f" project {_GOLD}{mem.get('project','—')}{_RESET}")
        conf  = mem.get("confidence")
        drift = mem.get("drift", False)
        right.append(f" conf    {_TEAL if conf and conf > 0.7 else _ORANGE}{(conf*100):.0f}%{_RESET}" if conf is not None else f" conf    {_GREY}—{_RESET}")
        right.append(f" drift   {_RED}YES{_RESET}" if drift else f" drift   {_GREEN}no{_RESET}")
        theme = mem.get("returning_theme","")
        right.append("")
        right.append(f"{_GREY}LOOP STATUS{_RESET}")
        right.append(f" total  {_RED if state.loops else _GREY}{state.loops}{_RESET}")
        if state.loops and cur.get("loop_reason"):
            right.append(f" {_GREY}{cur['loop_reason'][:RIGHT_W-2]}{_RESET}")

    # feed events
    feed_lines = []
    for ev in state.events:
        mc   = mode_color(ev.get("mode",""))
        loop = f" {_RED}⚠{_RESET}" if ev.get("loop") else ""
        ts   = ev.get("timestamp","")[-8:-1]   # HH:MM:SS
        mode = ev.get("mode","?")[:10]
        inp  = ev.get("input","")[:FEED_W - 22]
        feed_lines.append(
            f" {_GREY}{ts}{_RESET} {mc}{mode:<10}{_RESET}{loop} "
            f"{_GOLD}\"{inp}\"{_RESET}"
        )

    # merge columns
    max_rows = max(len(feed_lines), len(right))
    for i in range(max_rows):
        fl = feed_lines[i] if i < len(feed_lines) else ""
        rl = right[i]      if i < len(right)       else ""
        # pad feed column
        padded_feed = _pad(fl, FEED_W)
        L(f"{padded_feed}  {_GREY}│{_RESET} {rl}")

    L(_GREY + "─" * W + _RESET)
    L(_GREY + " Ctrl+C to quit  │  browser: http://localhost:5050/" + _RESET)

    sys.stdout.write(_CLEAR)
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


# ── SSE reader ─────────────────────────────────────────────────────────────────

def stream_events(url: str, state: DashState, on_event):
    """Read SSE stream from url, call on_event(dict) for each event."""
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            state.connected = True
            buf = ""
            while True:
                chunk = resp.read(1).decode("utf-8", errors="replace")
                if not chunk:
                    break
                buf += chunk
                if buf.endswith("\n\n"):
                    for line in buf.strip().splitlines():
                        if line.startswith("data: "):
                            try:
                                event = json.loads(line[6:])
                                on_event(event)
                            except json.JSONDecodeError:
                                pass
                    buf = ""
    except Exception as exc:
        state.connected = False
        raise exc


# ── entry point ────────────────────────────────────────────────────────────────

def run(url: str = "http://localhost:5050/stream"):
    state = DashState(history=15)

    def on_event(event: dict):
        state.ingest(event)
        render(state)

    render(state)   # initial empty frame

    while True:
        try:
            stream_events(url, state, on_event)
        except KeyboardInterrupt:
            sys.stdout.write("\033[?25h")   # restore cursor
            print("\nDashboard closed.")
            break
        except Exception:
            state.connected = False
            render(state)
            time.sleep(2)   # retry after pause


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eLo AI Terminal Dashboard")
    parser.add_argument("--url", default="http://localhost:5050/stream",
                        help="SSE stream URL (default: http://localhost:5050/stream)")
    args = parser.parse_args()

    try:
        sys.stdout.write("\033[?25l")   # hide cursor
        run(args.url)
    finally:
        sys.stdout.write("\033[?25h")   # restore cursor on exit
