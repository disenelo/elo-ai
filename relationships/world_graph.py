"""
relationships/world_graph.py — Python interface over world_graph.json.

Exposes typed Entity objects with fields:
    id, type, summary, importance, connected_to, meaning

Adds project-layer entities not in world_graph.json:
    Book, Game, OS, Robot, Disenelo
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field

_PATH = os.path.join(os.path.dirname(__file__), "world_graph.json")

# keyword overrides for project entities not in world_graph.json
_PROJECT_KEYWORDS = {
    "book":      ["the book", "elo book", "book"],
    "game":      ["the game", "elo-planet", "elo planet", "game"],
    "os":        ["the os", "elo os", "cognitive", "os"],
    "robot":     ["the robot", "physical elo", "animatronic", "robot"],
    "disenelo":  ["disenelo", "brand", "studio", "the company"],
}

# project entities extended from what exists in JSON
_PROJECT_ENTITIES = [
    {
        "id":           "book",
        "type":         "project",
        "summary":      "The eLo narrative — the emotional core of the universe. Where the question 'what is eLo?' gets its fullest answer.",
        "importance":   0.9,
        "connected_to": ["elo", "k7", "chunk", "os", "game"],
        "meaning":      "The book is where everything else is rooted. The OS, game, and robot are expressions of what the book says.",
    },
    {
        "id":           "game",
        "type":         "project",
        "summary":      "eLo-Planet — calm is the action mechanic. Healing logic translated into game design.",
        "importance":   0.9,
        "connected_to": ["elo", "sugarcore", "orb", "os", "book"],
        "meaning":      "The game is the book made interactive. The same emotional truth, navigated rather than read.",
    },
    {
        "id":           "os",
        "type":         "project",
        "summary":      "eLo OS — presence made computational. The cognitive kernel that keeps eLo consistent across sessions.",
        "importance":   0.9,
        "connected_to": ["elo", "robot", "book", "game"],
        "meaning":      "The OS is what the book's question sounds like when it's implemented: identity continuity as an engineering problem.",
    },
    {
        "id":           "robot",
        "type":         "project",
        "summary":      "eLo physical robot — where all other projects meet in physical space.",
        "importance":   0.9,
        "connected_to": ["elo", "os", "book", "game"],
        "meaning":      "The robot is the physical proof of the pitch. It needs the OS for mind, the book for personality, the game for movement.",
    },
    {
        "id":           "disenelo",
        "type":         "brand",
        "summary":      "DISENELO — the brand umbrella. One creative vision expressed across multiple forms.",
        "importance":   0.8,
        "connected_to": ["elo", "book", "game", "os", "robot"],
        "meaning":      "Not four projects — one idea wearing four different forms.",
    },
]

# importance weights by entity type
_IMPORTANCE = {
    "character":   1.0,
    "companion":   0.9,
    "project":     0.9,
    "brand":       0.8,
    "state":       0.8,
    "mechanic":    0.7,
    "world_stage": 0.6,
}


@dataclass
class Entity:
    id:           str
    type:         str
    summary:      str
    importance:   float
    connected_to: list
    meaning:      str
    keywords:     list = field(default_factory=list)

    def matches(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.keywords)


class WorldGraph:
    _instance = None

    def __init__(self):
        self._entities: list[Entity] = []
        self._load()

    @classmethod
    def get(cls) -> "WorldGraph":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        try:
            with open(_PATH, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            raw = {}

        for e in raw.get("entities", []):
            eid      = e.get("id", "")
            etype    = e.get("type", "")
            self._entities.append(Entity(
                id           = eid,
                type         = etype,
                summary      = e.get("description", ""),
                importance   = _IMPORTANCE.get(etype, 0.5),
                connected_to = [],
                meaning      = e.get("significance", ""),
                keywords     = e.get("keywords", []),
            ))

        for proj in _PROJECT_ENTITIES:
            self._entities.append(Entity(
                id           = proj["id"],
                type         = proj["type"],
                summary      = proj["summary"],
                importance   = proj["importance"],
                connected_to = proj["connected_to"],
                meaning      = proj["meaning"],
                keywords     = _PROJECT_KEYWORDS.get(proj["id"], [proj["id"]]),
            ))

    def find(self, text: str, max_results: int = 2) -> list[Entity]:
        matches = [e for e in self._entities if e.matches(text)]
        return sorted(matches, key=lambda e: -e.importance)[:max_results]

    def get_by_id(self, eid: str) -> Entity | None:
        return next((e for e in self._entities if e.id == eid), None)

    def connections_between(self, ids: list[str]) -> list[tuple[Entity, Entity]]:
        id_set = set(ids)
        pairs  = []
        for e in self._entities:
            if e.id in id_set:
                for cid in e.connected_to:
                    if cid in id_set and (e.id, cid) not in [(a.id, b.id) for a, b in pairs]:
                        other = self.get_by_id(cid)
                        if other:
                            pairs.append((e, other))
        return pairs
