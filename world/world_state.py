"""
world/world_state.py — eLo Planet persistent world state.

Converts memory snapshots into a spatial node graph for eLo Planet.
No kernel logic. No AI. Only: read memory → build graph → persist.

Structure:
    WorldNode  — a spatial entity in the world (concept, project, universe entity)
    WorldEdge  — a relationship between two nodes
    WorldState — the full graph at a point in time

Data sources (read-only):
    core/memory_engine.py  — interaction history, concept pairs, entity counts
    core/visual_memory.py  — cluster groupings (reused as a starting point)

Entry points:
    build_world_state(project=None)  → WorldState dict (from current memory)
    update_world_state(state, event) → updated state (from a new event dict)
    save_world_state(state, path)    → write to JSON
    load_world_state(path)           → read from JSON
    node_by_id(state, node_id)       → find a node by id

The world state is Unity-consumable JSON.
Positions are 3D floats in world-space units.
"""

import json
import math
import os
import re
from collections import Counter
from datetime import datetime


# ── node types ────────────────────────────────────────────────────────────────

NODE_TYPES = (
    "universe_entity",   # eLo, Chunk, K-7, Core, Sugarcore
    "concept",           # creation, narrative, identity, emotion, imagination, technical
    "project",           # disenelo_universe, sugarcore_arc, orb_device, elo_ai_core
    "interaction",       # a notable interaction cluster (high-weight memory)
)

# Universe entities with fixed world positions (landmarks)
_ENTITY_POSITIONS: dict = {
    "eLo":       {"x":  0.0, "y": 10.0, "z":  0.0},   # centre island, elevated
    "Core":      {"x":  0.0, "y":  8.0, "z":  5.0},   # near eLo
    "Chunk":     {"x": -8.0, "y":  2.0, "z":  0.0},   # west
    "K-7":       {"x":  8.0, "y":  2.0, "z":  0.0},   # east
    "Sugarcore": {"x":  0.0, "y": -2.0, "z":-10.0},   # south, lower (distortion)
}

# eLo universe entity definitions (copied from memory — no import cycle)
_ENTITY_DEFINITIONS: dict = {
    "eLo":       "creative explorer intelligence — self / companion / navigator",
    "Chunk":     "wholeness and reconstruction — identity integration / modular body",
    "K-7":       "emotional expression through behaviour — loyalty / spirit guide",
    "Core":      "navigation and memory system — guidance / Core Orb device",
    "Sugarcore": "imbalance and distortion system — overload state",
}

_CONCEPT_COLOUR: dict = {
    "creation":    "#dcdcaa",
    "narrative":   "#c586c0",
    "identity":    "#9cdcfe",
    "emotion":     "#ce9178",
    "imagination": "#c586c0",
    "technical":   "#4ec9b0",
}


# ── layout ────────────────────────────────────────────────────────────────────

def _radial_position(index: int, total: int, radius: float, y: float = 0.0) -> dict:
    """Place node at angle on a circle of given radius."""
    if total <= 1:
        return {"x": 0.0, "y": y, "z": 0.0}
    angle = (2 * math.pi * index) / total
    return {
        "x": round(math.cos(angle) * radius, 2),
        "y": round(y, 2),
        "z": round(math.sin(angle) * radius, 2),
    }


# ── node / edge builders ──────────────────────────────────────────────────────

def _make_node(
    node_id:    str,
    label:      str,
    node_type:  str,
    position:   dict,
    weight:     float = 1.0,
    properties: dict  = None,
) -> dict:
    return {
        "id":         node_id,
        "label":      label,
        "type":       node_type,
        "position":   position,
        "weight":     round(weight, 2),
        "properties": properties or {},
    }


def _make_edge(
    from_id:    str,
    to_id:      str,
    edge_type:  str,
    strength:   float = 0.5,
    label:      str   = "",
) -> dict:
    return {
        "from":     from_id,
        "to":       to_id,
        "type":     edge_type,     # associated / belongs_to / references / co_occurs
        "strength": round(strength, 2),
        "label":    label,
    }


# ── world state builder ───────────────────────────────────────────────────────

