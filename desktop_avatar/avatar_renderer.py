"""
desktop_avatar/avatar_renderer.py — eLo desktop avatar renderer.

Phase F — DESKTOP → AVATAR.

Renders eLo as a small tkinter window on the desktop.
No eyes. Expression in body shape + movement.

Abilities: sit  walk  float  jump  wave  point  look  idle

Rules:
    - No interruptions
    - Presence > notifications
    - Movement is slow and deliberate
    - eLo stays in a corner unless responding to context

Run standalone:
    python -m desktop_avatar.avatar_renderer
"""

from __future__ import annotations
import tkinter as tk
import threading
import time
import math
import random
from typing import Optional

# ── constants ─────────────────────────────────────────────────────────────────

_WIN_W   = 80
_WIN_H   = 100
_PADDING = 20      # distance from screen edge
_FPS     = 30
_DT      = 1.0 / _FPS

_CORNER = "bottom-right"   # where eLo rests

# ── eLo body proportions (canvas units) ──────────────────────────────────────

_CX = _WIN_W // 2    # center x
_HEAD_R  = 16        # head radius
_HEAD_CY = 32        # head center y
_BODY_W  = 22        # body width
_BODY_H  = 28        # body height
_BODY_Y  = _HEAD_CY + _HEAD_R + 4
_LEG_W   = 6
_LEG_H   = 14

# colours
_COLOR_BODY  = "#7ED8F6"   # eLo light blue
_COLOR_MOUTH = "#2A6080"   # dark for mouth only — no eyes
_COLOR_GLOW  = "#B0EEFF"   # glow tint

# ── motion states ─────────────────────────────────────────────────────────────

_MOTIONS = ("idle", "sit", "walk", "float", "jump", "wave", "point", "look")


