"""
tools/timer_agent.py — countdown timer agent for eLo OS.

Sets named or unnamed timers in background threads. When a timer fires:
  1. macOS notification (osascript display notification)
  2. eLo speaks the completion if voice_engine is available

Multiple timers run concurrently. Each is tracked so eLo can list what's running.
"""

from __future__ import annotations

import os
import re
import time
import threading
import subprocess
import logging
from typing import Optional

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

# Active timer registry — {id: {"label": str, "ends_at": float}}
_timers: dict[int, dict] = {}
_timer_lock = threading.Lock()
_timer_id_counter = 0


# ── Duration parsing ──────────────────────────────────────────────────────────

def parse_duration(text: str) -> Optional[float]:
    """Extract duration in minutes from natural language. Returns None if not found."""
    t = text.lower()

    if "half an hour" in t or "half hour" in t:
        return 30.0
    if re.search(r"\ban?\s+hour\b", t):
        return 60.0
    if re.search(r"\ban?\s+hour\s+and\s+a\s+half\b", t):
        return 90.0

    m = re.search(r"(\d+(?:\.\d+)?)\s*h(?:our|r)?s?", t)
    if m:
        return float(m.group(1)) * 60

    m = re.search(r"(\d+(?:\.\d+)?)\s*m(?:in(?:ute)?)?s?(?:\b|$)", t)
    if m:
        return float(m.group(1))

    m = re.search(r"(\d+(?:\.\d+)?)\s*s(?:ec(?:ond)?)?s?", t)
    if m:
        return float(m.group(1)) / 60

    return None


def _extract_label(text: str) -> str:
    """Pull a human label out of 'set a timer for X called Y' / 'X minute Y timer'."""
    t = text.lower()
    # "timer for X [called/named/labelled Y]"
    m = re.search(r"(?:called|named|labelled?)\s+[\"']?(.+?)[\"']?\s*$", t)
    if m:
        return m.group(1).strip().title()
    # "X minute focus" / "X min pomodoro"
    m = re.search(r"\d+\s*(?:min(?:ute)?|hour)s?\s+(.+?)(?:\s+timer)?$", t)
    if m:
        label = m.group(1).strip()
        if label not in ("timer", "break", "focus", "pomodoro", ""):
            return label.title()
    return ""


# ── Timer execution ───────────────────────────────────────────────────────────

def _fire_timer(timer_id: int, label: str, minutes: float) -> None:
    """Background thread: sleep, then notify."""
    seconds = max(1, int(minutes * 60))
    time.sleep(seconds)

    with _timer_lock:
        _timers.pop(timer_id, None)

    display = label if label else f"{_format_duration(minutes)} timer"
    msg = f"{display} — done!"

    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{msg}" with title "eLo" sound name "Glass"'],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass

    try:
        from voice.voice_engine import speak
        speak(msg)
    except Exception:
        pass


def _format_duration(minutes: float) -> str:
    if minutes < 1:
        return f"{int(minutes * 60)} second"
    if minutes < 60:
        m = int(minutes)
        return f"{m} minute" + ("s" if m != 1 else "")
    h = int(minutes // 60)
    m = int(minutes % 60)
    parts = [f"{h} hour" + ("s" if h != 1 else "")]
    if m:
        parts.append(f"{m} minute" + ("s" if m != 1 else ""))
    return " ".join(parts)


# ── Public API ────────────────────────────────────────────────────────────────

def set_timer(minutes: float, label: str = "") -> str:
    """Start a timer. Returns a confirmation string."""
    global _timer_id_counter

    with _timer_lock:
        _timer_id_counter += 1
        tid = _timer_id_counter
        _timers[tid] = {"label": label, "ends_at": time.time() + minutes * 60}

    t = threading.Thread(target=_fire_timer, args=(tid, label, minutes), daemon=True)
    t.start()

    display = label if label else _format_duration(minutes) + " timer"
    return f"Timer set: {display} in {_format_duration(minutes)}."


def list_active() -> str:
    """Return a short string listing running timers."""
    with _timer_lock:
        if not _timers:
            return "No active timers."
        lines = []
        now = time.time()
        for tid, info in _timers.items():
            remaining = max(0, info["ends_at"] - now)
            rem_min = remaining / 60
            label = info["label"] or "Timer"
            lines.append(f"{label}: {_format_duration(rem_min)} left")
        return "Active timers: " + ", ".join(lines)


def is_timer_intent(text: str) -> bool:
    t = text.lower()
    has_timer = any(k in t for k in ("timer", "pomodoro", "focus timer", "break timer"))
    has_duration = parse_duration(t) is not None
    has_remind_in = bool(re.search(r"\bremind\s+me\s+in\b", t))
    return (has_timer and has_duration) or has_remind_in


def agent(query: str) -> str:
    """Parse query, set timer or list active timers, return context string."""
    t = query.lower()

    if any(k in t for k in ("list", "what timers", "active timers", "my timers", "running timers")):
        return list_active()

    minutes = parse_duration(t)
    if minutes is None:
        return "Timer request understood but I couldn't find a duration — try '25 minutes' or 'an hour'."

    label = _extract_label(query)
    return set_timer(minutes, label)
