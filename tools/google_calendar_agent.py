"""
tools/google_calendar_agent.py — Google Calendar via API.

Requires one-time OAuth setup:
    python3 tools/google_calendar_agent.py --setup

After setup, credentials are stored in ~/.elo_gcal_token.json and reused automatically.

Setup steps:
    1. Go to console.cloud.google.com → New Project
    2. Enable Google Calendar API
    3. Create OAuth 2.0 credentials (Desktop App) → download as credentials.json
    4. Place credentials.json at ~/.elo_gcal_credentials.json
    5. Run: python3 tools/google_calendar_agent.py --setup
    6. Approve in browser — done.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

_CREDS_PATH = os.path.expanduser("~/.elo_gcal_credentials.json")
_TOKEN_PATH = os.path.expanduser("~/.elo_gcal_token.json")
_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


def _get_service():
    """Return an authenticated Google Calendar service, or raise if not set up."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError("Google API packages not installed. Run: pip install google-api-python-client google-auth-oauthlib")

    creds = None
    if os.path.exists(_TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(_CREDS_PATH):
                raise RuntimeError(
                    f"Google Calendar not set up. Download OAuth credentials from "
                    f"console.cloud.google.com and save as {_CREDS_PATH}, "
                    f"then run: python3 tools/google_calendar_agent.py --setup"
                )
            flow = InstalledAppFlow.from_client_secrets_file(_CREDS_PATH, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def is_available() -> bool:
    """True if Google Calendar credentials are stored and usable."""
    return os.path.exists(_TOKEN_PATH)


def get_events(days: int = 7, max_results: int = 10) -> list[dict]:
    """
    Return upcoming events from Google Calendar.

    Returns list of {summary, start, end, calendar} dicts.
    Raises on auth failure or network error.
    """
    service = _get_service()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for item in result.get("items", []):
        start = item["start"].get("dateTime", item["start"].get("date", ""))
        events.append({
            "summary": item.get("summary", "Untitled"),
            "start":   start,
        })
    return events


def create_event(summary: str, start: datetime, end: datetime | None = None,
                 description: str = "") -> str:
    """
    Create a new event in Google Calendar.

    Returns the event link or a confirmation string.
    """
    service = _get_service()
    if end is None:
        end = start + timedelta(hours=1)

    event_body = {
        "summary": summary,
        "start":   {"dateTime": start.isoformat(), "timeZone": "Europe/London"},
        "end":     {"dateTime": end.isoformat(),   "timeZone": "Europe/London"},
    }
    if description:
        event_body["description"] = description

    created = service.events().insert(calendarId="primary", body=event_body).execute()
    return created.get("htmlLink", "event created")


def agent_read(query: str) -> str:
    """
    Context string for eLo — upcoming Google Calendar events.
    Returns empty string if not set up (falls back to Apple Calendar).
    """
    try:
        q = query.lower()
        days = 7 if any(w in q for w in ["week", "next", "upcoming", "schedule", "soon"]) else 1
        events = get_events(days=days)
        if not events:
            label = "this week" if days == 7 else "today"
            return f"Google Calendar: nothing scheduled {label}."
        lines = []
        for e in events:
            start_str = e["start"]
            try:
                dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                label = dt.strftime("%a %d %b at %-I%p").replace("AM","am").replace("PM","pm")
            except Exception:
                label = start_str[:10]
            lines.append(f"{e['summary']} — {label}")
        return "Google Calendar: " + "; ".join(lines)
    except RuntimeError as e:
        if "not set up" in str(e) or "credentials" in str(e).lower():
            return ""   # silent fallback to Apple Calendar
        return f"Google Calendar unavailable: {str(e)[:60]}"
    except Exception as e:
        return ""   # network/auth failure — silent fallback


def agent_add(query: str) -> str:
    """
    Parse a natural-language event creation request and add it to Google Calendar.

    Returns a confirmation string for eLo to speak.
    """
    try:
        # Simple natural language parse — "add [title] [on/at date/time]"
        import re
        q = query.strip()

        now = datetime.now()
        start = None

        # ── Day-of-week resolution ─────────────────────────────────────────────
        # "next Tuesday", "on Friday", "this Thursday"
        _DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        dow_m = re.search(
            r'\b(?:next\s+|this\s+)?(' + '|'.join(_DAYS) + r')\b', q, re.IGNORECASE
        )
        if dow_m:
            target_day = _DAYS.index(dow_m.group(1).lower())
            days_ahead = (target_day - now.weekday()) % 7
            # "next X" always means the X at least 7 days out
            if re.search(r'\bnext\b', q[:dow_m.start() + 10], re.IGNORECASE):
                if days_ahead == 0:
                    days_ahead = 7
            elif days_ahead == 0:
                days_ahead = 7  # same weekday → next week
            base = now + timedelta(days=days_ahead)
            start = base.replace(hour=9, minute=0, second=0, microsecond=0)

        # "tomorrow"
        if re.search(r'\btomorrow\b', q, re.IGNORECASE):
            base = now + timedelta(days=1)
            start = base.replace(hour=9, minute=0, second=0, microsecond=0)

        # "at 3pm", "at 15:00", "at 3:30pm" — applies to whatever date was set above
        time_m = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', q, re.IGNORECASE)
        if time_m:
            hour = int(time_m.group(1))
            minute = int(time_m.group(2) or 0)
            ampm = (time_m.group(3) or "").lower()
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            base = start or now
            start = base.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if not start:
            start = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        # ── Title extraction ───────────────────────────────────────────────────
        title = re.sub(r'\b(add|create|schedule|book|put|set\s+up|shoot|record|film)\b', '', q, flags=re.IGNORECASE)
        title = re.sub(r'\b(?:next\s+|this\s+)?(?:' + '|'.join(_DAYS) + r')\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'(tomorrow|today|at\s+\d[\d:]*\s*(am|pm)?|(on|for|by)\s+\w+)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip(" ,.-")
        if not title:
            title = "New Event"

        link = create_event(title, start)
        day_label = start.strftime("%A %-d %b")
        time_label = start.strftime("%-I%p").lower()
        return f"Added '{title}' to Google Calendar — {day_label} at {time_label}."

    except RuntimeError as e:
        return f"Google Calendar not set up — {str(e)[:80]}"
    except Exception as e:
        return f"Couldn't add that: {str(e)[:60]}"


# ── CLI setup ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if "--setup" in sys.argv:
        print("Opening browser for Google Calendar authorisation...")
        try:
            _get_service()
            print(f"✓ Authorised. Token saved to {_TOKEN_PATH}")
            print("Google Calendar is now connected to eLo.")
        except Exception as e:
            print(f"Setup failed: {e}")
    elif "--test" in sys.argv:
        if is_available():
            print(agent_read("what's on this week"))
        else:
            print("Google Calendar not set up. Run: python3 tools/google_calendar_agent.py --setup")
    else:
        print(__doc__)
