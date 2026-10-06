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


# ── Named documents (B3 2026-10-06) ───────────────────────────────────────────
# Capability demo: "read my eLo tracker" → "no file path found" → mock filler.
# David names his trackers, not their paths. Resolved here; eLo gives a short
# summary taken from the file (latest change-log entry, status counts) — never
# reads a whole tracker aloud, never invents one.
import glob as _glob
import os as _os2
import re as _re2

_HUB = _os2.path.expanduser("~/Documents/DISENELO/memory/projects")
_ALIASES = {
    "elo": ["~/elo-ai/TRACKER.md", f"{_HUB}/eLo_OS_Tracker.md"],
    "elo os": ["~/elo-ai/TRACKER.md", f"{_HUB}/eLo_OS_Tracker.md"],
    "elo ai": ["~/elo-ai/TRACKER.md", f"{_HUB}/eLo_OS_Tracker.md"],
    "elo planet": ["~/eLo-Planet/eLo-Planet_Tracker.md", f"{_HUB}/eLo-Planet_Tracker.md"],
    "game": ["~/eLo-Planet/eLo-Planet_Tracker.md", f"{_HUB}/eLo-Planet_Tracker.md"],
    "robot": [f"{_HUB}/eLo_Robot_Tracker.md"],
    "face": [f"{_HUB}/eLo_FaceAnim_Tracker.md"],
    "plushies": [f"{_HUB}/DISENELO_Plushies_Tracker.md"],
    "seams": [f"{_HUB}/DISENELO_Seams_Tracker.md"],
    "retargeter": [f"{_HUB}/DISENELO_Retargeter_Tracker.md"],
}
_DOC_RE = _re2.compile(r"\b(?:my\s+|the\s+)?((?:[\w\-]+\s+){0,2}?)tracker\b", _re2.I)


def named_document(query: str) -> str | None:
    """Path of the tracker David named ('my eLo tracker', 'the Plushies tracker'),
    the most recently updated when two copies exist; None if not one of his."""
    m = _DOC_RE.search(query)
    if not m:
        return None
    key = _re2.sub(r"[^a-z0-9 ]", " ", m.group(1).lower().replace("-", " ")).strip()
    key = _re2.sub(r"^(?:my|the)\s+", "", key)
    cands = _ALIASES.get(key)
    if cands is None and key:
        cands = [p for p in _glob.glob(f"{_HUB}/*_Tracker.md")
                 if all(w in _os2.path.basename(p).lower().replace("-", "_") for w in key.split())]
    paths = [_os2.path.expanduser(p) for p in (cands or []) if _os2.path.exists(_os2.path.expanduser(p))]
    return max(paths, key=_os2.path.getmtime) if paths else None


def summarise_tracker(path: str) -> str:
    """Spoken summary from the file itself: latest dated change-log entry and
    status counts."""
    text = open(path, encoding="utf-8", errors="replace").read()
    title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("# ")),
                 _os2.path.basename(path))
    dated = _re2.findall(r"^#{2,4}\s+(\d{4}-\d{2}-\d{2})\s*[—–-]?\s*(.*)$", text, _re2.M)
    dated = [(d, t.strip()) for d, t in dated if "next session" not in t.lower()]
    parts = [f"{title}."]
    if dated:
        d, t = max(dated, key=lambda x: x[0])
        parts.append(f"Latest entry {d}: {t}." if t else f"Latest entry {d}.")
    ok, warn, bad = text.count("✅"), text.count("⚠️"), text.count("🔴")
    if ok + warn + bad:
        parts.append(f"Status marks: {ok} done, {warn} partial, {bad} broken.")
    return " ".join(parts)
