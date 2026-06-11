"""
knowledge/graph_loader.py — eLo OS Connection Engine.

Reads world_graph.json, concepts.json, and viewpoints.json.
Before each response, finds:
  1. Entities mentioned in user input
  2. Relationships between those entities
  3. Relevant viewpoint
  4. Relevant concept

Returns a compact context string for injection into the system prompt.
This enriches the prompt with relationship understanding and eLo's perspective —
without touching memory, routing, or architecture.
"""

from __future__ import annotations
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_GRAPH_PATH      = os.path.join(_ROOT, "relationships", "world_graph.json")
_CONCEPTS_PATH   = os.path.join(_ROOT, "relationships", "concepts.json")
_VIEWPOINTS_PATH = os.path.join(_ROOT, "knowledge",     "viewpoints.json")

# Module-level cache — loaded once per process
_graph:      dict = {}
_concepts:   dict = {}
_viewpoints: dict = {}


def _load_all():
    global _graph, _concepts, _viewpoints
    if _graph:
        return
    try:
        with open(_GRAPH_PATH,      encoding="utf-8") as f: _graph      = json.load(f)
        with open(_CONCEPTS_PATH,   encoding="utf-8") as f: _concepts   = json.load(f)
        with open(_VIEWPOINTS_PATH, encoding="utf-8") as f: _viewpoints = json.load(f)
    except Exception:
        _graph = _concepts = _viewpoints = {}


# ── entity matching ────────────────────────────────────────────────────────────

def _find_entities(text: str) -> list[dict]:
    """Return entities whose keywords appear in the lowercased input."""
    _load_all()
    t = text.lower()
    return [
        e for e in _graph.get("entities", [])
        if any(k in t for k in e.get("keywords", []))
    ]


def _find_relationships(entity_ids: list[str]) -> list[dict]:
    """Return relationships where both ends are in the matched entity set."""
    _load_all()
    id_set = set(entity_ids)
    return [
        r for r in _graph.get("relationships", [])
        if r.get("from") in id_set or r.get("to") in id_set
    ]


# ── concept matching ───────────────────────────────────────────────────────────

def _find_concept(text: str) -> dict | None:
    """Return the most relevant concept for this input."""
    _load_all()
    t = text.lower()
    for concept in _concepts.get("concepts", []):
        if any(k in t for k in concept.get("related", []) + [concept.get("id", ""), concept.get("name", "").lower()]):
            return concept
    return None


# ── viewpoint matching ─────────────────────────────────────────────────────────

def _find_viewpoint(text: str) -> dict | None:
    """Return the most relevant viewpoint for this input."""
    _load_all()
    t = text.lower()
    for vp in _viewpoints.get("viewpoints", []):
        if any(k in t for k in vp.get("keywords", [])):
            return vp
    return None


# ── context assembly ───────────────────────────────────────────────────────────

def build_context(user_input: str, max_chars: int = 800) -> str:
    """
    Build a compact context string from the knowledge graph.

    Returns up to max_chars of relevant:
      - Entity descriptions and relationships
      - A relevant viewpoint
      - A relevant concept connection

    Returns empty string if nothing relevant found.
    """
    _load_all()
    if not _graph and not _viewpoints:
        return ""

    text      = user_input.strip()
    entities  = _find_entities(text)
    rels      = _find_relationships([e["id"] for e in entities]) if entities else []
    viewpoint = _find_viewpoint(text)
    concept   = _find_concept(text)

    lines: list[str] = []

    # entity context
    if entities:
        for e in entities[:2]:   # max 2 entities
            lines.append(f"{e['name']}: {e['description']}")

    # relationship context — most relevant connection
    if rels:
        r = rels[0]
        # find both entity names
        from_name = next((e["name"] for e in _graph.get("entities", []) if e["id"] == r["from"]), r["from"])
        to_name   = next((e["name"] for e in _graph.get("entities", []) if e["id"] == r["to"]),   r["to"])
        lines.append(f"Connection ({from_name} → {to_name}): {r['connection']}")

    # viewpoint
    if viewpoint:
        lines.append(f"Perspective: {viewpoint['viewpoint']}")

    # concept (only if no viewpoint or there's room)
    if concept and not viewpoint:
        lines.append(f"Concept note: {concept['emotional_significance']}")

    if not lines:
        return ""

    context = "\n".join(lines)
    return context[:max_chars]
