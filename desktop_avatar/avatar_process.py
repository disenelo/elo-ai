"""
desktop_avatar/avatar_process.py — self-contained avatar subprocess.

Launched by main.py via subprocess.Popen when DESKTOP_AVATAR=1.
Runs tkinter on its own main thread — no threading conflict.

Communication: polls blender/blender_state.json every 100ms.
animation_router already writes that file on every conversation turn.

Standalone test:
    python -m desktop_avatar.avatar_process
"""

from __future__ import annotations
import sys
import os
import json
import time
import math
import tkinter as tk
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")
_POLL_MS    = 120   # state file poll interval

# ── constants ─────────────────────────────────────────────────────────────────

_WIN_W   = 80
_WIN_H   = 100
_PADDING = 20
_FRAME   = 33       # ~30fps draw interval

_CX      = _WIN_W // 2
_HEAD_R  = 16
_HEAD_CY = 32
_BODY_W  = 22
_BODY_H  = 28
_BODY_Y  = _HEAD_CY + _HEAD_R + 4
_LEG_W   = 6
_LEG_H   = 14

_COLOR_BODY  = "#7ED8F6"
_COLOR_MOUTH = "#2A6080"

_MOTIONS = ("idle", "sit", "walk", "float", "jump", "wave", "point", "look")

# translate motion_mapper names → visual names
_MOTION_MAP = {
    "breathe": "idle",
    "settle":  "sit",
    "pace":    "walk",
    "hop":     "jump",
    "wander":  "walk",
}


# ── welcome helpers ───────────────────────────────────────────────────────────

def _build_welcome() -> str:
    try:
        from memory import state_manager
        from core.continuity import cross_session_delta
        state   = state_manager.load()
        anchor  = state.get("session_anchor", {})
        summary = anchor.get("current_session_summary", "")
        if summary:
            msg = (summary
                   .replace("User explored ", "we were exploring ")
                   .replace(" with a neutral tone.", "")
                   .replace(" with a low-energy tone.", "")
                   .replace(" with a positive tone.", "")
                   .replace(" with a frustrated tone.", "")
                   .rstrip("."))
            delta = cross_session_delta(state)
            if delta:
                return f"Welcome back. Last time {msg}. {delta}"
            return f"Welcome back. Last time {msg}."
        if state.get("session_summaries"):
            return "Welcome back. Last time we were exploring how the robot and the book connect."
    except Exception:
        pass
    return "Welcome back."


# ── avatar window ─────────────────────────────────────────────────────────────