class AvatarRenderer:
    """
    eLo desktop avatar — persistent tkinter window.

    Usage:
        renderer = AvatarRenderer()
        renderer.start()        # non-blocking, runs in background thread
        renderer.set_motion("walk")
        renderer.say("Welcome back.")
        renderer.stop()
    """

    def __init__(self):
        self._root:    Optional[tk.Tk]    = None
        self._canvas:  Optional[tk.Canvas] = None
        self._running: bool = False
        self._motion:  str  = "idle"
        self._speech:  str  = ""
        self._speech_until: float = 0.0
        self._tick:    float = 0.0
        self._offset_y: float = 0.0   # for float/bounce
        self._thread:  Optional[threading.Thread] = None

    # ── public API ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Launch the avatar window in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def set_motion(self, motion: str) -> None:
        if motion in _MOTIONS:
            self._motion = motion

    def say(self, text: str, duration: float = 4.0) -> None:
        """Display a speech bubble for `duration` seconds."""
        self._speech       = text
        self._speech_until = time.monotonic() + duration

    def walk_to_corner(self) -> None:
        self.set_motion("walk")
        threading.Timer(2.5, lambda: self.set_motion("idle")).start()

    def look_around(self) -> None:
        self.set_motion("look")
        threading.Timer(2.0, lambda: self.set_motion("idle")).start()

    # ── window setup ──────────────────────────────────────────────────────────

    def _run(self) -> None:
        self._root = tk.Tk()
        self._root.title("eLo")
        self._root.geometry(f"{_WIN_W}x{_WIN_H}")
        self._root.configure(bg="white")
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.92)
        self._root.overrideredirect(True)   # no title bar
        self._root.resizable(False, False)

        # position in corner
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x  = sw - _WIN_W  - _PADDING
        y  = sh - _WIN_H  - _PADDING - 40   # 40 for dock
        self._root.geometry(f"+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root, width=_WIN_W, height=_WIN_H,
            bg="white", highlightthickness=0
        )
        self._canvas.pack()

        self._root.after(0, self._loop)
        self._root.mainloop()

    def _loop(self) -> None:
        if not self._running:
            self._root.destroy()
            return

        self._tick += _DT
        self._draw()
        self._root.after(int(_DT * 1000), self._loop)

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        c = self._canvas
        c.delete("all")

        # motion offset
        dy = self._motion_offset()

        # body
        bx1 = _CX - _BODY_W // 2
        bx2 = _CX + _BODY_W // 2
        by1 = _BODY_Y + dy
        by2 = _BODY_Y + _BODY_H + dy
        c.create_rectangle(bx1, by1, bx2, by2,
                            fill=_COLOR_BODY, outline=_COLOR_BODY, width=0)

        # head (circle — no eyes)
        hx1 = _CX - _HEAD_R
        hx2 = _CX + _HEAD_R
        hy1 = _HEAD_CY - _HEAD_R + dy
        hy2 = _HEAD_CY + _HEAD_R + dy
        c.create_oval(hx1, hy1, hx2, hy2,
                      fill=_COLOR_BODY, outline=_COLOR_BODY, width=0)

        # mouth — changes with motion
        self._draw_mouth(c, dy)

        # arms (wave / point)
        if self._motion == "wave":
            self._draw_wave_arm(c, dy)
        elif self._motion == "point":
            self._draw_point_arm(c, dy)

        # legs
        self._draw_legs(c, dy)

        # speech bubble
        if self._speech and time.monotonic() < self._speech_until:
            self._draw_speech(c, self._speech)

    def _motion_offset(self) -> float:
        t = self._tick
        if self._motion == "idle":
            return math.sin(t * 0.8) * 1.5
        if self._motion == "float":
            return math.sin(t * 1.2) * 5.0
        if self._motion == "jump":
            phase = (t % 1.2) / 1.2
            return -abs(math.sin(phase * math.pi)) * 18
        if self._motion == "walk":
            return math.sin(t * 3.0) * 2.0
        if self._motion == "sit":
            return 6.0
        return 0.0

    def _draw_mouth(self, c: tk.Canvas, dy: float) -> None:
        mx = _CX
        my = _HEAD_CY + 8 + dy
        if self._motion in ("idle", "float", "look"):
            # small smile
            c.create_arc(mx - 6, my - 3, mx + 6, my + 5,
                         start=200, extent=140,
                         style=tk.ARC, outline=_COLOR_MOUTH, width=2)
        elif self._motion in ("jump", "wave"):
            # open happy mouth
            c.create_arc(mx - 7, my - 4, mx + 7, my + 6,
                         start=200, extent=140,
                         style=tk.CHORD, fill=_COLOR_MOUTH, outline=_COLOR_MOUTH)
        elif self._motion == "sit":
            # small relaxed line
            c.create_line(mx - 4, my + 1, mx + 4, my + 1,
                          fill=_COLOR_MOUTH, width=2)
        else:
            c.create_arc(mx - 5, my - 2, mx + 5, my + 4,
                         start=200, extent=140,
                         style=tk.ARC, outline=_COLOR_MOUTH, width=2)

    def _draw_legs(self, c: tk.Canvas, dy: float) -> None:
        leg_top = _BODY_Y + _BODY_H + dy
        # left leg
        lx = _CX - 7
        if self._motion == "walk":
            swing = math.sin(self._tick * 3.0) * 4
            c.create_rectangle(lx - _LEG_W//2, leg_top,
                                lx + _LEG_W//2, leg_top + _LEG_H + swing,
                                fill=_COLOR_BODY, outline=_COLOR_BODY)
        else:
            c.create_rectangle(lx - _LEG_W//2, leg_top,
                                lx + _LEG_W//2, leg_top + _LEG_H,
                                fill=_COLOR_BODY, outline=_COLOR_BODY)
        # right leg
        rx = _CX + 7
        if self._motion == "walk":
            swing = math.sin(self._tick * 3.0 + math.pi) * 4
            c.create_rectangle(rx - _LEG_W//2, leg_top,
                                rx + _LEG_W//2, leg_top + _LEG_H + swing,
                                fill=_COLOR_BODY, outline=_COLOR_BODY)
        else:
            c.create_rectangle(rx - _LEG_W//2, leg_top,
                                rx + _LEG_W//2, leg_top + _LEG_H,
                                fill=_COLOR_BODY, outline=_COLOR_BODY)

    def _draw_wave_arm(self, c: tk.Canvas, dy: float) -> None:
        ax = _CX + _BODY_W // 2
        ay = _BODY_Y + 6 + dy
        angle = math.sin(self._tick * 4.0) * 0.5
        ex = ax + int(14 * math.cos(angle - 0.8))
        ey = ay + int(14 * math.sin(angle - 0.8))
        c.create_line(ax, ay, ex, ey, fill=_COLOR_BODY, width=5, capstyle=tk.ROUND)

    def _draw_point_arm(self, c: tk.Canvas, dy: float) -> None:
        ax = _CX + _BODY_W // 2
        ay = _BODY_Y + 6 + dy
        c.create_line(ax, ay, ax + 16, ay - 8,
                      fill=_COLOR_BODY, width=5, capstyle=tk.ROUND)

    def _draw_speech(self, c: tk.Canvas, text: str) -> None:
        # small tooltip above head
        c.create_rectangle(2, 2, _WIN_W - 2, 22,
                            fill="#F0FAFF", outline="#B0EEFF", width=1)
        c.create_text(_WIN_W // 2, 12, text=text[:22],
                      font=("Helvetica", 7), fill="#2A6080",
                      anchor="center", width=_WIN_W - 8)


# ── module-level singleton ────────────────────────────────────────────────────

_renderer: Optional[AvatarRenderer] = None


def get() -> AvatarRenderer:
    """Return the module-level singleton renderer."""
    global _renderer
    if _renderer is None:
        _renderer = AvatarRenderer()
    return _renderer
