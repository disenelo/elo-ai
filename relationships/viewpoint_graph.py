"""
relationships/viewpoint_graph.py — Python interface over knowledge/viewpoints.json.

Exposes typed Viewpoint objects with fields:
    topic, perspective, extended, keywords
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field

_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge", "viewpoints.json")


@dataclass
class Viewpoint:
    topic:      str
    perspective: str
    extended:   str
    keywords:   list = field(default_factory=list)

    def matches(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.keywords)


class ViewpointGraph:
    _instance = None

    def __init__(self):
        self._viewpoints: list[Viewpoint] = []
        self._load()

    @classmethod
    def get(cls) -> "ViewpointGraph":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        try:
            with open(_PATH, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return

        for v in raw.get("viewpoints", []):
            self._viewpoints.append(Viewpoint(
                topic       = v.get("topic", ""),
                perspective = v.get("viewpoint", ""),
                extended    = v.get("extended", ""),
                keywords    = v.get("keywords", []),
            ))

    def find(self, text: str) -> Viewpoint | None:
        for v in self._viewpoints:
            if v.matches(text):
                return v
        return None

    def all(self) -> list[Viewpoint]:
        return list(self._viewpoints)
