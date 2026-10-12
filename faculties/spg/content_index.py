"""
faculties/spg/content_index.py — WO-B2-0011: what was actually significant.

An SPG node carries `id`, `content_hash`, `significance`, `embodiment`, `ts`
and nothing else. So SPG can say THAT a moment mattered and never WHAT it
was. Builder 1 hit this from the mock-backend side (0120): nothing can read a
node and get anything back.

Worse, the 3,335 backfill nodes carry `content_hash=""`
(`memory/spg_backfill.py:225`, `:345`), so they cannot even be matched by
hash — reachable by significance and time, by nothing else.

WHY A SIDE INDEX AND NOT A FIELD ON Node. The obvious fix is `content: str` on
the Node dataclass in `memory/spg_graph.py`. That file is not Builder 2's
seat. This keeps the same capability inside the lane: an index keyed by the
node id the graph already stores, so a reader joins on the key it already
has. No schema change, no migration, and nothing to coordinate.

If the Node field is later authorised, this becomes its backfill source
rather than being thrown away.

Text is stored as David and eLo actually said it, with the assembled-prompt
scaffolding stripped — `david_said()` exists because `User asked:` and
`[BLOCK]` prefixes contaminated the corrections ledger the same way.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

_log = logging.getLogger("elo.spg.content")

_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = _ROOT / "data" / "spg_content.json"

# A node's text is for reading back, not for storing the conversation twice.
MAX_CHARS = 600

_lock = threading.Lock()


def _load() -> dict:
    try:
        with open(INDEX_PATH, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d: dict) -> None:
    """Atomic — a half-written index reads as missing content, not wrong content."""
    try:
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
        tmp = f"{INDEX_PATH}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1, ensure_ascii=False)
        os.replace(tmp, INDEX_PATH)
    except Exception as e:
        _log.debug("spg content index not saved (non-fatal): %s", e)


def record_content(node_id: str, text: str) -> bool:
    """Attach readable text to one node id. Returns True if it was stored."""
    node_id = str(node_id or "").strip()
    text = str(text or "").strip()
    if not node_id or not text:
        return False
    with _lock:
        d = _load()
        d[node_id] = text[:MAX_CHARS]
        _save(d)
    return True


def content_for(node_id: str) -> str:
    """
    The text behind a node, or "" when there is none.

    "" means this node predates the capture — not that the turn was empty.
    """
    return _load().get(str(node_id or "").strip(), "")


def sync_from_interactions(rows: list[dict] | None = None) -> int:
    """
    Fill the index for every turn the backfill has a node for.

    Uses exactly the id `spg_backfill.build()` mints, so the join is on the
    same key the graph is stored under rather than on a guess about ordering.

    Returns how many entries were added. Never raises.
    """
    added = 0
    try:
        # Read INTERACTIONS at CALL time, not as load_interactions' default.
        # That default is bound when the function is defined, so patching the
        # module attribute does nothing and a test silently reads David's real
        # store — caught by this module's own tests returning 3,336 instead of
        # 2. Same shape as the ambient_engine motion-state path.
        import memory.spg_backfill as _bf
        from memory.spg_backfill import david_said, _ts

        rows = _bf.load_interactions(_bf.INTERACTIONS) if rows is None else rows
        rows = sorted(rows, key=_ts)

        with _lock:
            d = _load()
            for i, row in enumerate(rows):
                nid = f"bf-{i:05d}-{str(row.get('timestamp',''))[:19]}"
                if nid in d:
                    continue
                said = david_said(row.get("user", "")).strip()
                said = said or str(row.get("user") or "").strip()
                reply = str(row.get("response") or "").strip()
                if not said and not reply:
                    continue
                parts = []
                if said:
                    parts.append(f"David: {said}")
                if reply:
                    parts.append(f"eLo: {reply}")
                d[nid] = "\n".join(parts)[:MAX_CHARS]
                added += 1
            if added:
                _save(d)
    except Exception as e:
        _log.debug("spg content sync skipped (non-fatal): %s", e)
    return added
