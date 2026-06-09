"""
core/memory_loader.py — Obsidian vault memory loader for eLo AI OS.

Reads markdown files from an Obsidian vault and builds a context block
for injection into the system prompt. No cloud AI required.

Vault path: ELO_VAULT_PATH env var, or defaults to memory/ in project root.

Memory types loaded:
    long_term   — always loaded (priority 1)
    character   — always loaded (priority 1)
    personal    — always loaded (priority 1)
    project     — loaded if topic matches (priority 2)
    world       — loaded if topic matches (priority 2)
    technical   — loaded on request (priority 3)

Note format expected:
    YAML frontmatter with: memory_type, load_priority, active, title, tags
    Markdown body follows the frontmatter block.
"""

from __future__ import annotations

import os
import re
from typing import Optional


_DEFAULT_VAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memory"
)

_VAULT_PATH = os.environ.get("ELO_VAULT_PATH", _DEFAULT_VAULT)


# ── frontmatter parser ─────────────────────────────────────────────────────────

def _parse_frontmatter(content: str) -> tuple:
    """
    Parse YAML-style frontmatter from a markdown file.
    Returns (metadata_dict, body_text).
    Simple parser — handles string, int, bool, and list values.
    """
    if not content.startswith("---"):
        return {}, content

    end = content.find("\n---", 3)
    if end == -1:
        return {}, content

    fm_text = content[3:end].strip()
    body    = content[end + 4:].strip()

    meta = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        # parse list: [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip('"').strip("'")
                     for v in val[1:-1].split(",") if v.strip()]
            meta[key] = items
        # parse bool
        elif val.lower() == "true":
            meta[key] = True
        elif val.lower() == "false":
            meta[key] = False
        # parse int
        elif val.isdigit():
            meta[key] = int(val)
        else:
            meta[key] = val.strip('"').strip("'")

    return meta, body


# ── note scanner ───────────────────────────────────────────────────────────────

class MemoryNote:
    """One parsed memory note from the vault."""

    def __init__(self, path: str, meta: dict, body: str):
        self.path          = path
        self.meta          = meta
        self.body          = body
        self.memory_type   = meta.get("memory_type",  "")
        self.title         = meta.get("title",         os.path.basename(path))
        self.tags          = meta.get("tags",          [])
        self.category      = meta.get("category",      "")
        self.load_priority = int(meta.get("load_priority", 2))
        self.active        = meta.get("active",        True)
        self.confidence    = meta.get("confidence",    "unknown")

    def summary(self, max_chars: int = 400) -> str:
        """Return a compact summary: title + first meaningful paragraph."""
        first_para = ""
        for line in self.body.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                first_para = line
                break
        summary = f"**{self.title}**: {first_para}"
        return summary[:max_chars]

    def full_body(self, max_chars: int = 800) -> str:
        """Return body text up to max_chars."""
        return self.body[:max_chars]


def scan_vault(vault_path: str = None) -> list:
    """
    Scan a vault directory for all active memory notes.
    Returns a list of MemoryNote objects.
    Skips files with active: false.
    """
    root = vault_path or _VAULT_PATH
    if not os.path.exists(root):
        return []

    notes = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                meta, body = _parse_frontmatter(content)
                if not meta.get("memory_type"):
                    continue   # not a memory note — skip
                note = MemoryNote(path, meta, body)
                if note.active:
                    notes.append(note)
            except Exception:
                continue   # malformed file — skip silently

    return notes


# ── topic matching ─────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the","a","an","is","it","in","on","at","to","of","and","or","but",
    "i","my","me","this","that","for","with","be","do","not","was","are"
}


def _extract_topics(user_input: str) -> set:
    """Extract meaningful words from user input for topic matching."""
    words = re.findall(r"\b\w+\b", user_input.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _note_matches(note: MemoryNote, topics: set) -> bool:
    """Return True if any topic word appears in the note's tags or category."""
    note_words = set()
    for tag in note.tags:
        note_words.update(re.findall(r"\w+", tag.lower()))
    note_words.update(re.findall(r"\w+", note.category.lower()))
    note_words.update(re.findall(r"\w+", note.title.lower()))
    return bool(topics & note_words)


# ── context builder ────────────────────────────────────────────────────────────

def _format_section(memory_type: str, notes: list, full_body: bool = False) -> str:
    """Format a group of notes into a memory section string."""
    if not notes:
        return ""

    label = memory_type.replace("_", " ").title()
    lines = [f"[MEMORY: {label}]"]
    for note in notes:
        if full_body:
            lines.append(note.full_body())
        else:
            lines.append(note.summary())
    return "\n".join(lines)


def load_memory(
    vault_path:  str  = None,
    user_input:  str  = "",
    max_chars:   int  = 3000,
    full_body:   bool = False,
) -> str:
    """
    Load memory from the vault and return a context block string.

    Priority 1 notes are always included.
    Priority 2 notes are included if they match the user input topic.
    Priority 3 notes are not loaded automatically.

    Args:
        vault_path:  Path to vault root. Defaults to ELO_VAULT_PATH or memory/.
        user_input:  User's message — used for topic matching.
        max_chars:   Maximum characters in the returned context block.
        full_body:   If True, include full note body (not just summary).

    Returns:
        Memory context string ready for injection into system prompt.
        Empty string if vault is unavailable or empty.
    """
    notes    = scan_vault(vault_path)
    topics   = _extract_topics(user_input)
    sections = []

    # group by memory type
    by_type: dict = {}
    for note in notes:
        by_type.setdefault(note.memory_type, []).append(note)

    # priority 1: always load
    _PRIORITY_1_TYPES = ("long_term", "character", "personal")
    for mtype in _PRIORITY_1_TYPES:
        p1 = [n for n in by_type.get(mtype, []) if n.load_priority == 1]
        if p1:
            sections.append(_format_section(mtype, p1, full_body))

    # priority 2: load if topic matches
    _PRIORITY_2_TYPES = ("project", "world", "technical")
    for mtype in _PRIORITY_2_TYPES:
        p2 = [n for n in by_type.get(mtype, [])
              if n.load_priority == 2 and _note_matches(n, topics)]
        if p2:
            sections.append(_format_section(mtype, p2, full_body))

    result = "\n\n".join(s for s in sections if s)
    return result[:max_chars] if result else ""


def load_memory_section(
    memory_type: str,
    vault_path:  str  = None,
    max_chars:   int  = 1000,
) -> str:
    """
    Load all active notes of a specific memory type.
    Used for on-demand retrieval of a single category.
    """
    notes = [n for n in scan_vault(vault_path) if n.memory_type == memory_type]
    section = _format_section(memory_type, notes, full_body=True)
    return section[:max_chars]
