"""
faculties/dream/symbol_history.py — Recurring symbol tracking.

WO-DREAM-ENGINE-001 PHASE 10.

Symbols that appear across >= 3 dreams become eLo's personal dream lexicon.

    {
      "mechanical_bird": {
        "first_appeared": "2026-09-15",
        "count": 4,
        "evolution": [
          {"dream": "001", "meaning": "freedom"},
          {"dream": "002", "meaning": "escape"},
          {"dream": "003", "meaning": "invention"},
          {"dream": "004", "meaning": "transformation"}
        ],
        "current_association": "transformation"
      }
    }

The rule the WO sets, enforced here: **meanings are OBSERVED from context,
not hardcoded.** This module never decides what a symbol means. It records
what the dream that produced it was about, and lets the association drift as
later dreams reuse the symbol. A lexicon nobody wrote.

Recurrence is what makes a symbol eLo's rather than a one-off image, so it is
counted across dreams, never within one. `dream_work.build_dream_world()`
accepts a `recurring_symbol` — that is where a promoted symbol re-enters the
next dream, and where the loop closes.

Persistence is a plain JSON file. No LLM, no network, no server.py.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field as _field
from datetime import date
from pathlib import Path
from typing import Iterable

# Appearances before a symbol counts as part of the lexicon (WO PHASE 10).
RECURRENCE_THRESHOLD = 3

# How many evolution entries to keep per symbol. The association drifts, so
# the tail matters more than the head — but the head is never dropped, since
# "first_appeared" is part of the record.
MAX_EVOLUTION = 24

_HISTORY_PATH = Path(__file__).parent.parent.parent / "self" / "dream_symbols.json"

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def normalise(symbol: str) -> str:
    """
    Canonical key for a symbol. "Mechanical birds" and "mechanical_bird" are
    the same entry in the lexicon, otherwise recurrence never accumulates.
    """
    slug = _SLUG_RE.sub("_", str(symbol or "").strip().lower()).strip("_")
    # crude singularisation — "birds" and "bird" must not split the count
    if len(slug) > 4 and slug.endswith("s") and not slug.endswith("ss"):
        slug = slug[:-1]
    return slug


@dataclass
class SymbolRecord:
    """One symbol in eLo's dream lexicon."""
    symbol: str                 # storage key — normalised, deduplicated
    first_appeared: str
    count: int = 0
    evolution: list[dict] = _field(default_factory=list)
    display: str = ""           # original wording as first observed

    @property
    def current_association(self) -> str:
        """The most recent observed meaning. Empty if never observed."""
        for entry in reversed(self.evolution):
            if entry.get("meaning"):
                return str(entry["meaning"])
        return ""

    @property
    def is_recurring(self) -> bool:
        return self.count >= RECURRENCE_THRESHOLD

    @property
    def display_name(self) -> str:
        """
        How the symbol should READ. The storage key is singularised so
        "birds" and "bird" share one entry; that must not reach a prompt as
        "unlit window" when the dream actually saw "unlit windows".
        """
        return self.display or self.symbol.replace("_", " ")

    def as_dict(self) -> dict:
        # The four WO PHASE 10 keys, plus `display` (additive — the WO's
        # schema has no place to keep the original wording).
        return {
            "first_appeared": self.first_appeared,
            "count": self.count,
            "evolution": list(self.evolution),
            "current_association": self.current_association,
            "display": self.display_name,
        }

    @classmethod
    def from_dict(cls, symbol: str, data: dict) -> "SymbolRecord":
        return cls(
            symbol=symbol,
            first_appeared=str(data.get("first_appeared", "")),
            count=int(data.get("count", 0) or 0),
            evolution=list(data.get("evolution", []) or []),
            display=str(data.get("display", "") or ""),
        )


# ── Persistence ────────────────────────────────────────────────────────────────

