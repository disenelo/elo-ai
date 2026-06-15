"""
presence_playback/playback.py — drives blender_state.json from a scripted timeline.

Run this when eLo is idle (no conversation) to keep the rig alive with
the 2-minute scripted presence loop.

Does NOT require main.py to be running.

Run:
    python -m presence_playback.playback              # one full loop, writes state.json
    python -m presence_playback.playback --continuous  # loops forever (Ctrl+C to stop)
    python -m presence_playback.playback --preview     # print timeline only, no write
"""
from __future__ import annotations
import sys
import time

from presence_playback.timeline import IDLE_LOOP, LOOP_DURATION, get_at
from blender.state_driver import write as _write_state


_TICK_INTERVAL = 0.25   # seconds between state.json updates


def _entry_to_command(entry) -> dict:
    return {
        "animation": entry.clip,
        "speed":     0.6 + entry.intensity * 0.4,
        "intensity": entry.intensity,
        "energy":    entry.intensity,
        "duration":  entry.duration,
        "mood":      entry.mood,
        "mode":      entry.mode,
    }


def run_loop(continuous: bool = False) -> None:
    t_start = time.monotonic()
    runs    = 0

    print(f"[presence_playback] starting {'continuous' if continuous else '1 loop'}  "
          f"({LOOP_DURATION:.0f}s per loop)")

    try:
        while True:
            now     = time.monotonic()
            elapsed = now - t_start
            entry   = get_at(elapsed)
            cmd     = _entry_to_command(entry)
            _write_state(cmd)

            if elapsed >= LOOP_DURATION:
                runs += 1
                if not continuous:
                    print(f"[presence_playback] loop complete ({runs} run)")
                    break
                t_start = now  # reset loop

            time.sleep(_TICK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[presence_playback] stopped.")


def preview() -> None:
    print(f"\n{'t_start':>8}  {'mode':<12}  {'clip':<8}  {'intensity':>10}  {'mood'}")
    print("-" * 60)
    for e in IDLE_LOOP:
        print(f"{e.t_start:>7.1f}s  {e.mode:<12}  {e.clip:<8}  {e.intensity:>10.2f}  {e.mood}")
    print(f"\nTotal: {LOOP_DURATION:.0f}s")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--preview" in args:
        preview()
    elif "--continuous" in args:
        run_loop(continuous=True)
    else:
        run_loop(continuous=False)
