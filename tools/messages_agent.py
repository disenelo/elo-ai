"""
tools/messages_agent.py — iMessage send agent for eLo OS.

Requires macOS Messages.app with an active iMessage account.
Sending is a two-step confirm flow — agent() returns PENDING_MESSAGE,
server.py intercepts "send it" / "cancel" to complete or cancel.

Parsing handled:
    "message David saying come check this out"
    "text Mum that I'll be late"
    "send [name] [message]"
    'send [name] "quoted message"'
"""
from __future__ import annotations

import re
import subprocess
from typing import Optional

_PENDING: Optional[dict] = None


def _run(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10.0,
        )
        return result.stdout.strip()
    except Exception as e:
        return f"error: {e}"


# ── send ───────────────────────────────────────────────────────────────────────

def send_message(contact: str, text: str) -> str:
    c = contact.replace('"', '\\"')
    t = text.replace('"', '\\"')
    script = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{c}" of targetService
            send "{t}" to targetBuddy
        end tell
    '''
    result = _run(script)
    if result.startswith("error"):
        # Try by phone number / email fallback
        script2 = f'''
            tell application "Messages"
                send "{t}" to participant "{c}" of 1st service
            end tell
        '''
        _run(script2)
    return f"Sent to {contact}: '{text}'"


# ── pending plan state ─────────────────────────────────────────────────────────

def has_pending() -> bool:
    return _PENDING is not None


def execute_pending() -> str:
    global _PENDING
    if not _PENDING:
        return "No pending message."
    result = send_message(_PENDING["contact"], _PENDING["text"])
    _PENDING = None
    return result


def cancel_pending() -> None:
    global _PENDING
    _PENDING = None


def get_pending_summary() -> Optional[str]:
    if not _PENDING:
        return None
    return f"to {_PENDING['contact']}: '{_PENDING['text']}'"


# ── intent detection ──────────────────────────────────────────────────────────

def is_messages_intent(text: str) -> bool:
    t = text.lower()
    send_pat = re.search(r'\b(?:send|text|message|imessage)\s+\w', t)
    tell_pat = re.search(r'\btell\s+\w+\s+that\b', t)
    return bool(send_pat or tell_pat)


def is_message_confirm(text: str) -> bool:
    t = text.lower().strip()
    return t in ("send it", "send", "yes send", "do it", "confirm", "go ahead", "yeah send it")


def is_message_cancel(text: str) -> bool:
    t = text.lower().strip()
    return t in ("cancel", "don't send", "nevermind", "stop", "no", "abort", "forget it")


# ── parsing ───────────────────────────────────────────────────────────────────

def _parse(query: str) -> Optional[tuple[str, str]]:
    """Return (contact, message_text) or None if parsing fails."""

    # Pattern 1: send/text/message [contact] "[quoted text]"
    m = re.search(
        r'(?:send|text|message|imessage)\s+(.+?)\s+"(.+?)"',
        query, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Pattern 2: send/text/message [contact] saying/that [text]
    m = re.search(
        r'(?:send|text|message|imessage)\s+(.+?)\s+(?:saying|that|:)\s+(.+)',
        query, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Pattern 3: tell [contact] that [text]
    m = re.search(r'tell\s+(.+?)\s+that\s+(.+)', query, re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Pattern 4: send/text/message [contact] [rest as message — 3+ words after contact]
    m = re.search(
        r'(?:send|text|message)\s+([\w\s]{2,30}?)\s+(?!saying|that|to\b)(.{10,})',
        query, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Pattern 5: "assign [task] to [contact]" / "give [contact] the [task]"
    m = re.search(r'assign\s+(.+?)\s+to\s+([\w\s]{1,30}?)(?:\s*$|[,.])', query, re.IGNORECASE)
    if m:
        task = m.group(1).strip().rstrip(" .,")
        contact = m.group(2).strip()
        return contact, f"You've been assigned: {task}"

    m = re.search(r'give\s+([\w\s]{1,20}?)\s+the\s+(.+)', query, re.IGNORECASE)
    if m:
        contact = m.group(1).strip()
        task = m.group(2).strip().rstrip(" .,")
        return contact, f"You've been assigned: {task}"

    return None


# ── main entry ────────────────────────────────────────────────────────────────

def agent(query: str) -> str:
    global _PENDING

    parsed = _parse(query)
    if not parsed:
        return "[MESSAGE: Couldn't parse contact or message text — try: 'message David saying hey come check this' or 'text Mum \"running late\"']"

    contact, text = parsed
    _PENDING = {"contact": contact, "text": text}
    return f"I can send \"{text}\" to {contact}. Say \"send it\" to confirm, or \"cancel\" to skip."
