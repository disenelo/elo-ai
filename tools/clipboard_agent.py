"""
tools/clipboard_agent.py — macOS clipboard agent for eLo OS.

Reads and writes the system clipboard via pbpaste/pbcopy.
Returns data strings for LLM context injection — no character voice.
"""
from __future__ import annotations

import re
import subprocess


def is_clipboard_intent(text: str) -> bool:
    t = text.lower()
    return "clipboard" in t or "what did i copy" in t or "what's copied" in t


def read() -> str:
    """Return clipboard text, capped at 1500 chars, or an empty-signal string."""
    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        text = result.stdout
        if not text:
            return "Clipboard is empty."
        if len(text) > 1500:
            text = text[:1500]
        return f"Clipboard contents: {text}"
    except Exception as e:
        return f"Clipboard read error: {e}"


def write(text: str) -> None:
    """Write text to the clipboard via pbcopy."""
    proc = subprocess.run(["pbcopy"], input=text, text=True, timeout=5)
    proc.check_returncode()


def agent(query: str) -> str:
    """
    Main entry point for tool_router.
    Detects read vs explicit-write intent and returns a data string.
    """
    q = query.lower()

    # Explicit quoted write: copy "..." to clipboard / copy '...' to clipboard
    m = re.search(r"""copy\s+['"](.+?)['"]\s+to\s+clipboard""", q, re.IGNORECASE)
    if m:
        quoted = m.group(1)
        try:
            write(quoted)
            return f"Copied to clipboard: '{quoted}'"
        except Exception as e:
            return f"Clipboard write error: {e}"

    # Write-intent without explicit text — defer to server.py
    if any(p in q for p in ["copy that", "put that on clipboard", "clipboard that"]):
        return "[CLIPBOARD_WRITE_INTENT]"

    # Default: read
    return read()
