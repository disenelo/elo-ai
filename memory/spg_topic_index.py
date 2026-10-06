"""
memory/spg_topic_index.py — ROOT-4, the half that makes the graph matter.

The brief's definition of done:

    "David mentions something repeatedly (a pattern). SPG identifies it as
     significant. That significance score CHANGES HOW ELO RETRIEVES AND
     WEIGHTS related memories."

efe3cd3 did the first two sentences: the graph holds 3,321 turns, 13,203
edges, 1,241 distinct significance values, four months deep.

The third was still false, and quietly. spg_faculty.query_spg_entities ranks
entities by the significance of the SPG node belonging to their CLAIMS —
nodes keyed by claim_id. The backfill creates nodes keyed by TURN
("bf-00788-2026-08-13T02:49:33"). Two node populations in one graph, and the
ranker can only see one of them, so filling the graph changed retrieval by
exactly nothing.

This is the join. Semantic edges already carry the topic that linked two
turns ("topic:robot"), so the graph knows, for every recurring topic, which
turns it appears in and how significant those turns were. An entity whose
label is one of those topics can then be ranked by it.

Which makes the brief's sentence literally true: "robot" appears in 239 of
David's turns, those turns carry real significance, and the robot entity now
outranks one mentioned once.

Read-only. Never writes the graph.
"""
from __future__ import annotations

import logging
import re
import threading
import time

_log = logging.getLogger("elo.spg_topic_index")

# Rebuilt at most this often. The graph changes once per claim; rereading
# 13,000 edges on every turn would be the expensive kind of correct.
_TTL_S: float = 120.0

_lock = threading.Lock()
_cache: dict[str, float] = {}
_cache_at: float = 0.0

_TOPIC_RE = re.compile(r"^topic:(.+)$")


def _build() -> dict[str, float]:
    """topic -> the significance of the most significant turn it appears in."""
    try:
        from memory.spg_graph import SPGGraph
        graph = SPGGraph.load()
    except Exception as e:
        _log.warning("spg_topic_index: cannot load graph — %s", e)
        return {}

    nodes = getattr(graph, "_nodes", {}) or {}
    edges = getattr(graph, "_edges", []) or []
    if not nodes or not edges:
        return {}

    out: dict[str, float] = {}
    freq: dict[str, int] = {}
    for e in edges:
        m = _TOPIC_RE.match(str(getattr(e, "evidence", "") or ""))
        if not m:
            continue
        topic = m.group(1).strip().lower()
        if not topic:
            continue
        freq[topic] = freq.get(topic, 0) + 1
        for nid in (getattr(e, "from_node", ""), getattr(e, "to_node", "")):
            n = nodes.get(nid)
            if n is None:
                continue
            sig = float(getattr(n, "significance", 0.0) or 0.0)
            if sig > out.get(topic, 0.0):
                out[topic] = sig

    # Significance alone is too blunt, and the live store shows it plainly:
    # "world" recurs in over a thousand turns, so every entity carrying that
    # word inherited the top score — World Literature Diversity and
    # "Hello, World!" ranked level with eLo robot design constraints. The word
    # recurs; those entities do not.
    #
    # A topic in 50 turns identifies something; a topic in 1,100 identifies
    # almost nothing. So significance is discounted by how indiscriminate the
    # topic is — the same reason IDF exists. Rare-and-significant wins;
    # common-and-significant is still worth something, but not the top.
    # Relative to the RAREST topic, not to the absolute maximum. Against the
    # maximum, a graph where every topic recurs equally discounted all of them
    # by 75% for no reason — caught by the unit tests, where one edge per
    # topic made share 1.0 across the board. If nothing is more
    # indiscriminate than anything else, nothing should be penalised.
    if freq:
        _lo, _hi = min(freq.values()), max(freq.values())
        _span = (_hi - _lo) or 1
        for topic, sig in list(out.items()):
            share = (freq[topic] - _lo) / _span
            out[topic] = round(sig * (1.0 - 0.75 * share), 4)

    _log.info("spg_topic_index: %d recurring topics from %d edges",
              len(out), len(edges))
    return out


def topic_significance(*, force: bool = False) -> dict[str, float]:
    """The index, rebuilt at most every _TTL_S seconds."""
    global _cache, _cache_at
    with _lock:
        if force or not _cache or (time.time() - _cache_at) > _TTL_S:
            _cache = _build()
            _cache_at = time.time()
        return _cache


def score_label(label: str, index: dict[str, float] | None = None) -> float:
    """
    How significant is this entity, judged by what David keeps returning to?

    0.0 when the label matches no recurring topic — which is most of them, and
    correct. A label is scored on its strongest matching word so a multi-word
    entity is not punished for carrying an incidental one.
    """
    idx = topic_significance() if index is None else index
    if not idx:
        return 0.0
    words = re.findall(r"[a-z][a-z'-]{2,}", str(label or "").lower())
    if not words:
        return 0.0

    hits = [idx.get(w, 0.0) for w in words if idx.get(w, 0.0) > 0.0]
    if not hits:
        return 0.0

    # Strength AND coverage. Taking the max alone meant one shared common noun
    # carried a whole entity: "Arabic Language" and "Modernist Design" ranked
    # above "eLo robot design constraints" because they each touched one
    # mid-frequency topic, while the robot entity touches three.
    #
    # An entity whose words are MOSTLY things David returns to is about one of
    # his threads. An entity that happens to contain "design" is not.
    # Mean, not max. Max let one shared common noun carry a whole entity.
    # Coverage then asks how much of the label is his vocabulary at all.
    #
    # TUNED BY LOOKING AT OUTPUT, three times, and that is worth admitting:
    # max alone put "Hello, World!" level with the robot; max x coverage put
    # "Arabic Language" above it; this puts his own domain on top. The
    # ORDERING is a judgement — [BUILDER CHOICE], same standing as
    # significance_faculty._WEIGHTS.
    #
    # What is NOT a judgement, and is the claim worth making: the separation
    # between zero and non-zero. 83 of 249 entities score at all; Ada
    # Lovelace, the African Continent and Akan Culture score 0.0 while eLo's
    # robot, projects and Unity do not. That gap is measured, not tuned.
    coverage = len(hits) / len(words)
    return round((sum(hits) / len(hits)) * (coverage ** 0.5), 4)


def top_topics(n: int = 15) -> list[tuple[str, float]]:
    """What the graph says matters most. For evidence, not for ranking."""
    return sorted(topic_significance().items(), key=lambda kv: -kv[1])[:n]
