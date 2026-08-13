"""
tools/notes_agent.py — Apple Notes agent for eLo OS.

No API key. Uses AppleScript via Notes.app.
Creates, reads, and searches notes in your default Notes account.

Capabilities:
    create  — make a new note with a title (+ optional body)
    recent  — list the 5 most recent note titles + first line
    search  — keyword search across all notes
"""
from __future__ import annotations

import re
import subprocess


def _run(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10.0,
        )
        return result.stdout.strip()
    except Exception:
        return ""


# ── actions ───────────────────────────────────────────────────────────────────

def create_note(title: str, body: str = "") -> str:
    t = title.replace('"', '\\"').replace("\\", "\\\\")
    b = body.replace('"', '\\"').replace("\\", "\\\\")
    _run(f'''
        tell application "Notes"
            make new note at default account with properties {{name:"{t}", body:"{b}"}}
        end tell
    ''')
    return f"Note created: '{title}'"


def read_recent(n: int = 5) -> str:
    script = f'''
        tell application "Notes"
            set noteList to {{}}
            set idx to 0
            repeat with n in (notes of default account)
                if idx < {n} then
                    set nb to body of n
                    set snippet to text 1 thru (min of {{(count of nb), 80}}) of nb
                    set end of noteList to (name of n) & ": " & snippet
                    set idx to idx + 1
                end if
            end repeat
            set AppleScript's text item delimiters to " ||| "
            set result to noteList as text
            set AppleScript's text item delimiters to ""
            return result
        end tell
    '''
    raw = _run(script)
    if not raw:
        return "No notes found."
    entries = [e.strip() for e in raw.split("|||") if e.strip()]
    return "Recent notes: " + "; ".join(f"{i+1}. {e}" for i, e in enumerate(entries))


def search_notes(query: str) -> str:
    q = query.replace('"', '\\"')
    script = f'''
        tell application "Notes"
            set hits to {{}}
            repeat with n in (notes of default account)
                set nb to body of n
                if (name of n) contains "{q}" or nb contains "{q}" then
                    set snippet to text 1 thru (min of {{(count of nb), 100}}) of nb
                    set end of hits to (name of n) & ": " & snippet
                    if (count of hits) >= 3 then exit repeat
                end if
            end repeat
            if (count of hits) = 0 then return "no match"
            set AppleScript's text item delimiters to " ||| "
            set result to hits as text
            set AppleScript's text item delimiters to ""
            return result
        end tell
    '''
    raw = _run(script)
    if not raw or raw == "no match":
        return f"No notes found matching '{query}'."
    entries = [e.strip() for e in raw.split("|||") if e.strip()]
    return "Found notes: " + "; ".join(f"{i+1}. {e}" for i, e in enumerate(entries))


# ── intent detection ──────────────────────────────────────────────────────────

def is_notes_intent(text: str) -> bool:
    t = text.lower()
    create_pat = re.search(r'\b(?:make|create|add|write|new)\s+(?:a\s+)?note\b', t)
    read_pat   = re.search(r'\bmy\s+notes?\b', t) or re.search(r'\brecent\s+notes?\b', t)
    search_pat = re.search(r'\b(?:search|find)\s+(?:my\s+)?notes?\b', t)
    return bool(create_pat or read_pat or search_pat)


# ── main entry point ──────────────────────────────────────────────────────────

def agent(query: str) -> str:
    q = query.lower()

    # search
    if re.search(r'\b(?:search|find)\b', q):
        m = re.search(
            r'(?:search|find)\s+(?:notes?\s+)?(?:about|for|on|with|containing)?\s+(.+)',
            query, re.IGNORECASE,
        )
        term = m.group(1).strip().strip('"\'') if m else query
        return search_notes(term)

    # create
    if re.search(r'\b(?:make|create|add|write|new)\b', q):
        m = re.search(
            r'(?:make|create|add|write|new)\s+(?:a\s+)?note\s+(?:called|named|titled|about|saying|:)?\s*(.+)',
            query, re.IGNORECASE,
        )
        title = m.group(1).strip().strip('"\'') if m else query.strip()
        return create_note(title)

    # default: recent
    return read_recent()
