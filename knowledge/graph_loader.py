"""
knowledge/graph_loader.py — eLo OS Connection Engine.

WO-CANON-XXIV (Ruling A): one canonical graph (relationships/world_graph.json).
Retrieval contract: results carry confidence + kind + evidence[] + score.
Ranked by score DESC. Unknown facts return empty list — never backfilled from LLM.

Reads world_graph.json, concepts.json, and viewpoints.json.
Before each response, finds:
  1. Entities mentioned in user input (ranked by keyword match count)
  2. Relationships between those entities
  3. Relevant viewpoint
  4. Relevant concept

Returns a compact context string for injection into the system prompt.
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
    """Return entities whose keywords appear in the lowercased input, with match count."""
    _load_all()
    t = text.lower()
    matched = []
    for e in _graph.get("entities", []):
        score = sum(1 for k in e.get("keywords", []) if k in t)
        if score > 0:
            matched.append((score, e))
    matched.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in matched]


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


# ── ranked structured retrieval ────────────────────────────────────────────────

def retrieve(user_input: str, top_k: int = 3) -> list[dict]:
    """
    Return up to top_k ranked knowledge items for user_input.

    Each result dict carries:
      label:      display label (entity name or relationship pair)
      content:    description / connection text
      confidence: epistemic confidence 0.0–1.0 (graph field or default 1.0)
      kind:       entity type or "relationship"
      evidence:   list of source strings (graph field or [])
      score:      keyword match count (salience rank)

    Returns [] when no graph knowledge matches — never backfills from LLM.
    """
    _load_all()
    if not _graph:
        return []

    text     = user_input.strip().lower()
    entities = _find_entities(text)
    results: list[dict] = []

    # entity hits
    for e in entities:
        kw_score = sum(1 for k in e.get("keywords", []) if k in text)
        results.append({
            "label":      e.get("name", e.get("id", "")),
            "content":    e.get("description", ""),
            "confidence": float(e.get("confidence", 1.0)),
            "kind":       e.get("type", "entity"),
            "evidence":   list(e.get("evidence", [])),
            "score":      kw_score,
        })

    # relationship hits (from/to entity in matched set)
    if entities:
        entity_ids = {e["id"] for e in entities}
        for r in _graph.get("relationships", []):
            if r.get("from") in entity_ids or r.get("to") in entity_ids:
                from_name = next((e["name"] for e in _graph["entities"] if e["id"] == r["from"]), r["from"])
                to_name   = next((e["name"] for e in _graph["entities"] if e["id"] == r["to"]),   r["to"])
                results.append({
                    "label":      f"{from_name} → {to_name}",
                    "content":    r.get("connection", r.get("meaning", "")),
                    "confidence": float(r.get("confidence", 1.0)),
                    "kind":       "relationship",
                    "evidence":   list(r.get("evidence", [])),
                    "score":      float(r.get("strength", 0.5)),
                })

    # rank: entity match count DESC, then confidence DESC
    results.sort(key=lambda x: (x["score"], x["confidence"]), reverse=True)
    return results[:top_k]


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
