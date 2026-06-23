"""
tools/calendar_agent.py — Apple Calendar events via AppleScript.

No API key, no OAuth. Reads directly from the user's Calendar.app.
macOS only. Returns today's events or upcoming events as a context string.
"""
from __future__ import annotations

import subprocess
from datetime import datetime


_SCRIPT_TODAY = """
tell application "Calendar"
    set today to current date
    set startOfDay to today - (time of today)
    set endOfDay to startOfDay + 86399
    set allEvents to {}
    repeat with cal in calendars
        try
            set calEvents to (every event of cal whose start date >= startOfDay and start date <= endOfDay)
            repeat with e in calEvents
                set end of allEvents to (summary of e & " at " & (time string of (start date of e)))
            end repeat
        end try
    end repeat
    if length of allEvents > 0 then
        set AppleScript's text item delimiters to ", "
        set eventStr to allEvents as text
        set AppleScript's text item delimiters to ""
        return eventStr
    else
        return "no events today"
    end if
end tell
"""

_SCRIPT_NEXT = """
tell application "Calendar"
    set rightNow to current date
    set searchEnd to rightNow + (7 * 86400)
    set allEvents to {}
    repeat with cal in calendars
        try
            set calEvents to (every event of cal whose start date >= rightNow and start date <= searchEnd)
            repeat with e in calEvents
                set end of allEvents to (summary of e & " on " & (short date string of (start date of e)))
            end repeat
        end try
    end repeat
    if length of allEvents > 0 then
        set AppleScript's text item delimiters to "; "
        set eventStr to allEvents as text
        set AppleScript's text item delimiters to ""
        return eventStr
    else
        return "nothing scheduled this week"
    end if
end tell
"""


def _run(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=8.0,
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return f"error: {e}"


def agent(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["next", "coming", "week", "upcoming", "soon", "schedule"]):
        result = _run(_SCRIPT_NEXT)
        return f"CALENDAR (next 7 days): {result}"
    result = _run(_SCRIPT_TODAY)
    return f"CALENDAR (today {datetime.now().strftime('%a %d %b')}): {result}"
