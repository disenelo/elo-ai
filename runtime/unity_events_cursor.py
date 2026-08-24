"""
runtime/unity_events_cursor.py — Builder-side cursor for the unity_events.json append-log.

Card 0015 · RULING 00d: `unity_events.json` is an append-only NDJSON log written by Designer.
Each row carries a monotonic `seq`. The reader tracks the last `seq` it consumed; anything
above that is unread. That is what makes delivery provable rather than hopeful.

Rotation handshake (Designer FROM_DESIGN 2026-08-15):
- Designer bounds the log at 400 rows and reads `unity_events_cursor.json` before rotating.
- If rotation would discard a row above `consumed_seq`, Designer logs a WARNING (Rule 1).
- If the cursor file is absent Designer warns on any drop (conservative).
- So the Builder writes `{"consumed_seq": <long>, "_ts": <unix>}` here after each read batch.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time

_log = logging.getLogger(__name__)

_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURSOR_PATH  = os.path.join(_ROOT, "blender", "unity_events_cursor.json")
EVENTS_PATH  = os.path.join(_ROOT, "blender", "unity_events.json")


def read_cursor(path: str | None = None) -> int:
    """Return the last consumed seq, or -1 if the cursor file is absent/unreadable."""
    p = path or CURSOR_PATH
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        seq = data.get("consumed_seq", -1)
        return int(seq) if isinstance(seq, (int, float)) else -1
    except FileNotFoundError:
        return -1
    except Exception as e:
        _log.warning("unity_events_cursor: read error at %s: %s", p, e)
        return -1


def write_cursor(consumed_seq: int, path: str | None = None) -> bool:
    """Atomically write the consumed seq. Returns True on success."""
    p = path or CURSOR_PATH
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        payload = {"consumed_seq": int(consumed_seq), "_ts": time.time()}
        fd, tmp = tempfile.mkstemp(prefix=".cursor.", dir=os.path.dirname(p))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp, p)
        except Exception:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            raise
        return True
    except Exception as e:
        _log.warning("unity_events_cursor: write error at %s: %s", p, e)
        return False


def iter_events_from(seq_after: int, events_path: str | None = None):
    """Yield NDJSON rows with seq > seq_after, in file order. Tolerant of blank/corrupt lines."""
    p = events_path or EVENTS_PATH
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if not isinstance(row, dict):
                    continue
                seq = row.get("seq")
                if not isinstance(seq, int):
                    continue
                if seq <= seq_after:
                    continue
                yield row
    except FileNotFoundError:
        return


def max_seq(events_path: str | None = None) -> int:
    """Return the highest seq currently in the append-log, or -1 if empty/absent."""
    p = events_path or EVENTS_PATH
    highest = -1
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if isinstance(row, dict) and isinstance(row.get("seq"), int):
                    if row["seq"] > highest:
                        highest = row["seq"]
    except FileNotFoundError:
        pass
    return highest
