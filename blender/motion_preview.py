"""
blender/motion_preview.py — terminal preview of the current motion state.

Shows what Blender should be receiving right now.
Does not modify any state — read-only view.

Run:
    python -m blender.motion_preview
    python -m blender.motion_preview --watch   (live poll every 250ms)
"""
from __future__ import annotations
import sys
import time

from blender.state_driver import read as _read_state


_MOOD_COLOR = {
    "open":    "\033[96m",   # cyan
    "warm":    "\033[93m",   # yellow
    "focused": "\033[94m",   # blue
    "quiet":   "\033[90m",   # grey
    "lit":     "\033[95m",   # magenta
}
_RESET = "\033[0m"


def _bar(value: float, width: int = 20) -> str:
    filled = int(round(value * width))
    return "█" * filled + "░" * (width - filled)


def show(data: dict) -> None:
    motion = data.get("motion", {})
    state  = data.get("state",  {})

    animation = motion.get("animation", "—")
    mode      = motion.get("mode",      "—")
    mood      = motion.get("mood",      "—")
    speed     = motion.get("speed",     0.0)
    intensity = motion.get("intensity", 0.0)
    duration  = motion.get("duration",  0.0)
    energy    = state.get("energy",     0.0)

    color = _MOOD_COLOR.get(mood, "")

    print(f"\n  {color}eLo — {mode} ({mood}){_RESET}")
    print(f"  clip       {animation}")
    print(f"  energy     {_bar(energy)}  {energy:.2f}")
    print(f"  intensity  {_bar(intensity)}  {intensity:.2f}")
    print(f"  speed      {speed:.2f}  |  duration {duration:.1f}s")


def preview_once() -> None:
    data = _read_state()
    if not data:
        print("  [no state — run eLo OS first]")
        return
    show(data)


def watch(interval: float = 0.25) -> None:
    print("  watching blender_state.json  (Ctrl+C to stop)\n")
    try:
        while True:
            print("\033[2J\033[H", end="")  # clear
            preview_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n  stopped.")


if __name__ == "__main__":
    if "--watch" in sys.argv:
        watch()
    else:
        preview_once()
