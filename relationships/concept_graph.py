"""
relationships/concept_graph.py — Python interface over concepts.json.

Exposes typed Concept objects with fields:
    id, name, supports, conflicts, creates, emotion
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field

_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "relationships", "concepts.json")


@dataclass
class Concept:
    id:       str
    name:     str
    supports: list   # things this concept strengthens (from "related")
    conflicts: list  # things this concept is in tension with (from "opposites")
    creates:  list   # things this concept tends to produce (from "supporting")
    emotion:  str    # emotional significance (from "emotional_significance")
    keywords: list = field(default_factory=list)

    def matches(self, text: str) -> bool:
        t = text.lower()
        name_match = self.name.lower() in t or self.id in t
        kw_match   = any(k.lower() in t for k in self.supports[:4])
        return name_match or kw_match


class ConceptGraph:
    _instance = None

    def __init__(self):
        self._concepts: list[Concept] = []
        self._load()

    @classmethod
    def get(cls) -> "ConceptGraph":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        try:
            with open(_PATH, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return

        for c in raw.get("concepts", []):
            self._concepts.append(Concept(
                id        = c.get("id", ""),
                name      = c.get("name", ""),
                supports  = c.get("related", []),
                conflicts = c.get("opposites", []),
                creates   = c.get("supporting", []),
                emotion   = c.get("emotional_significance", ""),
                keywords  = [c.get("id", ""), c.get("name", "").lower()]
                             + c.get("related", [])[:3],
            ))

    def find(self, text: str) -> Concept | None:
        t = text.lower()
        for c in self._concepts:
            if any(k in t for k in c.keywords):
                return c
        return None

    def all(self) -> list[Concept]:
        return list(self._concepts)
