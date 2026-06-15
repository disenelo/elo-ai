"""
presence_playback/timeline.py — scripted 2-minute presence timeline.

A fixed sequence of presence states with timings.
Used for: idle animation when eLo is waiting, demo/Kickstarter filming,
Blender preview sessions where no conversation is happening.

No AI decisions in here. Pure choreography.
Each entry: {t_start, mode, intensity, mood, duration, clip}
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TimelineEntry:
    t_start:   float  # seconds from start
    mode:      str    # presence mode name
    clip:      str    # animation clip
    intensity: float
    mood:      str
    duration:  float  # how long to hold


# 2-minute idle presence loop
# eLo breathes, observes, leans in, settles, repeats
IDLE_LOOP: list[TimelineEntry] = [
    TimelineEntry(t_start=0.0,   mode="idle",      clip="idle",  intensity=0.4, mood="open",    duration=8.0),
    TimelineEntry(t_start=8.0,   mode="observing", clip="idle",  intensity=0.5, mood="warm",    duration=6.0),
    TimelineEntry(t_start=14.0,  mode="thinking",  clip="idle",  intensity=0.45, mood="focused", duration=5.0),
    TimelineEntry(t_start=19.0,  mode="idle",      clip="idle",  intensity=0.35, mood="open",    duration=7.0),
    TimelineEntry(t_start=26.0,  mode="exploring", clip="walk",  intensity=0.55, mood="open",    duration=6.0),
    TimelineEntry(t_start=32.0,  mode="idle",      clip="idle",  intensity=0.4,  mood="open",    duration=8.0),
    TimelineEntry(t_start=40.0,  mode="observing", clip="idle",  intensity=0.5,  mood="warm",    duration=5.0),
    TimelineEntry(t_start=45.0,  mode="resting",   clip="idle",  intensity=0.3,  mood="quiet",   duration=10.0),
    TimelineEntry(t_start=55.0,  mode="idle",      clip="idle",  intensity=0.4,  mood="open",    duration=8.0),
    TimelineEntry(t_start=63.0,  mode="building",  clip="walk",  intensity=0.65, mood="focused", duration=6.0),
    TimelineEntry(t_start=69.0,  mode="celebrating", clip="jump", intensity=0.75, mood="lit",    duration=3.0),
    TimelineEntry(t_start=72.0,  mode="observing", clip="idle",  intensity=0.5,  mood="warm",    duration=6.0),
    TimelineEntry(t_start=78.0,  mode="idle",      clip="idle",  intensity=0.35, mood="open",    duration=8.0),
    TimelineEntry(t_start=86.0,  mode="thinking",  clip="idle",  intensity=0.4,  mood="focused", duration=6.0),
    TimelineEntry(t_start=92.0,  mode="exploring", clip="walk",  intensity=0.5,  mood="open",    duration=7.0),
    TimelineEntry(t_start=99.0,  mode="resting",   clip="idle",  intensity=0.3,  mood="quiet",   duration=8.0),
    TimelineEntry(t_start=107.0, mode="idle",      clip="idle",  intensity=0.4,  mood="open",    duration=13.0),  # loop end
]

LOOP_DURATION = 120.0  # total length in seconds


def get_at(t: float) -> TimelineEntry:
    """Return the entry active at time t (wraps at LOOP_DURATION)."""
    t_loop = t % LOOP_DURATION
    active = IDLE_LOOP[0]
    for entry in IDLE_LOOP:
        if entry.t_start <= t_loop:
            active = entry
        else:
            break
    return active