def build_world_state(project: str = None) -> dict:
    """
    Build a world state graph from current memory.

    Reads: core/memory_engine._load_store(), concept pairs, entity counts.
    No kernel calls. No AI.

    Args:
        project: Optional project namespace filter.
                 None = all interactions.

    Returns:
        WorldState dict with keys: generated, project, nodes, edges, meta.
    """
    from core.memory_engine import (_load_store, _detect_concepts,
                                    _UNIVERSE_ENTITIES, _build_concept_pairs)

    interactions = _load_store()
    if project:
        interactions = [r for r in interactions if r.get("project_tag") == project]

    nodes = []
    edges = []
    node_ids = set()

    # ── 1: universe entity nodes (fixed positions, always present) ────────────
    for entity, definition in _ENTITY_DEFINITIONS.items():
        pos   = _ENTITY_POSITIONS.get(entity, {"x": 0.0, "y": 0.0, "z": 0.0})
        nid   = f"entity_{entity.lower().replace('-','_')}"
        count = sum(
            1 for r in interactions
            if re.search(r"\b" + re.escape(entity.lower()) + r"\b",
                         r.get("user", "").lower())
        )
        nodes.append(_make_node(
            nid, entity, "universe_entity", pos,
            weight=max(1.0, float(count)),
            properties={"definition": definition, "mention_count": count},
        ))
        node_ids.add(nid)

    # ── 2: concept nodes (radial layout around centre) ────────────────────────
    concept_counts: Counter = Counter(
        c for r in interactions for c in r.get("concepts", [])
    )
    concepts = [c for c, _ in concept_counts.most_common(6)]
    for i, concept in enumerate(concepts):
        nid = f"concept_{concept}"
        pos = _radial_position(i, len(concepts), radius=15.0, y=0.0)
        nodes.append(_make_node(
            nid, concept.title(), "concept", pos,
            weight=float(concept_counts[concept]),
            properties={
                "mention_count": concept_counts[concept],
                "colour": _CONCEPT_COLOUR.get(concept, "#888888"),
            },
        ))
        node_ids.add(nid)

    # ── 3: project nodes (outer ring) ─────────────────────────────────────────
    project_counts: Counter = Counter(
        r.get("project_tag", "elo_core") for r in interactions
    )
    projects = list(project_counts.keys())
    for i, proj in enumerate(projects):
        nid = f"project_{proj}"
        pos = _radial_position(i, len(projects), radius=25.0, y=-3.0)
        nodes.append(_make_node(
            nid, proj.replace("_", " ").title(), "project", pos,
            weight=float(project_counts[proj]),
            properties={"interaction_count": project_counts[proj]},
        ))
        node_ids.add(nid)

    # ── 4: concept co-occurrence edges ────────────────────────────────────────
    pairs = _build_concept_pairs(interactions)
    max_pair_count = 1
    pair_counts: Counter = Counter()
    for r in interactions:
        cs = r.get("concepts", [])
        for j, c1 in enumerate(cs):
            for c2 in cs[j+1:]:
                k = tuple(sorted([c1, c2]))
                pair_counts[k] += 1
    if pair_counts:
        max_pair_count = pair_counts.most_common(1)[0][1]

    for (c1, c2), count in pair_counts.most_common(12):
        id1, id2 = f"concept_{c1}", f"concept_{c2}"
        if id1 in node_ids and id2 in node_ids:
            strength = count / max_pair_count
            edges.append(_make_edge(id1, id2, "co_occurs", strength,
                                    label=f"{count}×"))

    # ── 5: entity → concept edges (entity appears with concept) ──────────────
    for entity in _ENTITY_DEFINITIONS:
        eid = f"entity_{entity.lower().replace('-','_')}"
        for r in interactions:
            if re.search(r"\b" + re.escape(entity.lower()) + r"\b",
                         r.get("user", "").lower()):
                for concept in r.get("concepts", []):
                    cid = f"concept_{concept}"
                    if cid in node_ids and eid in node_ids:
                        existing = next(
                            (e for e in edges
                             if e["from"] == eid and e["to"] == cid), None
                        )
                        if existing:
                            existing["strength"] = min(1.0, existing["strength"] + 0.1)
                        else:
                            edges.append(_make_edge(eid, cid, "references", 0.4))

    # ── 6: project → concept edges ────────────────────────────────────────────
    for proj in projects:
        pid = f"project_{proj}"
        proj_interactions = [r for r in interactions if r.get("project_tag") == proj]
        proj_concepts = Counter(c for r in proj_interactions for c in r.get("concepts", []))
        for concept, cnt in proj_concepts.most_common(3):
            cid = f"concept_{concept}"
            if cid in node_ids:
                edges.append(_make_edge(pid, cid, "belongs_to",
                                        min(1.0, cnt / max(1, len(proj_interactions)))))

    return {
        "generated":  datetime.utcnow().isoformat() + "Z",
        "project":    project or "all",
        "nodes":      nodes,
        "edges":      edges,
        "meta": {
            "total_interactions": len(interactions),
            "node_count":         len(nodes),
            "edge_count":         len(edges),
        },
    }


