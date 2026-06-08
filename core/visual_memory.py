"""
core/visual_memory.py — eLo AI visual memory world.

Reads the interaction store and organises it into a spatial cluster graph:
    clusters   — groups of related ideas (like islands)
    bridges    — weighted connections between clusters (like bridges)
    positions  — 2D coordinates for visual layout

The output is renderer-agnostic. Any visual layer can consume it:
    terminal tree    — text output, works now
    2D canvas        — tkinter/pygame rendering (Phase 5)
    3D world         — islands in space (long-term)
    Unity scene      — bridged via JSON

eLo never picks the visual representation.
It outputs semantic structure. The renderer picks the metaphor.

Usage:
    from core.visual_memory import build_world, render_terminal

    world = build_world(project="sugarcore_arc")
    print(render_terminal(world))
"""

import re
from collections import Counter, defaultdict


# ── concept-to-cluster label map ──────────────────────────────────────────────
# Maps memory concept groups to human-readable cluster names.

_CONCEPT_LABELS: dict = {
    "creation":    "Building",
    "narrative":   "Story",
    "identity":    "Identity",
    "emotion":     "Feeling",
    "imagination": "Ideas",
    "technical":   "Technical",
}

# ── visual hints (for renderers) ──────────────────────────────────────────────

_SIZE_HINTS = ["island_small", "island_medium", "island_large", "island_hub"]


def _size_hint(count: int) -> str:
    if count <= 2:   return "island_small"
    if count <= 5:   return "island_medium"
    if count <= 10:  return "island_large"
    return "island_hub"


# ── layout engine (force-directed, pure Python) ───────────────────────────────

def _layout(cluster_ids: list, bridges: list) -> dict:
    """
    Assign 2D positions to clusters using a simplified spring layout.
    Returns {cluster_id: {"x": float, "y": float}}.
    Pure Python — no dependencies.
    """
    import math

    n = len(cluster_ids)
    if n == 0:
        return {}

    # initialise in a circle
    positions = {}
    for i, cid in enumerate(cluster_ids):
        angle = (2 * math.pi * i) / n
        positions[cid] = [math.cos(angle) * 3.0, math.sin(angle) * 3.0]

    # simple spring relaxation — 20 iterations
    for _ in range(20):
        forces = {cid: [0.0, 0.0] for cid in cluster_ids}

        # repulsion between all pairs
        for i, a in enumerate(cluster_ids):
            for b in cluster_ids[i+1:]:
                dx = positions[a][0] - positions[b][0]
                dy = positions[a][1] - positions[b][1]
                dist = math.sqrt(dx*dx + dy*dy) or 0.01
                force = 2.0 / (dist * dist)
                forces[a][0] += force * dx / dist
                forces[a][1] += force * dy / dist
                forces[b][0] -= force * dx / dist
                forces[b][1] -= force * dy / dist

        # attraction along bridges
        for bridge in bridges:
            a = bridge["from"]
            b = bridge["to"]
            if a not in positions or b not in positions:
                continue
            dx = positions[b][0] - positions[a][0]
            dy = positions[b][1] - positions[a][1]
            dist = math.sqrt(dx*dx + dy*dy) or 0.01
            strength = bridge.get("strength", 0.5)
            force = dist * strength * 0.3
            forces[a][0] += force * dx / dist
            forces[a][1] += force * dy / dist
            forces[b][0] -= force * dx / dist
            forces[b][1] -= force * dy / dist

        for cid in cluster_ids:
            positions[cid][0] += forces[cid][0] * 0.1
            positions[cid][1] += forces[cid][1] * 0.1

    return {cid: {"x": round(pos[0], 2), "y": round(pos[1], 2)}
            for cid, pos in positions.items()}


# ── world builder ─────────────────────────────────────────────────────────────

