"""
memory/spg_graph.py — SPG R&D Track: Memory Link Graph prototype.

WO-SPG-RD-002 · R&D only — not wired into spine or Executive.
Gates required before production: G-2 (real-memory applicability) · G-5 (utility).

Graph model:
  Node = a memory/turn entry with significance + embodiment context.
  Edge = a typed associative link between nodes, with weight 0.0–1.0.

Link types (from WO spec):
  temporal            — same session, time-adjacent
  semantic            — similar topic (shared signal tags)
  relational          — same person/entity referenced
  significance_chain  — high-significance event referenced from another
  embodiment_continuity — same context across different surfaces

Auth: WO-SPG-RD-002, David L3 2026-09-05
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterator

_log = logging.getLogger(__name__)

_ROOT = Path(__file__).parent.parent
_SIGNALS_PATH = _ROOT / "data" / "spg_signals.jsonl"
_GRAPH_PATH   = _ROOT / "data" / "spg_graph.json"

# ── Schema ────────────────────────────────────────────────────────────────────


@dataclass
class Node:
    id:           str
    content_hash: str   = ""
    significance: float = 0.0
    embodiment:   str   = "desktop"
    ts:           float = field(default_factory=time.time)


@dataclass
class Edge:
    from_node: str
    to_node:   str
    link_type: str   # temporal | semantic | relational | significance_chain | embodiment_continuity
    weight:    float = 0.5
    evidence:  str   = ""


# ── Graph ─────────────────────────────────────────────────────────────────────


class SPGGraph:
    """In-memory associative graph over memory signals."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    # ── Construction ──────────────────────────────────────────────────────────

    def add_node(self, node: Node) -> None:
        self._nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.from_node in self._nodes and edge.to_node in self._nodes:
            self._edges.append(edge)

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    # ── Query ─────────────────────────────────────────────────────────────────

    def top_linked(self, context_node_id: str, top_n: int = 5) -> list[tuple[str, float]]:
        """
        Return top-N nodes most strongly linked to context_node_id.
        Scoring: sum of edge weights across all edges connecting the node to context_node_id.
        """
        scores: dict[str, float] = {}
        for edge in self._edges:
            other = None
            if edge.from_node == context_node_id:
                other = edge.to_node
            elif edge.to_node == context_node_id:
                other = edge.from_node
            if other:
                scores[other] = scores.get(other, 0.0) + edge.weight
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:top_n]

    # ── Serialise ────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "nodes": [asdict(n) for n in self._nodes.values()],
            "edges": [asdict(e) for e in self._edges],
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
        }

    def save(self, path: Path | None = None) -> None:
        # Resolved at CALL time. It was a default argument, evaluated once
        # when the class is defined, so monkeypatching _GRAPH_PATH did
        # nothing and every caller wrote the live store no matter what a test
        # did. That is how a full suite run came to add 8 nodes to eLo's real
        # memory.
        path = Path(path if path is not None else _GRAPH_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        _log.debug("spg_graph: saved %d nodes, %d edges → %s", self.node_count(), self.edge_count(), path)

    @classmethod
    def load(cls, path: Path | None = None) -> "SPGGraph":
        """Load persisted graph from spg_graph.json. Returns empty graph if absent."""
        path = Path(path if path is not None else _GRAPH_PATH)   # call-time, see save()
        graph = cls()
        if not path.exists():
            return graph
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for nd in data.get("nodes", []):
                graph.add_node(Node(
                    id=nd["id"],
                    content_hash=nd.get("content_hash", ""),
                    significance=nd.get("significance", 0.0),
                    embodiment=nd.get("embodiment", "desktop"),
                    ts=nd.get("ts", 0.0),
                ))
            for ed in data.get("edges", []):
                if ed.get("from_node") and ed.get("to_node"):
                    graph._edges.append(Edge(
                        from_node=ed["from_node"],
                        to_node=ed["to_node"],
                        link_type=ed.get("link_type", "semantic"),
                        weight=float(ed.get("weight", 0.5)),
                        evidence=ed.get("evidence", ""),
                    ))
        except Exception as _e:
            _log.warning("spg_graph: load failed (%s) — using empty graph", _e)
        return graph


# ── Builder ───────────────────────────────────────────────────────────────────


def _iter_signals(path: Path = _SIGNALS_PATH) -> Iterator[dict]:
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def build_graph(signals_path: Path = _SIGNALS_PATH) -> SPGGraph:
    """
    Read spg_signals.jsonl and construct an SPGGraph.

    One node per unique (turn_id, signal_type) pair.
    Edges: temporal (adjacent signals in same turn), significance_chain (sig ≥ 0.6).
    """
    graph = SPGGraph()
    signals = list(_iter_signals(signals_path))

    if not signals:
        _log.info("spg_graph: no signals to process (signals file empty or absent)")
        return graph

    # Create nodes
    for sig in signals:
        turn_id    = sig.get("turn_id", "unknown")
        sig_type   = sig.get("signal_type", "unknown")
        embodiment = sig.get("embodiment", "desktop")
        ts         = sig.get("ts", 0.0)
        raw_sig    = float(sig.get("significance", 0.0))

        node_id = f"{turn_id}:{sig_type}"
        content_hash = hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()[:16]
        graph.add_node(Node(
            id=node_id,
            content_hash=content_hash,
            significance=raw_sig,
            embodiment=embodiment,
            ts=ts,
        ))

    # Create temporal edges (same turn_id, different signal_types)
    by_turn: dict[str, list[str]] = {}
    for sig in signals:
        turn_id  = sig.get("turn_id", "unknown")
        sig_type = sig.get("signal_type", "unknown")
        node_id  = f"{turn_id}:{sig_type}"
        by_turn.setdefault(turn_id, []).append(node_id)

    for turn_id, node_ids in by_turn.items():
        for i in range(len(node_ids) - 1):
            graph.add_edge(Edge(
                from_node=node_ids[i],
                to_node=node_ids[i + 1],
                link_type="temporal",
                weight=0.7,
                evidence="same_turn",
            ))

    # Create significance_chain edges (nodes with significance ≥ 0.6 link to each other)
    high_sig = [n for n in graph._nodes.values() if n.significance >= 0.6]
    for i, n1 in enumerate(high_sig):
        for n2 in high_sig[i + 1:]:
            if n1.id != n2.id:
                weight = min(1.0, (n1.significance + n2.significance) / 2.0)
                graph.add_edge(Edge(
                    from_node=n1.id,
                    to_node=n2.id,
                    link_type="significance_chain",
                    weight=weight,
                    evidence="both_high_significance",
                ))

    # Create embodiment_continuity edges (same signal_type across different embodiments)
    by_signal_type: dict[str, list[str]] = {}
    for sig in signals:
        sig_type = sig.get("signal_type", "unknown")
        turn_id  = sig.get("turn_id", "unknown")
        node_id  = f"{turn_id}:{sig_type}"
        by_signal_type.setdefault(sig_type, []).append((node_id, sig.get("embodiment", "desktop")))

    for sig_type, entries in by_signal_type.items():
        seen_embodiments: set[str] = set()
        for i, (n1_id, emb1) in enumerate(entries):
            for n2_id, emb2 in entries[i + 1:]:
                if emb1 != emb2 and frozenset([emb1, emb2]) not in seen_embodiments:
                    graph.add_edge(Edge(
                        from_node=n1_id,
                        to_node=n2_id,
                        link_type="embodiment_continuity",
                        weight=0.6,
                        evidence=f"same_signal_type_across_{emb1}_{emb2}",
                    ))
                    seen_embodiments.add(frozenset([emb1, emb2]))

    _log.info(
        "spg_graph: built %d nodes, %d edges from %d signals",
        graph.node_count(), graph.edge_count(), len(signals),
    )
    return graph


def build_and_save(
    signals_path: Path = _SIGNALS_PATH,
    graph_path: Path   = _GRAPH_PATH,
) -> SPGGraph:
    """Build graph from signals file and persist snapshot."""
    graph = build_graph(signals_path)
    graph.save(graph_path)
    return graph
