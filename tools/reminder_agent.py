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

# B3 2026-10-06: "note that" / "flag that" / "set a note" / "come back to" removed —
# "come back to the song thing later" set a real reminder; notes are vault_write.
_TRIGGER_PHRASES = (
    "remind me",
    "set a reminder",
    "don't let me forget",
    "remember to",
)
_DURATION_RE = re.compile(r"\bin\s+(an?|\d+(?:\.\d+)?)\s*(min(?:ute)?s?|hours?|hrs?)\b", re.I)

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
    _dm = _DURATION_RE.search(t)
    if _dm:
        n = 1.0 if _dm.group(1) in ("a", "an") else float(_dm.group(1))
        delay_minutes = int(round(n * (60 if _dm.group(2).startswith(("h", "hr")) else 1)))
    for phrase, mins in ({} if _dm else _TIME_PATTERNS).items():
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
    thing = _DURATION_RE.sub("", text)
    thing = re.sub(r"\b(?:in an hour|tomorrow(?: morning)?|later|end of day)\b", "", thing, flags=re.I)
    thing = re.sub(
        r"(remind me|set a reminder|don't let me forget|remember to)\s*(to|about|that|for)?\s*",
        "", thing, flags=re.I,
    )
    thing = re.sub(r"^\s*(?:to|about|that|for)\s+", "", thing.strip(), flags=re.I)
    thing = re.sub(r"\s{2,}", " ", thing).strip().strip(".,!?") or context[:80] or text[:80]

    fire_time = now + datetime.timedelta(minutes=delay_minutes)
    if delay_minutes >= 60 and fire_time.date() > now.date():
        fire_time = fire_time.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1 if fire_time.second else 0)
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
    delay_secs = max(1, int((fire_time - now).total_seconds()))
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
    if fire_time.date() > now.date():
        time_label = ("tomorrow" if (fire_time.date() - now.date()).days == 1 else fire_time.strftime("%A")) \
            + f" at {fire_time.strftime('%H:%M')}"
    elif delay_minutes < 60:
        time_label = f"in {delay_minutes} minutes"
    elif delay_minutes == 60:
        time_label = "in an hour"
    elif delay_minutes < 1440:
        hrs = delay_minutes // 60
        time_label = f"in {hrs} hours"
    else:
        time_label = f"tomorrow ({fire_time.strftime('%H:%M')})"

    return f"Got it — I'll remind you {time_label} to {thing[:80]}."


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