def build_world(
    project: str = None,
    interactions: list = None,
    world_name: str = None,
) -> dict:
    """
    Build a visual memory world from stored interactions.

    Args:
        project:      Filter to a specific project namespace. None = all.
        interactions: Pass a list directly (for testing). None = load from store.
        world_name:   Override the world title.

    Returns:
        {
            world_name: str
            total_items: int
            clusters: [
                {
                    id, label, count, dominant_concept,
                    position, visual_hint, items: [...]
                }
            ]
            bridges: [
                {from, to, strength, label}
            ]
        }
    """
    if interactions is None:
        try:
            from core.memory_engine import _load_store
            interactions = _load_store()
        except Exception:
            interactions = []

    # filter by project
    if project:
        interactions = [r for r in interactions if r.get("project_tag") == project]

    if not interactions:
        return {
            "world_name":  world_name or "Empty Memory World",
            "total_items": 0,
            "clusters":    [],
            "bridges":     [],
        }

    # group by dominant concept
    concept_groups: dict = defaultdict(list)
    for record in interactions:
        concepts = record.get("concepts", [])
        if concepts:
            dominant = concepts[0]   # first concept is primary
        else:
            dominant = "uncategorised"
        concept_groups[dominant].append(record)

    # build clusters
    clusters = []
    for concept, records in concept_groups.items():
        label = _CONCEPT_LABELS.get(concept, concept.title())
        cid   = f"{project or 'all'}_{concept}" if project else concept
        items = [
            {
                "text":      r.get("user", "")[:80],
                "timestamp": r.get("timestamp", "")[:10],
                "mode":      r.get("mode", "?"),
                "tags":      r.get("concepts", []),
            }
            for r in records[-10:]   # cap at last 10 per cluster
        ]
        clusters.append({
            "id":               cid,
            "label":            label,
            "count":            len(records),
            "dominant_concept": concept,
            "visual_hint":      _size_hint(len(records)),
            "items":            items,
        })

    # sort clusters largest first
    clusters.sort(key=lambda c: c["count"], reverse=True)

    # build bridges from concept co-occurrence
    concept_pair_counts: Counter = Counter()
    for record in interactions:
        concepts = record.get("concepts", [])
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                key = tuple(sorted([c1, c2]))
                concept_pair_counts[key] += 1

    bridges = []
    cluster_by_concept = {c["dominant_concept"]: c["id"] for c in clusters}
    for (c1, c2), count in concept_pair_counts.most_common(10):
        id1 = cluster_by_concept.get(c1)
        id2 = cluster_by_concept.get(c2)
        if id1 and id2 and id1 != id2:
            bridges.append({
                "from":     id1,
                "to":       id2,
                "strength": min(1.0, round(count / max(concept_pair_counts.values()), 2)),
                "label":    f"{_CONCEPT_LABELS.get(c1, c1)} ↔ {_CONCEPT_LABELS.get(c2, c2)}",
            })

    # calculate layout
    cluster_ids = [c["id"] for c in clusters]
    positions   = _layout(cluster_ids, bridges)
    for cluster in clusters:
        cluster["position"] = positions.get(cluster["id"], {"x": 0.0, "y": 0.0})

    title = world_name or f"eLo Memory — {project or 'All Projects'}"

    return {
        "world_name":  title,
        "total_items": len(interactions),
        "clusters":    clusters,
        "bridges":     bridges,
    }


# ── terminal renderer ──────────────────────────────────────────────────────────

def render_terminal(world: dict) -> str:
    """
    Render a memory world as a readable terminal tree.
    No dependencies. Works immediately.
    """
    lines = [
        f"  {world['world_name']}",
        f"  {world['total_items']} interactions",
        "",
    ]

    clusters = world.get("clusters", [])
    if not clusters:
        lines.append("  No memory yet.")
        return "\n".join(lines)

    for cluster in clusters:
        count  = cluster["count"]
        label  = cluster["label"]
        hint   = cluster["visual_hint"]

        _ICONS = {
            "island_small":  "◦",
            "island_medium": "●",
            "island_large":  "◉",
            "island_hub":    "★",
        }
        icon = _ICONS.get(hint, "·")
        lines.append(f"  {icon}  {label} ({count})")

        # show last 2 items as preview
        for item in cluster["items"][-2:]:
            text = item["text"][:55] + ("…" if len(item["text"]) > 55 else "")
            lines.append(f"       {item['timestamp']}  {text}")
        lines.append("")

    # show strongest bridges
    bridges = world.get("bridges", [])[:4]
    if bridges:
        lines.append("  Connections:")
        for bridge in bridges:
            lines.append(f"    {bridge['label']}  (strength {bridge['strength']})")

    return "\n".join(lines)


# ── eLo voice for the memory world ────────────────────────────────────────────

def world_to_elo_speech(world: dict) -> str:
    """
    Convert a memory world into eLo's spoken description.
    This is what eLo says when asked to organise memory visually.
    """
    clusters = world.get("clusters", [])
    total    = world.get("total_items", 0)

    if not clusters:
        return "Memory is empty. Start a conversation and it will grow."

    cluster_lines = "  ·  ".join(
        f"{c['label']} ({c['count']})" for c in clusters[:6]
    )
    response = f"You have {total} interactions here.\n\nGrouped: {cluster_lines}"

    bridges = world.get("bridges", [])
    if bridges:
        strongest = bridges[0]
        response += f"\n\nStrongest connection: {strongest['label']}."

    return response
