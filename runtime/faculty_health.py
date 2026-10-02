"""
runtime/faculty_health.py — Faculty Health Registry (WO-042)

Persistent, session-scoped health state per faculty.
The Executive routes on this — a DEGRADED/OFFLINE faculty is quarantined and
retried periodically instead of hammered every turn.

Faculties tracked (WO-FACULTY-HEALTH-EXPAND-001: expanded from 4 to 11):
    reasoning   — LLM backend (OpenAI / Groq / Cerebras / Ollama)
    memory      — vault + interaction store
    tools       — tool agents (weather, calendar, web search, etc.)
    embodiment  — Unity/Presence ACK channel
    curiosity   — curiosity_faculty gap detection + question formation
    dream       — dream_faculty + dream_review wake transfer
    synthesis   — synthesis observer cross-signal connections
    perception  — perception faculty sensory integration
    wkg         — working knowledge graph reads + writes
    reflection  — reflection_faculty vault integration
    voice       — TTS output + voice register

Status values:
    CONNECTED   — working normally
    DEGRADED    — partial failure; fallback in use
    OFFLINE     — fully unavailable; quarantined

Usage:
    from runtime.faculty_health import mark_degraded, mark_recovered, get_status, health_summary
"""
from __future__ import annotations
import os
import json
import logging
import time

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())
_log.propagate = False

CONNECTED = "CONNECTED"
DEGRADED  = "DEGRADED"
OFFLINE   = "OFFLINE"

# WO-FACULTY-HEALTH-EXPAND-001: expanded from 4 to 11 faculties.
# Original 4 (coarse system buckets) kept unchanged; 7 new ones added.
_FACULTIES = (
    "reasoning",   # LLM backend
    "memory",      # vault + interaction store
    "tools",       # tool agents
    "embodiment",  # Unity/Presence ACK
    "curiosity",   # gap detection + question formation
    "dream",       # dream_faculty + dream_review wake transfer
    "synthesis",   # cross-signal synthesis observer
    "perception",  # sensory integration
    "wkg",         # working knowledge graph
    "reflection",  # reflection_faculty vault integration
    "voice",       # TTS + voice register
)

_registry: dict[str, dict] = {
    f: {"status": CONNECTED, "error_count": 0, "last_error": "", "last_checked": 0.0}
    for f in _FACULTIES
}

_HEALTH_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "blender", "faculty_health.json"
)


def get_status(faculty: str) -> str:
    """Return CONNECTED | DEGRADED | OFFLINE for this faculty."""
    return _registry.get(faculty, {}).get("status", CONNECTED)


def mark_degraded(faculty: str, reason: str = "") -> None:
    if faculty not in _registry:
        return
    rec = _registry[faculty]
    rec["status"]       = DEGRADED
    rec["last_error"]   = reason
    rec["error_count"] += 1
    rec["last_checked"] = time.time()
    _log.warning("Faculty DEGRADED: %s — %s (errors: %d)", faculty, reason, rec["error_count"])
    _persist()


def mark_offline(faculty: str, reason: str = "") -> None:
    if faculty not in _registry:
        return
    rec = _registry[faculty]
    rec["status"]       = OFFLINE
    rec["last_error"]   = reason
    rec["error_count"] += 1
    rec["last_checked"] = time.time()
    _log.error("Faculty OFFLINE: %s — %s", faculty, reason)
    _persist()


def mark_recovered(faculty: str) -> None:
    if faculty not in _registry:
        return
    rec = _registry[faculty]
    if rec["status"] != CONNECTED:
        _log.info("Faculty RECOVERED: %s (was %s)", faculty, rec["status"])
    rec["status"]       = CONNECTED
    rec["error_count"]  = 0
    rec["last_error"]   = ""
    rec["last_checked"] = time.time()
    _persist()


def health_summary() -> str:
    """One-line summary of all faculty states — for eLo self-report."""
    parts = []
    for f, rec in _registry.items():
        st = rec["status"]
        if st == CONNECTED:
            parts.append(f"{f}: OK")
        elif st == DEGRADED:
            parts.append(f"{f}: DEGRADED ({rec['last_error'][:40]})")
        else:
            parts.append(f"{f}: OFFLINE ({rec['last_error'][:40]})")
    return " | ".join(parts)


def all_statuses() -> dict[str, str]:
    """Return {faculty: status} dict."""
    return {f: rec["status"] for f, rec in _registry.items()}


def _persist() -> None:
    try:
        tmp = _HEALTH_PATH + ".tmp"
        payload = {f: dict(rec) for f, rec in _registry.items()}
        payload["_ts"] = time.time()
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(tmp, _HEALTH_PATH)
    except Exception as e:
        _log.debug("faculty_health persist failed: %s", e)


# ── Genome-aware health surface (WO-CANON-XXII) ───────────────────────────────
# Per-faculty health keyed by genome name (e.g. "PerceptionFaculty").
# Supplements the four coarse buckets above; does not replace them.
# Health values mirror GenomeRegistry: CONNECTED | DEGRADED | OFFLINE | UNKNOWN.

import threading as _threading

_genome_registry: dict = {}
_genome_lock = _threading.Lock()


def genome_health_status(faculty_name: str) -> str:
    """Return CONNECTED | DEGRADED | OFFLINE | UNKNOWN for a genome-registered faculty."""
    with _genome_lock:
        return _genome_registry.get(faculty_name, {}).get("status", "UNKNOWN")


def mark_genome_degraded(faculty_name: str, reason: str = "") -> None:
    """Mark a genome-registered faculty as DEGRADED."""
    with _genome_lock:
        _genome_registry.setdefault(faculty_name, {"status": "CONNECTED", "last_error": ""})
        _genome_registry[faculty_name]["status"]     = "DEGRADED"
        _genome_registry[faculty_name]["last_error"] = reason
    _log.warning("Genome DEGRADED: %s — %s", faculty_name, reason)


def mark_genome_recovered(faculty_name: str) -> None:
    """Mark a genome-registered faculty as CONNECTED (recovered)."""
    with _genome_lock:
        _genome_registry.setdefault(faculty_name, {"status": "CONNECTED", "last_error": ""})
        _genome_registry[faculty_name]["status"]     = "CONNECTED"
        _genome_registry[faculty_name]["last_error"] = ""


def genome_health_summary() -> dict:
    """Return {faculty_name: status} for all genome-registered faculties."""
    with _genome_lock:
        return {k: v.get("status", "UNKNOWN") for k, v in _genome_registry.items()}
