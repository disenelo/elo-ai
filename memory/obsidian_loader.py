"""
memory/obsidian_loader.py — The single bridge between Obsidian vault and eLo AI OS.

THIS IS THE ONLY FILE ALLOWED TO READ obsidian_vault/.

No other module may import from or read obsidian_vault/ directly.
The kernel receives processed output only — it never knows where memory came from.

Architecture:

    obsidian_vault/      ← pure markdown data (never imported, never executed)
          ↓
    memory/obsidian_loader.py   ← this file (only bridge)
          ↓
    MemoryPack (dict)    ← processed output
          ↓
    kernel / backends    ← receive {memory, state, context} — source-agnostic

The kernel contract:
    kernel.decide_response(raw_context)
    raw_context contains memory signals — never vault file paths or markdown.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

# ── vault location ─────────────────────────────────────────────────────────────
# The vault lives at elo-ai/obsidian_vault/ — relative to project root.
# Override with ELO_VAULT_PATH environment variable if needed.

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VAULT   = os.environ.get("ELO_VAULT_PATH", os.path.join(_ROOT, "obsidian_vault"))
_CACHE   = os.path.join(_ROOT, "memory", "obsidian_cache.json")


# ── frontmatter parser ─────────────────────────────────────────────────────────

def _parse_frontmatter(content: str) -> tuple:
    """Extract YAML frontmatter and body. Returns ({meta}, body_str)."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    fm, body = content[3:end].strip(), content[end + 4:].strip()
    meta = {}
    for line in fm.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
        elif v.lower() in ("true", "false"):
            meta[k] = v.lower() == "true"
        else:
            meta[k] = v.strip("\"'")
    return meta, body


def _first_paragraph(body: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line[:200]
    return ""


def _extract_links(body: str) -> list:
    return re.findall(r"\[\[([^\]]+)\]\]", body)


# ── vault scanner ─────────────────────────────────────────────────────────────
# Only this function touches the obsidian_vault directory.

def _scan_vault() -> list:
    """
    Walk obsidian_vault/ and parse all typed memory notes.
    Returns a list of note dicts.

    This is the ONLY function in the codebase that reads obsidian_vault/.
    """
    if not os.path.exists(_VAULT):
        return []

    notes = []
    for dirpath, dirnames, filenames in os.walk(_VAULT):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                meta, body = _parse_frontmatter(content)
                if not meta.get("type"):
                    continue  # skip untyped notes
                notes.append({
                    "title":   fname[:-3],
                    "folder":  os.path.relpath(dirpath, _VAULT),
                    "type":    meta.get("type",    ""),
                    "domain":  meta.get("domain",  ""),
                    "tags":    meta.get("tags",    []),
                    "version": str(meta.get("version", "0.1")),
                    "summary": _first_paragraph(body),
                    "links":   _extract_links(body),
                })
            except Exception:
                continue  # bad file — skip silently
    return notes


# ── memory pack builder ────────────────────────────────────────────────────────

def _build_pack(notes: list) -> dict:
    """
    Convert raw note list into a structured MemoryPack.
    This is what the rest of the system receives — never raw markdown.
    """
    all_tags  = sorted({t for n in notes for t in n["tags"]})
    entities  = sorted([n["title"] for n in notes if n["domain"] in ("universe", "identity")])
    by_domain: dict = {}
    for n in notes:
        by_domain.setdefault(n["domain"], []).append(n)

    # context block — what gets injected into the system prompt
    context_lines = []
    for domain in ("identity", "universe", "ai-os", "game", "robot"):
        domain_notes = by_domain.get(domain, [])
        if domain_notes:
            context_lines.append(f"[{domain.upper()}]")
            for note in domain_notes[:6]:
                if note["summary"]:
                    context_lines.append(f"**{note['title']}**: {note['summary']}")
            context_lines.append("")

    return {
        "generated":     datetime.now().isoformat(),
        "vault":         _VAULT,
        "note_count":    len(notes),
        "entity_count":  len(entities),
        "tag_count":     len(all_tags),
        "entities":      entities,
        "tags":          all_tags,
        "domains":       {d: len(n) for d, n in by_domain.items()},
        "context_block": "\n".join(context_lines).strip(),
        "notes":         notes,
    }


# ── public API ─────────────────────────────────────────────────────────────────

def load(use_cache: bool = True) -> dict:
    """
    Load the vault and return a MemoryPack.

    The MemoryPack is what every other system receives.
    Nothing outside this file ever reads obsidian_vault/ directly.

    Args:
        use_cache: If True, return cached pack if it exists and is recent.

    Returns:
        MemoryPack dict with: context_block, entities, tags, notes, domains.
        Returns minimal empty pack if vault is unavailable.
    """
    if use_cache and os.path.exists(_CACHE):
        try:
            with open(_CACHE) as f:
                return json.load(f)
        except Exception:
            pass  # cache corrupt — rebuild

    notes = _scan_vault()
    pack  = _build_pack(notes) if notes else _empty_pack()

    # write cache
    try:
        with open(_CACHE, "w") as f:
            json.dump(pack, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # cache write failure is non-fatal

    return pack


def get_context_block(max_chars: int = 2000) -> str:
    """
    Return the memory context block for system prompt injection.
    This is the primary interface for the personality/prompt pipeline.
    """
    pack = load()
    return pack.get("context_block", "")[:max_chars]


def invalidate_cache():
    """Force a fresh vault scan on next load()."""
    if os.path.exists(_CACHE):
        try:
            os.remove(_CACHE)
        except Exception:
            pass


def _empty_pack() -> dict:
    return {
        "generated":     datetime.now().isoformat(),
        "vault":         _VAULT,
        "note_count":    0,
        "entity_count":  0,
        "tag_count":     0,
        "entities":      [],
        "tags":          [],
        "domains":       {},
        "context_block": "",
        "notes":         [],
    }


# ── CLI (for STEP 5 testing) ───────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="eLo Obsidian vault loader")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--output",   default=None)
    args = parser.parse_args()

    if args.no_cache:
        invalidate_cache()

    pack = load(use_cache=not args.no_cache)

    print(f"Loaded notes:    {pack['note_count']}")
    print(f"Entities:        {pack['entity_count']}")
    print(f"Tags:            {pack['tag_count']}")
    print(f"Domains:         {pack['domains']}")
    print()
    print("Memory pack generated")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(pack, f, indent=2)
        print(f"Written to: {args.output}")
    else:
        print()
        print("--- Context block preview ---")
        print(pack["context_block"][:600])
