"""
memory/long_term_reader.py — Long-Term Memory Document Retrieval

Reads all active long-term memory documents from memory/long_term/*.md
and injects them into the system prompt as a [LONG-TERM MEMORY] block.

These are not rolling conversation facts — they are stable, versioned
identity and constraint documents that must always be on the live turn path.

Current documents:
  - elo-is-not-an-assistant.md  (load_priority=1, category=identity)
  - kernel-is-frozen.md         (load_priority=1, category=constraint)

Format: YAML frontmatter (--- ... ---) followed by markdown body.
Filter: active: true and load_priority >= 1.
Sort:   by load_priority ascending (1 = most critical, loaded first).

Never raises — fail-quiet so the turn still proceeds.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import List, Optional

_log = logging.getLogger(__name__)

_ROOT      = Path(__file__).parent.parent
_LT_DIR    = Path(__file__).parent / "long_term"

# Minimum load_priority to include (1 = always include)
_MIN_PRIORITY = 1


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Split YAML frontmatter from body. Returns (meta_dict, body_text).
    If no frontmatter, returns ({}, full_text).
    Simple key: value parser — no PyYAML dependency.
    """
    if not text.startswith("---"):
        return {}, text

    end_idx = text.find("---", 3)
    if end_idx == -1:
        return {}, text

    fm_block = text[3:end_idx].strip()
    body     = text[end_idx + 3:].strip()

    meta: dict = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()

    return meta, body


def load_long_term_docs(lt_dir: Optional[Path] = None) -> List[dict]:
    """
    Read all active long-term memory docs from memory/long_term/.
    Returns list of dicts sorted by load_priority ascending.
    Never raises.
    """
    path = lt_dir or _LT_DIR
    docs: List[dict] = []
    try:
        if not Path(path).exists():
            return docs
        for fpath in sorted(Path(path).glob("*.md")):
            try:
                raw = fpath.read_text(encoding="utf-8")
                meta, body = _parse_frontmatter(raw)
                active   = str(meta.get("active", "true")).lower() in ("true", "yes", "1")
                priority = int(meta.get("load_priority", "1"))
                if not active or priority < _MIN_PRIORITY:
                    continue
                docs.append({
                    "file":     fpath.name,
                    "title":    meta.get("title", fpath.stem),
                    "category": meta.get("category", "general"),
                    "priority": priority,
                    "body":     body.strip(),
                })
            except Exception as exc:
                _log.warning("long_term_reader: skipped %s — %s", fpath.name, exc)
    except Exception as exc:
        _log.warning("long_term_reader: load failed (non-fatal): %s", exc)

    docs.sort(key=lambda d: d["priority"])
    return docs


def long_term_prompt_block(lt_dir: Optional[Path] = None) -> str:
    """
    Build a [LONG-TERM MEMORY] prompt block from active long-term docs.
    Returns "" when no docs exist (non-blocking).
    Never raises.
    """
    try:
        docs = load_long_term_docs(lt_dir=lt_dir)
        if not docs:
            return ""

        lines = ["[LONG-TERM MEMORY — stable identity and constraint documents]"]
        for doc in docs:
            lines.append(f"  [{doc['category'].upper()}] {doc['title']}")
            for body_line in doc["body"].splitlines():
                stripped = body_line.strip()
                if stripped and not stripped.startswith("#"):
                    lines.append(f"    {stripped}")
        return "\n".join(lines)

    except Exception as exc:
        _log.warning("long_term_prompt_block failed (non-fatal): %s", exc)
        return ""
