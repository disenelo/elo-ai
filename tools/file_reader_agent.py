"""
tools/file_reader_agent.py — eLo file reading agent.

Reads a file by path and injects its content as [CONTEXT] so eLo can
respond about what's actually in the file — not guess at it.

Triggered by:
    "read this file: ~/path/to/file"
    "look at /path/to/script.cs"
    "what's in ~/Desktop/brief.md"
    "open ~/eLo-Planet/Assets/Scripts/PlayerController.cs"
    "check this: /path/to/file.py"

Safety:
    - Only reads text files (checks extension)
    - Max 4000 chars to stay within context budget
    - Never reads .env, private keys, or binary files
    - Path must exist and be a file (not a directory)
"""

from __future__ import annotations
import os
import re
import logging

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

_MAX_CHARS = 4000

_TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".cs", ".js", ".ts", ".json", ".yaml", ".yml",
    ".toml", ".cfg", ".ini", ".sh", ".swift", ".html", ".css", ".xml",
    ".blend", ".log", ".csv", ".env.example",
}

_BLOCKED = {".env", ".pem", ".key", ".p12", ".pfx", ".cer", ".secret"}

_PATH_PATTERNS = [
    r'(?:read|open|look\s+at|check|show\s+me|what(?:\'s|\s+is)\s+in|load)\s+(?:this\s+)?(?:file\s+)?["\']?([~/\w\.\-/\\ ]+\.\w+)["\']?',
    r'["\']([~/\w\.\-/\\ ]+\.\w+)["\']',      # quoted path anywhere
    r'([~/][/\w\.\-]+\.\w+)',                  # bare path starting with ~ or /
]


def _extract_path(query: str) -> str:
    for pat in _PATH_PATTERNS:
        m = re.search(pat, query, re.IGNORECASE)
        if m:
            return m.group(1).strip().strip("\"'")
    return ""


def _is_safe(path: str) -> bool:
    _, ext = os.path.splitext(path.lower())
    basename = os.path.basename(path).lower()
    if ext in _BLOCKED or basename == ".env":
        return False
    if ext and ext not in _TEXT_EXTENSIONS:
        return False
    return True


def agent(query: str) -> str:
    raw_path = _extract_path(query)
    if not raw_path:
        raise ValueError("no file path found in query")

    path = os.path.expanduser(raw_path.strip())

    if not _is_safe(path):
        raise ValueError(f"file type not allowed: {path}")

    if not os.path.isfile(path):
        raise ValueError(f"file not found: {path}")

    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read(_MAX_CHARS)

    truncated = len(content) == _MAX_CHARS
    name = os.path.basename(path)
    result = f"Contents of {name}:\n\n{content}"
    if truncated:
        result += f"\n\n[Truncated at {_MAX_CHARS} chars — file continues]"
    return result


def is_file_read_intent(text: str) -> bool:
    t = text.lower()
    has_trigger = any(w in t for w in ["read ", "open ", "look at ", "check ", "show me ", "what's in ", "load "])
    has_path    = bool(re.search(r'[~/][\w/\.\-]+\.\w+', t) or re.search(r'["\'][^"\']+\.\w+["\']', t))
    return has_trigger and has_path
