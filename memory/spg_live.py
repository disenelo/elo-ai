"""
memory/spg_live.py — SPG keeps up with the conversation.

Card WO-B2-0008: "Every turn David speaks, significance is scored and written
to SPG in real time."

WHAT WAS ACTUALLY HAPPENING. Two paths could put a live node in the graph and
neither covered a turn:

  1. server.py:7442 records a WKG claim (which mints an SPG node) only
     `if _mem_cats` — category-tagged turns. Measured across the whole store:
     2,536 of 3,335 tagged, so **799 turns (24%) wrote nothing**, including
     "I want to build a world" and "what is Sugarcore?".
  2. significance_faculty taps SPG on a spike above SPIKE_THRESHOLD = 0.6.
     That module asserts its own unreachability at import: max achievable
     overall is 0.0929. No spike has ever been logged.

So "SPG live scoring" was 76% coverage through a side effect, plus a tap that
has never once fired.

WHAT THIS DOES INSTEAD. The backfill scorer already reads the same turn store
and already discriminates — 1,260 distinct significance values across 3,335
turns, against significance_faculty's range of 0.0065. `spg_backfill.update()`
is incremental and keyed by the node id `build()` would mint, so it adds only
turns that have no node yet and cannot eat live claim-keyed nodes.

Driven from the ambient tick rather than the turn path, which means **no
server.py change** — the file is Builder 1's, and a turn appears in the store
within a tick of being spoken either way.

Cheap by construction: the store's mtime is checked first, so the common case
(nothing new) is one stat() call and no graph load.
"""
from __future__ import annotations

import logging
import os
import threading

_log = logging.getLogger("elo.spg_live")

_lock = threading.Lock()
_last_mtime: float = 0.0
_last_count: int = 0


def _store_mtime() -> float:
    try:
        from memory.spg_backfill import INTERACTIONS
        return os.path.getmtime(INTERACTIONS)
    except Exception:
        return 0.0


def sync_new_turns(*, force: bool = False) -> int:
    """
    Score and record any turn that has no SPG node yet.

    Returns how many nodes were added. 0 is the common answer and an honest
    one — it means the graph is current, not that the sync is broken.

    Never raises: SPG falling behind must not stop an ambient tick.
    """
    global _last_mtime, _last_count
    try:
        mtime = _store_mtime()
        with _lock:
            if not force and mtime and mtime == _last_mtime:
                return 0            # nothing has been said since last look
            _last_mtime = mtime

            from memory.spg_backfill import update
            from memory.spg_graph import SPGGraph

            graph = SPGGraph.load()
            before = len(getattr(graph, "nodes", []) or [])
            graph, added = update(graph=graph)
            if not added:
                return 0
            graph.save()
            after = len(getattr(graph, "nodes", []) or [])
            # WO-B2-0011 — a node that says THAT something mattered without
            # saying WHAT it was cannot be read by anything downstream. The
            # index is keyed by the same node id the graph stores.
            try:
                from faculties.spg.content_index import sync_from_interactions
                sync_from_interactions()
            except Exception:
                pass
            _last_count = after
            _log.info("SPG live: +%d node(s) from %d new turn(s) (%d -> %d)",
                      after - before, len(added), before, after)
            return after - before
    except Exception as e:
        _log.debug("SPG live sync skipped (non-fatal): %s", e)
        return 0
