"""
tools/vault_writer.py — eLo saves notes/decisions to the Obsidian vault.

This is the "learns" half of two-way creation.
When the user says "remember this", "save this", "note that down" —
eLo writes a new note into the vault so it becomes part of long-term memory.

Save destination (in priority order):
    1. ELO_VAULT_PATH env var — user's real Obsidian app vault
    2. elo-ai/obsidian_vault/07 Journal/ — eLo's internal vault

After writing, the obsidian_loader cache is invalidated so the new note
is visible to eLo immediately in subsequent turns.

Triggered by:
    "remember this"
    "save this to memory" / "save this to vault"
    "note that down" / "make a note"
    "add this to my vault"
    "keep this" / "store this"
    "remember that [content]"
    "save the decision that [content]"
"""

from __future__ import annotations
import os
import re
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SAVE_TRIGGERS = [
    r"\bremember\s+(?:this|that|it)\b",
    r"\bsave\s+(?:this|that|it)\b",
    r"\bnote\s+(?:this|that|it|down)\b",
    r"\bmake\s+a\s+note\b",
    r"\badd\s+(?:this|that)\s+to\s+(?:my\s+)?(?:vault|memory|notes?|obsidian)\b",
    r"\bkeep\s+(?:this|that)\b",
    r"\bstore\s+(?:this|that)\b",
    r"\bwrite\s+(?:this|that)\s+down\b",
    r"\bsave\s+(?:to\s+)?(?:my\s+)?(?:vault|memory|notes?|obsidian)\b",
    r"\bput\s+(?:this|that)\s+in\s+(?:my\s+)?(?:vault|memory|notes?)\b",
    r"\bremember\s+(?:we\s+)?decided\b",
    r"\bremember\s+(?:the\s+)?(?:fact|decision|rule|note)\s+that\b",
]


def is_save_intent(text: str) -> bool:
    t = text.lower()
    return any(re.search(pat, t) for pat in _SAVE_TRIGGERS)


def _extract_content(query: str) -> str:
    """Pull the content to save from the query — strip the save trigger phrase."""
    t = query.strip()
    for pat in _SAVE_TRIGGERS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE).strip()
    t = re.sub(r'^[:\-–—,\.]+\s*', "", t).strip()
    return t or query.strip()


def _make_title(content: str) -> str:
    """Generate a short file-safe title from the content."""
    words = re.sub(r"[^\w\s]", "", content).split()[:6]
    title = " ".join(w.capitalize() for w in words) or "Note"
    return title


def _vault_journal_path() -> str:
    """Return the path to write new notes — real Obsidian vault or internal."""
    real_vault = os.environ.get("ELO_VAULT_PATH", "").strip()
    if real_vault and os.path.isdir(real_vault):
        journal = os.path.join(real_vault, "Journal")
        os.makedirs(journal, exist_ok=True)
        return journal

    # Internal vault
    internal = os.path.join(_ROOT, "obsidian_vault", "07 Journal")
    os.makedirs(internal, exist_ok=True)
    return internal


_current_session_id: str = ""


def set_session_id(session_id: str) -> None:
    """AC-GR12: set the session_id written into note frontmatter."""
    global _current_session_id
    _current_session_id = session_id


def _note_content(title: str, content: str, raw_query: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""---
type: memory
domain: journal
tags: [user-note, saved, {today}]
version: 0.1
created: {today}
epistemic_class: generated
session_id: {_current_session_id}
---

# {title}

{content}

---
*Saved by eLo during conversation.*
"""


def agent(query: str) -> str:
    content = _extract_content(query)
    if not content or len(content) < 3:
        raise ValueError("nothing to save — content too short")

    title       = _make_title(content)
    journal_dir = _vault_journal_path()
    timestamp   = datetime.now().strftime("%Y%m%d-%H%M")
    safe_title  = re.sub(r'[^\w\s\-]', '', title).strip()[:50]
    filename    = f"{timestamp} {safe_title}.md"
    filepath    = os.path.join(journal_dir, filename)

    note = _note_content(title, content, query)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(note)

    # Invalidate vault cache so eLo sees this note immediately
    try:
        from memory.obsidian_loader import invalidate_cache
        invalidate_cache()
    except Exception:
        pass

    vault_name = "Obsidian vault" if os.environ.get("ELO_VAULT_PATH") else "vault"
    return f"Saved to {vault_name}: '{title}'"
