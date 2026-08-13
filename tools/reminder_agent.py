"""
tools/reminder_agent.py — eLo reminder system.

Writes reminder files to ~/Documents/DISENELO/reminders/ and schedules
a macOS notification via osascript at the right time.

eLo says: "I'll remind you in an hour" or "Reminder set for tomorrow morning."
"""
from __future__ import annotations

import os
import re
import json
import subprocess
import datetime

_REMINDERS_DIR = os.path.expanduser("~/Documents/DISENELO/reminders")

_TRIGGER_PHRASES = (
    "remind me",
    "set a reminder",
    "don't let me forget",
    "remember to",
    "note that",
    "flag that",
    "come back to",
    "set a note",
)

_TIME_PATTERNS = {
    "in an hour":          60,
    "in 1 hour":           60,
    "in 2 hours":          120,
    "in 30 minutes":       30,
    "in 30 mins":          30,
    "in 15 minutes":       15,
    "tomorrow morning":    None,  # handled specially
    "tomorrow":            None,
    "end of day":          None,
}


def is_reminder_intent(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in _TRIGGER_PHRASES)


def set_reminder(text: str, context: str = "") -> str:
    """
    Parse the reminder intent, write a reminder file, schedule notification.
    Returns eLo's confirmation string.
    """
    os.makedirs(_REMINDERS_DIR, exist_ok=True)

    now = datetime.datetime.now()
    delay_minutes = 60  # default: 1 hour

    t = text.lower()
    for phrase, mins in _TIME_PATTERNS.items():
        if phrase in t:
            if mins is not None:
                delay_minutes = mins
            elif "tomorrow morning" in phrase:
                tomorrow = now + datetime.timedelta(days=1)
                fire_at  = tomorrow.replace(hour=9, minute=0, second=0)
                delay_minutes = int((fire_at - now).total_seconds() / 60)
            elif "tomorrow" in phrase:
                tomorrow = now + datetime.timedelta(days=1)
                fire_at  = tomorrow.replace(hour=10, minute=0, second=0)
                delay_minutes = int((fire_at - now).total_seconds() / 60)
            elif "end of day" in phrase:
                eod = now.replace(hour=18, minute=0, second=0)
                if eod < now:
                    eod += datetime.timedelta(days=1)
                delay_minutes = int((eod - now).total_seconds() / 60)
            break

    # Extract the thing to remember
    thing = re.sub(
        r'(remind me|set a reminder|don\'t let me forget|remember to|note that|flag that|come back to|set a note)\s*(to|about|that|for)?\s*',
        '', text, flags=re.I
    ).strip().strip('.,!?') or context[:80] or text[:80]

    fire_time = now + datetime.timedelta(minutes=delay_minutes)
    time_str  = fire_time.strftime("%Y-%m-%d %H:%M")

    # Write reminder file
    filename = f"reminder_{now.strftime('%Y%m%d_%H%M%S')}.json"
    path     = os.path.join(_REMINDERS_DIR, filename)
    record   = {
        "created":   now.isoformat(),
        "fire_at":   fire_time.isoformat(),
        "topic":     thing,
        "context":   context[:200],
        "status":    "pending",
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
    except Exception as e:
        return f"Saved in memory but couldn't write the file — {e}"

    # Schedule macOS notification
    delay_secs = delay_minutes * 60
    script = (
        f'delay {delay_secs}\n'
        f'display notification "{thing[:100]}" with title "eLo reminder"'
    )
    try:
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    # Human-readable time label
    if delay_minutes < 60:
        time_label = f"in {delay_minutes} minutes"
    elif delay_minutes == 60:
        time_label = "in an hour"
    elif delay_minutes < 1440:
        hrs = delay_minutes // 60
        time_label = f"in {hrs} hours"
    else:
        time_label = f"tomorrow ({fire_time.strftime('%H:%M')})"

    return f"Reminder set — {time_label}. '{thing[:60]}'"


def pending_reminders() -> list[dict]:
    """Return all pending reminders."""
    if not os.path.isdir(_REMINDERS_DIR):
        return []
    result = []
    for fn in sorted(os.listdir(_REMINDERS_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(_REMINDERS_DIR, fn), encoding="utf-8") as f:
                r = json.load(f)
            if r.get("status") == "pending":
                result.append(r)
        except Exception:
            pass
    return result
