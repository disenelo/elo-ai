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

        title = _parse_title(query)
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
