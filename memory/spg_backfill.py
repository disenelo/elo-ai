"""
memory/spg_backfill.py — ROOT-4: build the pattern graph from what already
happened.

The framework's answer to "what can eLo become through experience that we did
not program him to become?" is "nothing, until ROOT-1 and ROOT-4 are wired".
ROOT-4 is this: SPG has four months of conversation available and has never
been loaded with it.

MEASURED BEFORE BUILDING, 2026-10-06:

    memory/interactions.json   3,309 turns, 2026-06-06 -> 2026-10-06
    data/spg_graph.json        3 nodes, 0 edges
    data/spg_signals.jsonl     13,919 signals, of which 13,877 (99.7%)
                               carry turn_id="" — so spg_graph's node id
                               f"{turn_id}:{signal_type}" collapsed all of
                               them onto 44 nodes

The signal log cannot be repaired after the fact: a turn identity that was
never written cannot be recovered. interactions.json can, because every row
IS a turn and carries its own timestamp. That is why the brief backfills from
here and not from the signal log.

WHY NOT `concepts`. The field exists and looks like the obvious key, but it is
populated on 232 of 3,309 rows and holds six coarse values (creation,
identity, emotion, technical, narrative, imagination). Six buckets over four
months is not a pattern space. The topics are extracted from what was actually
said instead.

WHAT "SIGNIFICANT" MEANS HERE. The brief's definition of done is: "David
mentions something repeatedly (a pattern). SPG identifies it as significant."
So recurrence dominates, log-scaled — the difference between mentioning
something once and ten times matters far more than between 100 and 110. That
matches memory/spg_significance.py, which uses the same shape for claims.

This module never writes the live graph unless asked. build() returns a graph;
the caller chooses where it goes.
"""
from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from memory.spg_graph import Edge, Node, SPGGraph

_log = logging.getLogger("elo.spg_backfill")

_ROOT = Path(__file__).parent.parent
INTERACTIONS = _ROOT / "memory" / "interactions.json"

# [BUILDER CHOICE — pending Board confirmation, same standing as
# significance_faculty._WEIGHTS]. Recurrence dominates because the brief
# defines significance as repetition. Mode is a weak prior: a turn where
# something was BUILT or REFLECTED on carries more than a social reflex.
W_RECURRENCE: float = 0.70
W_MODE:       float = 0.20
W_SUBSTANCE:  float = 0.10

# [BUILDER CHOICE] What each CAL mode contributes. Ordered by how much of eLo
# is engaged, not by how common the mode is.
MODE_WEIGHT: dict[str, float] = {
    "build":         1.00,
    "reflect":       0.85,
    "connect":       0.85,
    "challenge":     0.70,
    "answer":        0.55,
    "celebrate":     0.50,
    "witness":       0.45,
    "ground":        0.40,
    "companion":     0.30,
    "social_reflex": 0.10,
}

# Turns more than this far apart are different sessions, so no temporal edge.
SESSION_GAP_S: float = 1800.0

# A topic needs to appear at least this often to be a pattern rather than a
# one-off word.
MIN_TOPIC_COUNT: int = 3

_STOP = frozenset("""
a an and are as at be been being but by can could did do does doing for from
had has have he her hers him his how i if in into is it its me my no not of on
or our out over she so some than that the their them then there these they
this those to too us was we were what when where which who why will with would
you your yours am im it's thats just really very much more most like about
thing things something anything nothing one two get got go going know think
feel say said make made want need see come take here now still yet even yeah
okay ok right good well also because while after before back down up out
eLo elo david
""".split())


# The `user` field is not always what David said. 1,076 of 3,309 rows hold the
# ASSEMBLED PROMPT — a bracketed context block prepended to his words:
#
#   [WORLD_KNOWLEDGE — from eLo's own world (verified, confidence 1.0 ...)]
#   eLo Robot: A physical animatronic version of eLo ...
#   User asked: eLo, are you there? say something short
#
# Measured prefixes: WORLD_KNOWLEDGE 1076, WEB_SEARCH 126, COMPANY_STATE 27,
# CULTURAL_FACT 12, SCREEN_READ 2, TODO_VAULT 2, PROJECT_LIST 2.
#
# Scored raw, the top "topics David keeps returning to" came back as world,
# asked, user, answer, knowledge, confidence, verified — the graph measuring
# its own scaffolding and calling it David. Everything after the last
# "User asked:" is the real utterance.
_ASKED_RE = re.compile(r"User asked:\s*", re.I)
_LEADING_BLOCK_RE = re.compile(r"^\s*\[[A-Z_][A-Z_ ]*[^\]]*\][^\n]*\n?", re.M)


