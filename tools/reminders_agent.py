"""
tools/reminders_agent.py — Apple Reminders via AppleScript.

No API key, no OAuth. Reads and writes directly to Reminders.app.
macOS only. Returns pending reminders or confirms an addition as a context string.
"""
from __future__ import annotations

import re
import subprocess
from datetime import date, timedelta


def is_reminders_intent(text: str) -> bool:
    t = text.lower()
    # "remind me in N ..." belongs to timer_agent — exclude it
    if re.search(r"remind me\s+in\s+\d+", t):
        return False
    triggers = [
        "remind me to",
        "add a reminder",
        "add reminder",
        "my reminders",
        "show my reminders",
        "what are my reminders",
    ]
    return any(trigger in t for trigger in triggers)


def _run(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


_SCRIPT_LIST = """
tell application "Reminders"
    set pending to (every reminder in default list whose completed is false)
    set names to {}
    repeat with r in pending
        set end of names to name of r
        if (count of names) = 10 then exit repeat
    end repeat
    if (count of names) = 0 then
        return ""
    end if
    set AppleScript's text item delimiters to "||"
    set nameStr to names as text
    set AppleScript's text item delimiters to ""
    return nameStr
end tell
"""

_SCRIPT_ADD = """
tell application "Reminders"
    make new reminder at end of default list with properties {{name:"{title}"}}
end tell
"""

_SCRIPT_ADD_DATED = """
tell application "Reminders"
    set newRem to make new reminder at end of default list with properties {{name:"{title}"}}
    set due date of newRem to (current date) + ({days} * days)
end tell
"""


def _parse_title(query: str) -> str:
    t = query.strip()
    for prefix in [
        r"add a reminder to\s+",
        r"add a reminder:\s*",
        r"add reminder:\s*",
        r"add reminder to\s+",
        r"remind me to\s+",
    ]:
        m = re.match(prefix, t, re.IGNORECASE)
        if m:
            t = t[m.end():]
            break
    return t.strip()


_ADD_RE = re.compile(r"^(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
                     r"(?:add\s+(?:a\s+)?reminder(?:\s+to|:)\s*|remind\s+me\s+to\s+)", re.I)


def _explicit_add_title(query: str) -> str | None:
    """The reminder title when the text is an explicit add request, else None."""
    t = query.strip()
    low = t.lower()
    if "\nuser asked:" in low:                       # enriched turn: keep only David's words
        t = t[low.rfind("\nuser asked:") + len("\nuser asked:"):].strip()
    m = _ADD_RE.match(t)
    if not m:
        return None
    title = t[m.end():].strip().rstrip("?.!").strip()
    if not title or title.startswith("["):
        return None
    return title


def _parse_due_days(title: str) -> tuple[str, int | None]:
    """Return (cleaned title, days_offset) or (title, None) if no date found."""
    patterns = [
        (r"\s+tomorrow\s*$", 1),
        (r"\s+next week\s*$", 7),
        (r"\s+in (\d+) days?\s*$", None),  # None = capture group
    ]
    for pattern, offset in patterns:
        m = re.search(pattern, title, re.IGNORECASE)
        if m:
            days = int(m.group(1)) if offset is None else offset
            cleaned = title[:m.start()].strip()
            return cleaned, days
    return title, None


def _is_list_intent(query: str) -> bool:
    t = query.lower()
    return any(w in t for w in ["what are my reminders", "my reminders", "what do i need to do"])


def agent(query: str) -> str:
    try:
        if _is_list_intent(query):
            raw = _run(_SCRIPT_LIST)
            if not raw:
                return "No pending reminders."
            items = raw.split("||")
            numbered = ", ".join(f"{i + 1}. {name}" for i, name in enumerate(items))
            return f"Your reminders: {numbered}"

        # Write only on an explicit add ("remind me to …", "add a reminder …").
        # Anything else selected here (chat, enriched "[tag] … user asked: …"
        # text) used to become a reminder — 2026-06..09 junk in David's list.
        title = _explicit_add_title(query)
        if not title:
            return spoken_open_reminders()            # read-only, never a write
        title, days = _parse_due_days(title)

        # Escape any quotes in the title to avoid breaking the AppleScript string
        safe_title = title.replace('"', '\\"')

        if days is not None:
            script = _SCRIPT_ADD_DATED.format(title=safe_title, days=days)
            _run(script)
            if days == 1:
                due_label = "due tomorrow"
            elif days == 7:
                due_label = "due next week"
            else:
                due_date = date.today() + timedelta(days=days)
                due_label = f"due {due_date.strftime('%d %b')}"
            return f"Added reminder: '{title}' {due_label}."

        script = _SCRIPT_ADD.format(title=safe_title)
        _run(script)
        return f"Added reminder: '{title}'."

    except Exception as e:
        return f"Reminders unavailable: {e}"


# ── Open reminders from Reminders' own store (B3 2026-10-07) ──────────────────
# "What's on my reminders?" timed out: the AppleScript `whose completed is false`
# query is too slow. Reminders keeps its data in local SQLite stores — read-only
# here, every store, open + not deleted.
import glob as _glob
import os as _os
import sqlite3 as _sqlite3
from datetime import datetime as _dt

_STORES = _os.path.expanduser("~/Library/Group Containers/group.com.apple.reminders/Container_v1/Stores/Data-*.sqlite")
_EPOCH_2001 = 978307200


def open_reminders() -> list[dict] | None:
    """[{title, due (datetime|None), list, created}] — upcoming due dates soonest
    first, then everything else newest first. None when no store can be read."""
    out, read_any = [], False
    for path in _glob.glob(_STORES):
        try:
            con = _sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=3)
            rows = con.execute(
                """select r.ZTITLE, r.ZDUEDATE, l.ZNAME, r.ZCREATIONDATE from ZREMCDREMINDER r
                   left join ZREMCDBASELIST l on l.Z_PK = r.ZLIST
                   where r.ZCOMPLETED = 0 and coalesce(r.ZMARKEDFORDELETION, 0) = 0
                     and r.ZTITLE is not null and trim(r.ZTITLE) != ''""").fetchall()
            con.close()
            read_any = True
        except Exception:
            continue
        for title, due, lst, created in rows:
            out.append({"title": title.strip(), "due": _dt.fromtimestamp(due + _EPOCH_2001) if due else None,
                        "list": lst or "", "created": created or 0.0})
    if not read_any:
        return None
    today = _dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
    upcoming = sorted((r for r in out if r["due"] and r["due"] >= today), key=lambda r: r["due"])
    rest = sorted((r for r in out if not (r["due"] and r["due"] >= today)), key=lambda r: -r["created"])
    return upcoming + rest


def spoken_open_reminders(limit: int = 5) -> str:
    rs = open_reminders()
    if rs is None:
        return "I can't read your reminders right now."
    if not rs:
        return "No open reminders."
    items = []
    for r in rs[:limit]:
        fmt = "%a %d %b" if r["due"] and r["due"].year == _dt.now().year else "%d %b %Y"
        due = f" (due {r['due'].strftime(fmt)})" if r["due"] else ""
        items.append(r["title"] + due)
    more = f" — and {len(rs) - limit} more" if len(rs) > limit else ""
    return f"You've got {len(rs)} open reminder{'s' if len(rs) != 1 else ''}: " + "; ".join(items) + more + "."