class AvatarWindow:

    def __init__(self):
        self._root   = tk.Tk()
        self._canvas: Optional[tk.Canvas] = None
        self._motion = "idle"
        self._speech = ""
        self._speech_until = 0.0
        self._tick   = 0.0
        self._last_state_mtime: float = 0.0

        self._setup()
        self._schedule_welcome()

    def _setup(self) -> None:
        r = self._root
        r.title("eLo")
        r.configure(bg="white")
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.92)
        r.overrideredirect(True)
        r.resizable(False, False)

        sw = r.winfo_screenwidth()
        sh = r.winfo_screenheight()
        x  = sw - _WIN_W - _PADDING
        y  = sh - _WIN_H - _PADDING - 40
        r.geometry(f"{_WIN_W}x{_WIN_H}+{x}+{y}")

        self._canvas = tk.Canvas(r, width=_WIN_W, height=_WIN_H,
                                  bg="white", highlightthickness=0)
        self._canvas.pack()

        r.after(_FRAME, self._draw_loop)
        r.after(_POLL_MS, self._poll_state)

    # ── welcome sequence ──────────────────────────────────────────────────────

    def _schedule_welcome(self) -> None:
        welcome = _build_welcome()

        def _look():    self._motion = "look"
        def _say():
            self._motion = "idle"
            self._speech = welcome[:40]
            self._speech_until = time.monotonic() + 5.0
        def _walk():    self._motion = "walk"
        def _settle():  self._motion = "idle"

        self._root.after(400,  _look)
        self._root.after(2400, _say)
        self._root.after(5600, _walk)
        self._root.after(8200, _settle)

    # ── state file polling ────────────────────────────────────────────────────

    def _poll_state(self) -> None:
        try:
            mtime = os.path.getmtime(_STATE_PATH)
            if mtime != self._last_state_mtime:
                self._last_state_mtime = mtime
                with open(_STATE_PATH) as f:
                    data = json.load(f)
                motion = data.get("motion", {})
                anim   = motion.get("animation", "idle")
                anim   = _MOTION_MAP.get(anim, anim)
                if anim in _MOTIONS:
                    self._motion = anim
        except Exception:
            pass
        self._root.after(_POLL_MS, self._poll_state)

    # ── draw loop ─────────────────────────────────────────────────────────────

    def _draw_loop(self) -> None:
        self._tick += _FRAME / 1000.0
        self._draw()
        self._root.after(_FRAME, self._draw_loop)

    def _draw(self) -> None:
        c  = self._canvas
        c.delete("all")
        dy = self._offset()

        # body
        c.create_rectangle(_CX - _BODY_W//2, _BODY_Y + dy,
                            _CX + _BODY_W//2, _BODY_Y + _BODY_H + dy,
                            fill=_COLOR_BODY, outline=_COLOR_BODY)
        # head
        c.create_oval(_CX - _HEAD_R, _HEAD_CY - _HEAD_R + dy,
                      _CX + _HEAD_R, _HEAD_CY + _HEAD_R + dy,
                      fill=_COLOR_BODY, outline=_COLOR_BODY)
        # mouth
        self._mouth(c, dy)
        # arms
        if self._motion == "wave":  self._wave_arm(c, dy)
        if self._motion == "point": self._point_arm(c, dy)
        # legs
        self._legs(c, dy)
        # speech bubble
        if self._speech and time.monotonic() < self._speech_until:
            self._speech_bubble(c, self._speech)

    def _offset(self) -> float:
        t = self._tick
        m = self._motion
        if m == "idle":   return math.sin(t * 0.8) * 1.5
        if m == "float":  return math.sin(t * 1.2) * 5.0
        if m == "jump":
            p = (t % 1.2) / 1.2
            return -abs(math.sin(p * math.pi)) * 18
        if m == "walk":   return math.sin(t * 3.0) * 2.0
        if m == "sit":    return 6.0
        return 0.0

    def _mouth(self, c: tk.Canvas, dy: float) -> None:
        mx, my = _CX, _HEAD_CY + 8 + dy
        if self._motion in ("jump", "wave"):
            c.create_arc(mx-7, my-4, mx+7, my+6, start=200, extent=140,
                         style=tk.CHORD, fill=_COLOR_MOUTH, outline=_COLOR_MOUTH)
        elif self._motion == "sit":
            c.create_line(mx-4, my+1, mx+4, my+1, fill=_COLOR_MOUTH, width=2)
        else:
            c.create_arc(mx-6, my-3, mx+6, my+5, start=200, extent=140,
                         style=tk.ARC, outline=_COLOR_MOUTH, width=2)

    def _legs(self, c: tk.Canvas, dy: float) -> None:
        top = _BODY_Y + _BODY_H + dy
        for sign in (-1, 1):
            lx = _CX + sign * 7
            if self._motion == "walk":
                swing = math.sin(self._tick * 3.0 + (0 if sign == -1 else math.pi)) * 4
                c.create_rectangle(lx - _LEG_W//2, top,
                                   lx + _LEG_W//2, top + _LEG_H + swing,
                                   fill=_COLOR_BODY, outline=_COLOR_BODY)
            else:
                c.create_rectangle(lx - _LEG_W//2, top,
                                   lx + _LEG_W//2, top + _LEG_H,
                                   fill=_COLOR_BODY, outline=_COLOR_BODY)

    def _wave_arm(self, c: tk.Canvas, dy: float) -> None:
        ax = _CX + _BODY_W//2
        ay = _BODY_Y + 6 + dy
        a  = math.sin(self._tick * 4.0) * 0.5
        c.create_line(ax, ay, ax + int(14*math.cos(a-0.8)), ay + int(14*math.sin(a-0.8)),
                      fill=_COLOR_BODY, width=5, capstyle=tk.ROUND)

    def _point_arm(self, c: tk.Canvas, dy: float) -> None:
        ax = _CX + _BODY_W//2
        ay = _BODY_Y + 6 + dy
        c.create_line(ax, ay, ax+16, ay-8, fill=_COLOR_BODY, width=5, capstyle=tk.ROUND)

    def _speech_bubble(self, c: tk.Canvas, text: str) -> None:
        c.create_rectangle(2, 2, _WIN_W-2, 22, fill="#F0FAFF", outline="#B0EEFF", width=1)
        c.create_text(_WIN_W//2, 12, text=text[:22], font=("Helvetica", 7),
                      fill="#2A6080", anchor="center", width=_WIN_W-8)

    def run(self) -> None:
        self._root.mainloop()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    AvatarWindow().run()
