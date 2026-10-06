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

def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _osa(script: str) -> tuple[int, str, str]:
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15.0)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


_NOT_ALLOWED = "macOS hasn't given me permission to use {app} yet"


def resolve_contact(name: str) -> tuple[str, str] | str:
    """(full name, phone-or-email) for a contact name, or a line saying why not.
    B3 2026-10-06: messages went to `buddy "<name>"`, which Messages rarely resolves."""
    n = _esc(name.strip())
    rc, out, err = _osa(f'''
        tell application "Contacts"
            set ps to (every person whose name contains "{n}")
            set res to {{}}
            repeat with p in ps
                set h to ""
                if (count of phones of p) > 0 then
                    set h to value of first phone of p
                else if (count of emails of p) > 0 then
                    set h to value of first email of p
                end if
                set end of res to (name of p) & "\t" & h
            end repeat
            set AppleScript's text item delimiters to "\n"
            return res as text
        end tell
    ''')
    if rc != 0:
        if "-1743" in err or "Not authorised" in err or "Not authorized" in err:
            return _NOT_ALLOWED.format(app="Contacts") + " — so I can't look anyone up."
        return f"I couldn't search your contacts ({err[:60]})."
    rows = [r.split("\t", 1) for r in out.splitlines() if r.strip()]
    rows = [(a, b) for a, b in rows if b]
    if not rows:
        return f"I can't find {name} in your contacts with a number or email."
    exact = [r for r in rows if r[0].lower() == name.strip().lower()]
    if len(exact) == 1 or len(rows) == 1:
        return tuple((exact or rows)[0])
    names = ", ".join(r[0] for r in rows[:4])
    return f"There's more than one {name} in your contacts — {names}. Which one?"


def send_message(contact: str, text: str, handle: str = "") -> str:
    """Send via iMessage to the contact's handle. Says 'Sent' only when Messages
    accepted it. B3 2026-10-06: it said 'Sent to X' whatever happened — osascript
    errors go to stderr, and the code checked stdout."""
    to = _esc(handle or contact)
    rc, _out, err = _osa(f'''
        tell application "Messages"
            set acct to 1st account whose service type = iMessage
            send "{_esc(text)}" to participant "{to}" of acct
        end tell
    ''')
    if rc != 0:
        if "-1743" in err or "Not authorised" in err or "Not authorized" in err:
            raise RuntimeError(_NOT_ALLOWED.format(app="Messages"))
        raise RuntimeError(f"Messages didn't send it ({err[:80]})")
    return f"Sent to {contact}: '{text}'"


# ── pending plan state ─────────────────────────────────────────────────────────

def has_pending() -> bool:
    return _PENDING is not None


def execute_pending() -> str:
    global _PENDING
    if not _PENDING:
        return "No pending message."
    p, _PENDING = _PENDING, None
    try:
        send_message(p["contact"], p["text"], p.get("handle", ""))
        return f"Sent to {p['contact']}."
    except RuntimeError as e:
        return f"Not sent — {e}."


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
    query = re.sub(r"\b(?:send|write)\s+(?:a\s+)?(?:message|text)\s+to\s+", "message ", query, flags=re.I)
    query = re.sub(r"^(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?", "", query.strip(), flags=re.I)

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
    who = resolve_contact(contact)
    if isinstance(who, str):
        return who
    _PENDING = {"contact": who[0], "text": text, "handle": who[1]}
    return f"Send \u201c{text}\u201d to {who[0]}? Say \u201csend it\u201d or \u201ccancel\u201d."


# B3 2026-10-06: a request to message someone, not "send me…" / "text me…".
_REQUEST_RE = re.compile(
    r"^(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
    r"(?:(?:send\s+(?:a\s+)?(?:message|text)\s+to|text|message|imessage)\s+(?!me\b|us\b|you\b)"
    r"|tell\s+(?!me\b|us\b|you\b)\w+\s+that\b)",
    re.IGNORECASE,
)


def is_message_request(text: str) -> bool:
    return bool(_REQUEST_RE.search(text.strip())) and _parse(text) is not None
