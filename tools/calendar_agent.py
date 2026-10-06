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


# ── Calendar's own local store (B3 2026-10-06) ────────────────────────────────
# The AppleScript queries time out (>8 s; one calendar took minutes) because
# Calendar expands recurring events on every query. EventKit from this Python
# saw only an empty default calendar — it would have said "nothing" falsely.
# Calendar.app keeps every occurrence already expanded in its own SQLite store
# (OccurrenceCache) — read-only here, ~0.3 s. A day outside the cached range is
# "can't tell" (None), never "nothing".
import os as _os
import sqlite3 as _sqlite3

_DB = _os.path.expanduser("~/Library/Group Containers/group.com.apple.calendar/Calendar.sqlitedb")
_EPOCH_2001 = 978307200


def events(days: int = 1, start_offset_days: int = 0) -> list[dict] | None:
    """[{title, start, end, all_day, calendar}] from start-of-today + offset for
    `days` days, sorted, de-duplicated. None when the store can't vouch for it."""
    try:
        con = _sqlite3.connect(f"file:{_DB}?mode=ro", uri=True, timeout=3)
    except Exception:
        return None
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        a = today.timestamp() + 86400 * start_offset_days - _EPOCH_2001
        b = a + 86400 * days
        lo, hi = con.execute("select min(day), max(day) from OccurrenceCacheDays").fetchone()
        if lo is None or a < lo or b > hi + 86400:
            return None
        rows = con.execute(
            """select i.summary, o.occurrence_start_date, o.occurrence_end_date, i.all_day, c.title
               from OccurrenceCache o
               join CalendarItem i on i.ROWID = o.event_id
               join Calendar c on c.ROWID = i.calendar_id
               where o.occurrence_start_date >= ? and o.occurrence_start_date < ?
               order by o.occurrence_start_date""", (a, b)).fetchall()
    except Exception:
        return None
    finally:
        con.close()
    out, seen = [], set()
    for title, st, en, all_day, cal in rows:
        key = (title, st)
        if key in seen or (cal or "") == "Siri Suggestions":
            continue
        seen.add(key)
        out.append({
            "title": str(title or "(untitled)"),
            "start": datetime.fromtimestamp(st + _EPOCH_2001),
            "end": datetime.fromtimestamp((en or st) + _EPOCH_2001),
            # Birthdays come through as UTC-midnight, 24 h, not flagged all-day.
            "all_day": bool(all_day) or ((en or st) - st) >= 23 * 3600,
            "calendar": str(cal or ""),
        })
    return out


def _when(ev: dict, with_day: bool = False) -> str:
    day = ev["start"].strftime("%A ") if with_day else ""
    return f"{day}all day" if ev["all_day"] else f"{day}at {ev['start'].strftime('%H:%M')}"


def spoken(query: str) -> str | None:
    """eLo's line for a calendar question, from EventKit. None if unavailable."""
    q = query.lower()
    if "tomorrow" in q:
        evs, label = events(1, 1), "tomorrow"
    elif any(w in q for w in ("week", "upcoming", "coming up", "next few days")):
        evs, label = events(7), "in the next 7 days"
    else:
        evs, label = events(1), "today"
    if evs is None:
        return None
    if not evs:
        nxt = events(30, 1)
        line = f"Nothing on your calendar {label}."
        if label == "today" and nxt:
            line += f" Next up: {nxt[0]['title']} — {nxt[0]['start'].strftime('%A %d %B')}, {_when(nxt[0])}."
        return line
    many = label != "today" and label != "tomorrow"
    items = [f"{e['title']} {_when(e, with_day=many)}" for e in evs[:6]]
    more = f" — and {len(evs) - 6} more" if len(evs) > 6 else ""
    return f"{label.capitalize()}: " + "; ".join(items) + more + "."


def agent(query: str) -> str:
    line = spoken(query)
    if line is not None:
        return f"CALENDAR: {line}"
    q = query.lower()
    if any(w in q for w in ["next", "coming", "week", "upcoming", "soon", "schedule"]):
        result = _run(_SCRIPT_NEXT)
        return f"CALENDAR (next 7 days): {result}"
    result = _run(_SCRIPT_TODAY)
    return f"CALENDAR (today {datetime.now().strftime('%a %d %b')}): {result}"
