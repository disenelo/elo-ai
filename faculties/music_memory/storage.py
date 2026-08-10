"""
faculties/music_memory/storage.py — Music memory persistence.

Two-tier storage:
    1. Local library  — faculties/music_memory/data/library.json
       Fast read/write. All tracks. Source of truth for the faculty.

    2. Vault (tiered) — obsidian_vault/09 Memory/
       Only significant memories (sig >= 0.45) get vault records.
       Uses existing vault_layer.write_memory() so music memories
       appear alongside all other eLo memories in Obsidian.

Safety rules (per spec):
    - Never deletes source data
    - Append-only writes to library.json (update by key, never remove)
    - Vault writes are additive
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Callable

from faculties.music_memory.models import MusicMemory

_HERE   = os.path.dirname(os.path.abspath(__file__))
_LIB    = os.path.join(_HERE, "data", "library.json")
_SIG_VAULT_THRESHOLD = 0.45   # minimum significance to write to vault


def _ensure_lib() -> None:
    os.makedirs(os.path.dirname(_LIB), exist_ok=True)
    if not os.path.exists(_LIB):
        with open(_LIB, "w", encoding="utf-8") as f:
            json.dump({}, f)


def load_all() -> dict[str, MusicMemory]:
    """Load the full library. Returns dict keyed by fact.key()."""
    _ensure_lib()
    with open(_LIB, encoding="utf-8") as f:
        raw = json.load(f)
    return {k: MusicMemory.from_dict(v) for k, v in raw.items()}


def save(memory: MusicMemory) -> None:
    """
    Upsert a music memory into the local library.
    Updates last_updated timestamp. Never removes existing records.
    """
    from dataclasses import replace
    _ensure_lib()

    memory = replace(memory, last_updated=datetime.now().isoformat(timespec="seconds"))

    library = {}
    with open(_LIB, encoding="utf-8") as f:
        library = json.load(f)

    library[memory.fact.key()] = memory.to_dict()

    with open(_LIB, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2, ensure_ascii=False)


def save_to_vault(memory: MusicMemory) -> str | None:
    """
    Write a significant music memory to the vault.
    Returns the spot code, or None if below threshold.
    """
    if memory.significance < _SIG_VAULT_THRESHOLD:
        return None

    try:
        from faculties.music_memory.analyser import vault_weight
        from memory.memory_faculty import MemoryFaculty as _MemFac, MemoryCandidate as _MemCand
    except ImportError:
        return None

    f = memory.fact
    i = memory.interpretation

    summary_parts = [f"{f.artist} — {f.title}"]
    if i.notes:
        summary_parts.append(i.notes[:120])
    if i.creative_projects:
        summary_parts.append(f"Connected to: {', '.join(i.creative_projects[:3])}")
    summary = ". ".join(summary_parts)

    deep_lines = [
        f"# {f.artist} — {f.title}",
        "",
        f"**Sources:** {', '.join(f.sources) if f.sources else 'unknown'}",
        f"**Play count:** {f.play_count}",
        f"**Discovered:** {f.discovered_date or 'unknown'} ({f.discovered_context})",
        f"**Emotion:** {i.emotion}",
        f"**Mood tags:** {', '.join(i.mood_tags) if i.mood_tags else '—'}",
        f"**Life period:** {i.life_period or '—'}",
        f"**Creative projects:** {', '.join(i.creative_projects) if i.creative_projects else '—'}",
        "",
    ]
    if i.notes:
        deep_lines += ["**Notes:**", i.notes, ""]
    if i.memories:
        deep_lines += ["**Memories:**"] + [f"- {m}" for m in i.memories] + [""]

    tags = ("music",) + ((i.emotion,) if i.emotion != "neutral" else ())

    _decision = _MemFac().submit(_MemCand(
        source_faculty="music",
        content="\n".join(deep_lines),
        proposed_type="emotional",
        proposed_weight=vault_weight(memory.significance),
        significance=memory.significance,   # already >= _SIG_VAULT_THRESHOLD (0.45)
        project="david",
        summary=summary[:200],
        tags=tags,
    ))
    return _decision.get("spot")


def load_by_artist(artist: str) -> list[MusicMemory]:
    lib = load_all()
    a = artist.lower().strip()
    return [m for m in lib.values() if m.fact.artist.lower() == a]


def load_by_significance(min_sig: float = 0.45) -> list[MusicMemory]:
    lib = load_all()
    return sorted(
        [m for m in lib.values() if m.significance >= min_sig],
        key=lambda m: m.significance,
        reverse=True,
    )


def load_by_project(project_name: str) -> list[MusicMemory]:
    lib = load_all()
    p = project_name.lower()
    return [
        m for m in lib.values()
        if any(p in proj.lower() for proj in m.interpretation.creative_projects)
    ]


def library_stats() -> dict:
    """Quick stats for debug/memory-status reporting."""
    lib = load_all()
    total = len(lib)
    significant = sum(1 for m in lib.values() if m.significance >= _SIG_VAULT_THRESHOLD)
    artists = len({m.fact.artist for m in lib.values()})
    return {"total": total, "significant": significant, "artists": artists}
