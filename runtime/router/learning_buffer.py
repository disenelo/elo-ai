"""
runtime/router/learning_buffer.py — Stage 10: Learning Buffer

Store successful and failed routes, typos, agent outcomes.
No online retraining. Logs only — read by diagnostics and future training pipelines.

Architecture authority: 16_diagnostics_and_health.md
"""
from __future__ import annotations

import json
import os
import time

_ROOT      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LOG_PATH  = os.path.join(_ROOT, "logs", "routing_buffer.jsonl")
_MAX_BYTES = 5 * 1024 * 1024   # 5 MB cap — rotate rather than grow unbounded


def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)


def record(
    raw: str,
    intent: str,
    agents: list[str],
    confidence: float,
    outcome: str,            # "success" | "failed" | "no_agent" | "confirmed" | "cancelled"
    typo_fixed: bool = False,
    duration_ms: float = 0.0,
) -> None:
    """
    Append one routing event to the log.

    Args:
        raw         — original user input
        intent      — classified intent
        agents      — list of agent names that ran
        confidence  — pipeline confidence score
        outcome     — result classification
        typo_fixed  — True if the typo engine changed the input
        duration_ms — wall time from input to response (if measured)
    """
    entry = {
        "_ts":        round(time.time(), 3),
        "raw":        raw[:200],             # cap length — no data bloat
        "intent":     intent,
        "agents":     agents,
        "confidence": round(confidence, 3),
        "outcome":    outcome,
        "typo_fixed": typo_fixed,
        "duration_ms": round(duration_ms, 1),
    }
    try:
        _ensure_dir()
        # Rotate if too large
        if os.path.exists(_LOG_PATH) and os.path.getsize(_LOG_PATH) > _MAX_BYTES:
            archive = _LOG_PATH + ".1"
            if os.path.exists(archive):
                os.unlink(archive)
            os.rename(_LOG_PATH, archive)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass   # never let logging break the runtime


def record_typo(original: str, repaired: str, confidence: float) -> None:
    """Record a typo repair event — helps identify patterns for future _KNOWN_TYPOS additions."""
    try:
        _ensure_dir()
        entry = {
            "_ts":        round(time.time(), 3),
            "type":       "typo",
            "original":   original[:100],
            "repaired":   repaired[:100],
            "confidence": round(confidence, 3),
        }
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def recent(n: int = 20) -> list[dict]:
    """Return the last n routing events (newest first). Read-only."""
    try:
        if not os.path.exists(_LOG_PATH):
            return []
        with open(_LOG_PATH, encoding="utf-8") as f:
            lines = f.readlines()
        entries = []
        for line in reversed(lines[-500:]):
            try:
                entries.append(json.loads(line))
                if len(entries) >= n:
                    break
            except Exception:
                continue
        return entries
    except Exception:
        return []


def summary() -> dict:
    """
    Quick health summary — used by diagnostics.
    Returns counts of success/failed/no_agent outcomes in the last 100 turns.
    """
    entries = recent(100)
    counts: dict[str, int] = {}
    for e in entries:
        outcome = e.get("outcome", "unknown")
        counts[outcome] = counts.get(outcome, 0) + 1

    intents: dict[str, int] = {}
    for e in entries:
        intent = e.get("intent", "unknown")
        intents[intent] = intents.get(intent, 0) + 1

    top_intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total":       len(entries),
        "outcomes":    counts,
        "top_intents": top_intents,
    }
