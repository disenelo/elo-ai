"""
self/route_memory.py — WO-094: Route Memory (Part D)

Records where eLo went, what path he took, and how it went.
A failed reach is as valuable as a success — both inform future navigation.

ADR-Exec-005 boundary:
  - Never touches identity / values / personality state
  - Outcomes written ONLY on verified body ACK (ack_received=True)
  - Append-only — no deletions, no overwrites

JSONL schema per record:
  ts          float   — Unix timestamp at write
  goal        str     — target surface_id or surface description
  route_legs  list    — ordered list of legs taken (each a string)
  arrived     bool    — did eLo reach goal
  fell        bool    — did eLo fall/miss during travel
  duration_s  float   — travel time in seconds (caller-provided)
  smoothness  float   — subjective 0.0–1.0 (caller-provided; 1.0 = perfectly smooth)
  ack_id      str     — the ACK identifier from the body, for traceability
"""
from __future__ import annotations

import json
import os
import time

_ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROUTE_LOG = os.path.join(_ROOT, "self", "journals", "route_memory.jsonl")

# Recent-record window for confidence scoring
_CONFIDENCE_WINDOW = 10


def remember_route(
    goal_surface: str,
    legs: list[str],
    arrived: bool,
    fell: bool,
    duration_s: float,
    smoothness: float,
    ack_id: str,
    ack_received: bool,
    log_path: str | None = None,
) -> bool:
    """
    Append a route outcome to the JSONL log.
    Returns True on success, False if not written (ack_received=False or error).

    Write ONLY when ack_received is True — an assumed success is NOT a success.
    """
    if not ack_received:
        return False

    path = log_path or _ROUTE_LOG
    record = {
        "ts":         time.time(),
        "goal":       goal_surface or "",
        "route_legs": legs if isinstance(legs, list) else [],
        "arrived":    bool(arrived),
        "fell":       bool(fell),
        "duration_s": float(duration_s),
        "smoothness": float(smoothness),
        "ack_id":     str(ack_id),
    }

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def recall_route(goal_surface: str, log_path: str | None = None) -> dict | None:
    """
    Return the most recent successful route to goal_surface, or None if unknown.
    'Successful' = arrived=True.  Falls back to the most recent attempt overall.
    """
    path = log_path or _ROUTE_LOG
    best: dict | None = None
    best_arrived: dict | None = None

    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("goal") != goal_surface:
                    continue
                best = rec
                if rec.get("arrived"):
                    best_arrived = rec
    except FileNotFoundError:
        return None
    except Exception:
        return None

    return best_arrived if best_arrived is not None else best


def route_confidence(goal_surface: str, log_path: str | None = None) -> float:
    """
    Return confidence [0.0, 1.0] that eLo can reach goal_surface based on recent attempts.
    0.0 = never tried or all failed.  1.0 = all recent attempts succeeded.
    Uses last _CONFIDENCE_WINDOW records for goal.
    """
    path = log_path or _ROUTE_LOG
    records: list[dict] = []

    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("goal") == goal_surface:
                    records.append(rec)
    except FileNotFoundError:
        return 0.0
    except Exception:
        return 0.0

    if not records:
        return 0.0

    window = records[-_CONFIDENCE_WINDOW:]
    successes = sum(1 for r in window if r.get("arrived"))
    return round(successes / len(window), 3)


def recent_routes(n: int = 5, log_path: str | None = None) -> list[dict]:
    """
    WO-118: Return the last n route records (any goal), newest last.
    Makes route history readable by the Executive (Row 14 ROUTE proof).
    """
    path = log_path or _ROUTE_LOG
    records: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return []
    except Exception:
        return []
    return records[-n:]