def load(path: Path | str | None = None) -> dict[str, SymbolRecord]:
    """Read the lexicon. A missing or corrupt file is an empty lexicon."""
    target = Path(path) if path else _HISTORY_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, SymbolRecord] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            out[key] = SymbolRecord.from_dict(key, value)
    return out


def save(records: dict[str, SymbolRecord], path: Path | str | None = None) -> bool:
    """
    Write the lexicon atomically. Best-effort — a failed write must never
    break a dream.
    """
    target = Path(path) if path else _HISTORY_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        payload = {k: v.as_dict() for k, v in sorted(records.items())}
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(target)
        return True
    except Exception:
        return False


# ── Recording ──────────────────────────────────────────────────────────────────

def record_dream(
    dream_id: str,
    symbols: Iterable[str],
    *,
    meaning: str = "",
    when: str | None = None,
    path: Path | str | None = None,
) -> dict[str, SymbolRecord]:
    """
    Record the symbols one dream produced.

    dream_id — the dream's id; one dream increments a symbol at most once,
               so a symbol repeated across scenes is still a single appearance.
    symbols  — the symbols that dream carried.
    meaning  — what that dream was ABOUT, observed by the caller from the
               dream's own content (its insight, tension or dominant emotion).
               Never inferred here; this module has no opinion about meaning.

    Returns the updated lexicon.
    """
    records = load(path)
    today = when or date.today().isoformat()

    seen: set[str] = set()
    for raw_symbol in symbols or []:
        key = normalise(raw_symbol)
        if not key or key in seen:
            continue        # one dream, one appearance
        seen.add(key)

        record = records.get(key)
        if record is None:
            record = SymbolRecord(
                symbol=key, first_appeared=today,
                display=str(raw_symbol).strip(),
            )
            records[key] = record

        # A re-run of the same dream must not inflate the count.
        if any(e.get("dream") == dream_id for e in record.evolution):
            continue

        record.count += 1
        record.evolution.append({
            "dream": dream_id,
            "meaning": str(meaning or ""),
            "date": today,
        })
        if len(record.evolution) > MAX_EVOLUTION:
            # keep the first (first_appeared provenance) plus the recent tail
            record.evolution = record.evolution[:1] + record.evolution[-(MAX_EVOLUTION - 1):]

    save(records, path)
    return records


# ── Reading ────────────────────────────────────────────────────────────────────

def recurring(path: Path | str | None = None) -> dict[str, SymbolRecord]:
    """Symbols that have appeared in >= RECURRENCE_THRESHOLD dreams."""
    return {k: v for k, v in load(path).items() if v.is_recurring}


def current_association(symbol: str, path: Path | str | None = None) -> str:
    """What this symbol most recently meant. Empty if unknown."""
    record = load(path).get(normalise(symbol))
    return record.current_association if record else ""


def most_established(path: Path | str | None = None) -> str:
    """
    The strongest symbol in the lexicon, for the visual engine to inject as
    an apex-layer overlay (WO section 32) and for the next Dream World to
    carry. Empty string when nothing recurs yet — it builds over time, it is
    not seeded.
    """
    candidates = recurring(path)
    if not candidates:
        return ""
    strongest = max(candidates.values(), key=lambda r: (r.count, r.first_appeared))
    # Display form, not the storage slug — this string goes straight into an
    # image prompt ("a_machine_breathing recur throughout" reads as a variable
    # name, not a dream). normalise() round-trips it back to the same key.
    return strongest.display_name


def lexicon_summary(path: Path | str | None = None) -> list[dict]:
    """The lexicon as plain dicts, strongest first. For journals and review."""
    records = sorted(load(path).values(), key=lambda r: r.count, reverse=True)
    return [
        {
            "symbol": r.symbol,
            "display": r.display_name,
            "count": r.count,
            "first_appeared": r.first_appeared,
            "current_association": r.current_association,
            "recurring": r.is_recurring,
        }
        for r in records
    ]
