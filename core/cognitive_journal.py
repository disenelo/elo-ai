"""
cognitive_journal.py — eLo Cognitive Journal

Pure stdlib module. No external dependencies.
Errors return empty list or empty string — never raise.
"""

from __future__ import annotations

import re
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class JournalEntry:
    date: str                          # ISO date string: YYYY-MM-DD
    entry_type: str                    # conversation | observation | insight | theme | decision | dream | question
    title: str
    project: str = ""
    characters: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    body: str = ""
    linked_notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

_LIST_SEP = "|"


def _entry_to_text(entry: JournalEntry) -> str:
    """Serialise a JournalEntry to the append format used in the journal file."""
    characters = _LIST_SEP.join(entry.characters)
    tags = _LIST_SEP.join(entry.tags)
    linked = _LIST_SEP.join(entry.linked_notes)
    # Escape body newlines so each entry stays on deterministic line boundaries
    body_escaped = entry.body.replace("\\", "\\\\").replace("\n", "\\n")
    return (
        f"DATE={entry.date} "
        f"TYPE={entry.entry_type} "
        f"TITLE={entry.title!r} "
        f"PROJECT={entry.project!r} "
        f"CHARACTERS={characters!r} "
        f"TAGS={tags!r} "
        f"LINKED={linked!r} "
        f"BODY={body_escaped!r}\n"
    )


def _parse_line(line: str) -> JournalEntry | None:
    """Parse a single serialised journal line back into a JournalEntry."""
    try:
        def _extract(key: str) -> str:
            # Match KEY='...' or KEY="..." produced by repr()
            m = re.search(rf"{key}=('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")", line)
            if m:
                return m.group(1)[1:-1]  # strip surrounding quotes
            # Plain (unquoted) token — used for DATE and TYPE
            m2 = re.search(rf"{key}=(\S+)", line)
            return m2.group(1) if m2 else ""

        raw_date = _extract("DATE")
        raw_type = _extract("TYPE")
        title = _extract("TITLE")
        project = _extract("PROJECT")

        chars_raw = _extract("CHARACTERS")
        characters = [c for c in chars_raw.split(_LIST_SEP) if c] if chars_raw else []

        tags_raw = _extract("TAGS")
        tags = [t for t in tags_raw.split(_LIST_SEP) if t] if tags_raw else []

        linked_raw = _extract("LINKED")
        linked = [l for l in linked_raw.split(_LIST_SEP) if l] if linked_raw else []

        body_escaped = _extract("BODY")
        body = body_escaped.replace("\\n", "\n").replace("\\\\", "\\")

        if not raw_date or not raw_type:
            return None

        return JournalEntry(
            date=raw_date,
            entry_type=raw_type,
            title=title,
            project=project,
            characters=characters,
            tags=tags,
            body=body,
            linked_notes=linked,
        )
    except Exception:
        return None


def _read_all_entries(journal_path: str) -> List[JournalEntry]:
    """Read all entries from a journal file. Returns [] on any error."""
    try:
        with open(journal_path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        entries = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            entry = _parse_line(line)
            if entry is not None:
                entries.append(entry)
        return entries
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def append_entry(entry: JournalEntry, journal_path: str) -> str:
    """
    Append a JournalEntry to the journal file.

    Creates the file (and parent directories) if they do not exist.
    Never overwrites existing content.
    Returns the path written to, or empty string on failure.
    """
    try:
        parent = os.path.dirname(journal_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        text = _entry_to_text(entry)
        with open(journal_path, "a", encoding="utf-8") as fh:
            fh.write(text)
        return journal_path
    except Exception:
        return ""


def load_recent_entries(journal_path: str, days: int = 7) -> List[JournalEntry]:
    """
    Return entries from the last N days, most recent first.

    Returns [] on any error.
    """
    try:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        entries = _read_all_entries(journal_path)
        recent = [e for e in entries if e.date >= cutoff]
        # Sort descending by date string (ISO format sorts lexicographically)
        recent.sort(key=lambda e: e.date, reverse=True)
        return recent
    except Exception:
        return []


def build_journal_context(entries: List[JournalEntry], max_chars: int = 1500) -> str:
    """
    Format a list of JournalEntry objects as a context block for the system prompt.

    Format per entry:
        [JOURNAL: YYYY-MM-DD type] Title
         <first line of body or empty>

    Truncates at max_chars. Returns empty string on any error.
    """
    try:
        if not entries:
            return ""

        lines = []
        for e in entries:
            header = f"[JOURNAL: {e.date} {e.entry_type}] {e.title}"
            # Extract first non-empty line of body as the key point
            key_point = ""
            for raw_line in e.body.splitlines():
                stripped = raw_line.strip()
                if stripped:
                    key_point = stripped
                    break
            if key_point:
                lines.append(f"{header}\n {key_point}")
            else:
                lines.append(header)

        block = "\n".join(lines)
        if len(block) > max_chars:
            block = block[:max_chars].rsplit("\n", 1)[0]
        return block
    except Exception:
        return ""


def find_by_project(journal_path: str, project: str) -> List[JournalEntry]:
    """
    Return all entries whose project field matches (case-insensitive).

    Returns [] on any error or no match.
    """
    try:
        needle = project.strip().lower()
        entries = _read_all_entries(journal_path)
        return [e for e in entries if e.project.strip().lower() == needle]
    except Exception:
        return []