# ── update functions ──────────────────────────────────────────────────────────

def update_world_state(state: dict, event: dict) -> dict:
    """
    Merge a new kernel event (from dashboard/event_bus.py) into the world state.

    Increments node weights for mentioned entities and concepts.
    Adds new edges if new co-occurrences appear.
    Does NOT rebuild the full graph — only applies the delta.

    Args:
        state: Existing WorldState dict (from build_world_state or load_world_state).
        event: A dashboard event dict (keys: input, classification, memory_snapshot, …)

    Returns:
        Updated WorldState dict (same reference, mutated in-place for efficiency).
    """
    from core.memory_engine import _detect_concepts

    user_input = event.get("input", "")
    cls        = event.get("classification", {})
    entities   = cls.get("entities", [])
    concepts   = _detect_concepts(user_input)

    # index nodes for fast lookup
    node_by_id_map = {n["id"]: n for n in state.get("nodes", [])}

    # increment entity weights
    for entity in entities:
        nid = f"entity_{entity.lower().replace('-','_')}"
        if nid in node_by_id_map:
            node_by_id_map[nid]["weight"] = round(
                node_by_id_map[nid]["weight"] + 0.5, 2
            )
            props = node_by_id_map[nid].setdefault("properties", {})
            props["mention_count"] = props.get("mention_count", 0) + 1

    # increment concept weights
    for concept in concepts:
        nid = f"concept_{concept}"
        if nid in node_by_id_map:
            node_by_id_map[nid]["weight"] = round(
                node_by_id_map[nid]["weight"] + 0.3, 2
            )

    # increment existing edge strengths for active pairs
    edge_index = {(e["from"], e["to"]): e for e in state.get("edges", [])}
    for entity in entities:
        eid = f"entity_{entity.lower().replace('-','_')}"
        for concept in concepts:
            cid = f"concept_{concept}"
            key = (eid, cid)
            if key in edge_index:
                edge_index[key]["strength"] = min(
                    1.0, round(edge_index[key]["strength"] + 0.05, 2)
                )

    state["meta"]["total_interactions"] = (
        state["meta"].get("total_interactions", 0) + 1
    )
    return state


def node_by_id(state: dict, node_id: str) -> dict:
    """Return a node by its id, or None if not found."""
    for node in state.get("nodes", []):
        if node["id"] == node_id:
            return node
    return None


def nodes_by_type(state: dict, node_type: str) -> list:
    """Return all nodes of a given type."""
    return [n for n in state.get("nodes", []) if n["type"] == node_type]


def edges_for_node(state: dict, node_id: str) -> list:
    """Return all edges connected to the given node id."""
    return [e for e in state.get("edges", [])
            if e["from"] == node_id or e["to"] == node_id]


# ── persistence ───────────────────────────────────────────────────────────────

def save_world_state(state: dict, path: str = "world/world_state.json"):
    """Write the world state to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return path


def load_world_state(path: str = "world/world_state.json") -> dict:
    """Load a world state from a JSON file. Returns empty state if file absent."""
    if not os.path.exists(path):
        return {"generated": None, "project": "all",
                "nodes": [], "edges": [], "meta": {}}
    with open(path) as f:
        return json.load(f)
