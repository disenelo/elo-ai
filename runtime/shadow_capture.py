"""
runtime/shadow_capture.py — WO-070: Understudy shadow-capture (training-data basket).

CAPTURE ONLY — no training, no model swap. Every runtime turn appends one clean
record to self/journals/understudy_shadow.jsonl for future LoRA fine-tuning (Vol XXVIII).

Architecture:
  - record_turn() enqueues immediately (non-blocking, <1µs on the caller's thread).
  - A daemon background writer drains the queue and does all file I/O.
  - Any write failure is isolated — the spine/bus turn is never affected.
  - Bus `*` subscriber for l3_rating events (David approve / override).
  - Append-only local storage, never external DB.

ADR-Exec-005 · Volume XXVIII (fine-tune is a separate WO, post-Presentable).
"""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time

_log = logging.getLogger(__name__)

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SHADOW_LOG = os.environ.get(
    "ELO_SHADOW_LOG",
    os.path.join(_ROOT, "self", "journals", "understudy_shadow.jsonl"),
)

_q: queue.Queue = queue.Queue(maxsize=0)  # unbounded — never blocks the enqueuer
_lock  = threading.Lock()
_started = False


# ── Background writer ─────────────────────────────────────────────────────────

def _writer_loop() -> None:
    """Daemon thread — drains queue, writes records to disk one at a time."""
    while True:
        try:
            record = _q.get(block=True, timeout=5.0)
        except queue.Empty:
            continue
        except Exception:
            continue
        if record is None:              # stop sentinel (used in tests)
            _q.task_done()
            break
        try:
            _flush(record)
        except Exception as e:
            _log.warning("shadow_capture writer error: %s", e)
        finally:
            _q.task_done()              # always decrements — flush failure cannot block join()


def _flush(record: dict) -> None:
    try:
        path = _SHADOW_LOG
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        _log.warning("shadow_capture flush failed: %s", e)


def _ensure_writer() -> None:
    global _started
    with _lock:
        if not _started:
            t = threading.Thread(
                target=_writer_loop,
                daemon=True,
                name="shadow-capture-writer",
            )
            t.start()
            _started = True


# ── Public API ────────────────────────────────────────────────────────────────

def record_turn(
    raw_input: str,
    elo_raw_gen: str,
    elo_final: str,
    backend_used: str,
    *,
    trace_id: str = "",
    context: dict | None = None,
    executed_action: str = "",
    l3_rating: str | None = None,
) -> None:
    """
    Enqueue one turn record for background writing. Returns immediately.
    Never raises — any failure is logged and dropped silently.
    """
    _ensure_writer()
    record = {
        "trace_id":        trace_id,
        "timestamp":       time.time(),
        "context":         context or {},
        "raw_input":       raw_input,
        "elo_raw_gen":     elo_raw_gen,
        "elo_final":       elo_final,
        "backend_used":    backend_used,
        "executed_action": executed_action,
        "l3_rating":       l3_rating,
    }
    try:
        _q.put_nowait(record)
    except Exception as e:
        _log.warning("shadow_capture enqueue failed: %s", e)


def record_l3_rating(trace_id: str, rating: str) -> None:
    """
    Called when David approves or overrides a turn (L3 signal).
    Appends a patch record — correlate by trace_id in post-processing.
    """
    _ensure_writer()
    record = {
        "_type":     "l3_patch",
        "trace_id":  trace_id,
        "timestamp": time.time(),
        "l3_rating": rating,
    }
    try:
        _q.put_nowait(record)
    except Exception as e:
        _log.warning("shadow_capture l3 enqueue failed: %s", e)


def subscribe_to_bus() -> None:
    """
    Register ShadowCapture as a `*` subscriber on the Faculty Bus.
    Filters for l3_rating payload events so bus heartbeat stays clean.
    Call once at startup. Non-blocking — any bus failure is silently swallowed.
    """
    try:
        from core.faculty_bus import get_bus
        bus = get_bus()
        bus.subscribe(
            "ShadowCapture",
            filter_fn=lambda e: e.payload.get("type") == "l3_rating",
        )
    except Exception as e:
        _log.warning("shadow_capture bus subscribe failed: %s", e)


def drain_bus_ratings() -> None:
    """
    Pull any pending l3_rating envelopes from the bus and enqueue them.
    Called opportunistically (e.g. after each turn) — not on a timer.
    """
    try:
        from core.faculty_bus import get_bus
        bus = get_bus()
        for env in bus.get_messages("ShadowCapture"):
            body = env.payload.get("body", {})
            tid  = body.get("trace_id", env.id)
            rating = body.get("rating", "unknown")
            record_l3_rating(tid, rating)
    except Exception as e:
        _log.warning("shadow_capture drain_bus_ratings failed: %s", e)


def flush_sync(timeout: float = 2.0) -> None:
    """
    Block until the write queue is empty (used in tests only).
    Does NOT drain bus — call drain_bus_ratings() first if needed.
    """
    try:
        _q.join()
    except Exception:
        pass