def david_said(text: str) -> str:
    """What David actually typed, with any injected context stripped."""
    t = str(text or "")
    if _ASKED_RE.search(t):
        t = _ASKED_RE.split(t)[-1]
    else:
        t = _LEADING_BLOCK_RE.sub("", t)
    return t.strip()


def _topics(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z'-]{3,}", david_said(text).lower())
    return {w for w in words if w not in _STOP}


def _ts(row: dict) -> float:
    raw = str(row.get("timestamp", "") or "")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _recurrence(topics: set[str], counts: Counter) -> float:
    """
    Log-scaled, 0..1. A turn scores on its MOST recurrent topic, not the sum —
    one deeply recurring thread should not be diluted by incidental words.
    """
    if not topics or not counts:
        return 0.0
    best = max((counts.get(t, 0) for t in topics), default=0)
    if best < MIN_TOPIC_COUNT:
        return 0.0
    ceiling = max(counts.values()) if counts else 1
    if ceiling <= 1:
        return 0.0
    return min(1.0, math.log1p(best) / math.log1p(ceiling))


def _substance(row: dict) -> float:
    """Length of what DAVID said — an injected context block is not substance."""
    n = len(david_said(row.get("user", "")))
    return min(1.0, n / 240.0)


def load_interactions(path: Path = INTERACTIONS) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        _log.warning("spg_backfill: cannot read %s — %s", path, e)
        return []
    rows = data if isinstance(data, list) else data.get("interactions", [])
    return [r for r in rows if isinstance(r, dict)]


def topic_counts(rows: list[dict]) -> Counter:
    """How often each topic appears across the whole history."""
    c: Counter = Counter()
    for r in rows:
        c.update(_topics(r.get("user", "")))
    return c


def score(row: dict, counts: Counter) -> float:
    rec = _recurrence(_topics(row.get("user", "")), counts)
    mode = MODE_WEIGHT.get(str(row.get("mode", "")).lower(), 0.3)
    return round(
        W_RECURRENCE * rec + W_MODE * mode + W_SUBSTANCE * _substance(row), 4
    )


def build(rows: list[dict] | None = None, *, max_rows: int | None = None
          ) -> SPGGraph:
    """
    One node per turn, edged temporally within a session and semantically by
    shared recurring topic.

    Node ids are backfill-prefixed so a backfilled node is always
    distinguishable from one written live — a graph that cannot say which of
    its memories were reconstructed is a graph that cannot be trusted about
    its own past.
    """
    rows = load_interactions() if rows is None else rows
    if max_rows:
        rows = rows[:max_rows]
    rows = sorted(rows, key=_ts)

    graph = SPGGraph()
    if not rows:
        return graph

    counts = topic_counts(rows)
    # Only topics that actually recur can carry a semantic edge.
    recurring = {t for t, n in counts.items() if n >= MIN_TOPIC_COUNT}

    ids: list[str] = []
    stamps: list[float] = []
    per_topic: dict[str, list[str]] = {}

    for i, row in enumerate(rows):
        ts = _ts(row)
        nid = f"bf-{i:05d}-{str(row.get('timestamp',''))[:19]}"
        ids.append(nid)
        stamps.append(ts)
        graph.add_node(Node(
            id=nid,
            content_hash="",
            significance=score(row, counts),
            embodiment=str(row.get("project_tag", "") or "desktop"),
            ts=ts,
        ))
        for t in _topics(row.get("user", "")) & recurring:
            per_topic.setdefault(t, []).append(nid)

    # Temporal — consecutive turns inside one session.
    for i in range(1, len(ids)):
        gap = stamps[i] - stamps[i - 1]
        if 0 <= gap <= SESSION_GAP_S:
            graph.add_edge(Edge(
                from_node=ids[i - 1], to_node=ids[i], link_type="temporal",
                weight=round(max(0.1, 1.0 - gap / SESSION_GAP_S), 3),
                evidence=f"{gap:.0f}s apart",
            ))

    # Semantic — consecutive mentions of the same recurring topic. Chained
    # rather than fully connected: a topic in 300 turns would otherwise make
    # ~45,000 edges and say nothing more than the chain does.
    for topic, members in per_topic.items():
        for a, b in zip(members, members[1:]):
            graph.add_edge(Edge(
                from_node=a, to_node=b, link_type="semantic",
                weight=round(min(1.0, math.log1p(counts[topic]) / 6.0), 3),
                evidence=f"topic:{topic}",
            ))

    _log.info("spg_backfill: %d turns -> %d nodes, %d edges",
              len(rows), len(graph._nodes), len(graph._edges))
    return graph


def recurring_topics(rows: list[dict] | None = None, top: int = 20
                     ) -> list[tuple[str, int]]:
    """What David actually returns to. The answer the graph exists to give."""
    rows = load_interactions() if rows is None else rows
    return topic_counts(rows).most_common(top)


# ── Incremental ──────────────────────────────────────────────────────────────
#
# build() constructs a FRESH graph. Re-running it to pick up new turns would
# discard every node written live since the last pass — the claim-keyed nodes
# from record_claim, which are the half that grows on its own. Measured
# 2026-10-06: 3,330 nodes, of which 3,321 backfilled and 9 live. A rebuild
# would have silently dropped those 9.
#
# So a second pass ADDS. It reads what is already there, works out which turns
# are missing, and appends only those.

def processed_ids(graph) -> set:
    """Backfill node ids already in a graph."""
    nodes = getattr(graph, "_nodes", {}) or {}
    return {nid for nid in nodes if str(nid).startswith("bf-")}


def unprocessed(rows: list[dict] | None = None, graph=None) -> list[dict]:
    """
    Turns that have no node yet, oldest first.

    Identity is the node id build() would mint, so this answers "has this turn
    been processed" by the same key the graph is stored under rather than by a
    guess about timestamps.
    """
    rows = load_interactions() if rows is None else rows
    rows = sorted(rows, key=_ts)

    if graph is None:
        try:
            from memory.spg_graph import SPGGraph
            graph = SPGGraph.load()
        except Exception as e:
            _log.warning("spg_backfill: cannot load graph — %s", e)
            return []

    have = processed_ids(graph)
    out = []
    for i, row in enumerate(rows):
        nid = f"bf-{i:05d}-{str(row.get('timestamp',''))[:19]}"
        if nid not in have:
            out.append(row)
    return out


def update(rows: list[dict] | None = None, graph=None):
    """
    Add any unprocessed turns to the existing graph, in place.

    Returns (graph, added) where added is the list of turns processed. The
    caller saves — this never writes, so a dry run is a dry run.
    """
    rows = load_interactions() if rows is None else rows
    rows = sorted(rows, key=_ts)

    if graph is None:
        from memory.spg_graph import SPGGraph
        graph = SPGGraph.load()

    have = processed_ids(graph)
    counts = topic_counts(rows)
    recurring = {t for t, n in counts.items() if n >= MIN_TOPIC_COUNT}

    # Every turn's id and topics, so a new node can edge to an existing one.
    ids: list[str] = []
    stamps: list[float] = []
    per_topic: dict[str, list[str]] = {}
    for i, row in enumerate(rows):
        nid = f"bf-{i:05d}-{str(row.get('timestamp',''))[:19]}"
        ids.append(nid)
        stamps.append(_ts(row))
        for t in _topics(row.get("user", "")) & recurring:
            per_topic.setdefault(t, []).append(nid)

    added: list[dict] = []
    for i, row in enumerate(rows):
        if ids[i] in have:
            continue
        graph.add_node(Node(
            id=ids[i], content_hash="",
            significance=score(row, counts),
            embodiment=str(row.get("project_tag", "") or "desktop"),
            ts=stamps[i],
        ))
        added.append(row)

        if i > 0:
            gap = stamps[i] - stamps[i - 1]
            if 0 <= gap <= SESSION_GAP_S:
                graph.add_edge(Edge(
                    from_node=ids[i - 1], to_node=ids[i], link_type="temporal",
                    weight=round(max(0.1, 1.0 - gap / SESSION_GAP_S), 3),
                    evidence=f"{gap:.0f}s apart",
                ))

        for t in _topics(row.get("user", "")) & recurring:
            members = per_topic.get(t, [])
            pos = members.index(ids[i]) if ids[i] in members else -1
            if pos > 0:
                graph.add_edge(Edge(
                    from_node=members[pos - 1], to_node=ids[i],
                    link_type="semantic",
                    weight=round(min(1.0, math.log1p(counts[t]) / 6.0), 3),
                    evidence=f"topic:{t}",
                ))

    _log.info("spg_backfill: %d new turn(s) added to %d existing nodes",
              len(added), len(have))
    return graph, added
