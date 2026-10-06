"""
memory/spg_capture.py — WO-SPG-CAPTURE-001: SPG Passive Memory Link Signal Logger

Passively captures signals needed to demonstrate SPG G-2/G-5 gates when R&D is ready.
SPG is NOT in production. This module writes signals only — no integration into the main turn path or capability layer.

Authority: David L3 directive 2026-09-05
Source: SOURCE_2026-09-05_DAVID_L3_SPG_reopen_memory_links.md
"""
from __future__ import annotations

import gzip
import json
import logging
import os
import time
from pathlib import Path
from threading import Lock

_log = logging.getLogger(__name__)

_ROOT      = Path(__file__).parent.parent
_DATA_DIR  = _ROOT / "data"
_SIGNALS   = _DATA_DIR / "spg_signals.jsonl"
_MAX_BYTES = 10 * 1024 * 1024   # 10MB — rotate threshold
_KEEP_DAYS = 30

_VALID_SIGNAL_TYPES = frozenset({
    "memory_write",
    "memory_read",
    "significance_spike",
    "relationship_shift",
    "continuity_link",
    "embodiment_transition",
    "creation_event",
})


class SPGCapture:
    """
    Passive logger for SPG (Shared Presence Graph) memory-link signals.

    Write-only from the turn loop's perspective. Never blocks a turn — writes are
    append-only and non-critical (failures are logged, never raised).

    Usage:
        spg = SPGCapture()
        spg.log("significance_spike", turn_id="t-001", significance=scores)
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path else _SIGNALS
        self._lock = Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        signal_type: str,
        *,
        turn_id:      str        = "",
        significance: dict       = None,
        memory_keys:  list[str]  = None,
        context_tags: list[str]  = None,
        relationship: str | None = None,
        embodiment:   str        = "terminal",
        edge_hint:    str | None = None,
    ) -> None:
        """
        Append one SPG signal entry to data/spg_signals.jsonl.
        Non-blocking — failures are logged, never raised.

        Args:
            signal_type: one of VALID_SIGNAL_TYPES
            turn_id:     current turn ID (empty string if unavailable)
            significance: SP-29 score dict (if available)
            memory_keys: WKG keys touched this turn
            context_tags: topic/domain tags from CCM
            relationship: current relationship context string
            embodiment:  surface — "terminal" / "desktop" / "voice" / "mobile"
            edge_hint:   optional heuristic link hint for graph edges
        """
        if signal_type not in _VALID_SIGNAL_TYPES:
            _log.debug("SPGCapture: unknown signal_type %r — skipped", signal_type)
            return

        # ROOT-4. Measured 2026-10-06: 13,877 of 13,919 signals carried
        # turn_id="" — 99.7%. spg_graph makes node ids as
        # f"{turn_id}:{signal_type}", so all of them collapsed onto the same
        # few nodes and 13,919 signals produced 44. The pattern graph could
        # not form, which is the mechanical reason "SPG patterns are not
        # active".
        #
        # Callers simply do not pass it, and two of the busiest live in
        # runtime/spine/spine.py (Builder 1's file), so the fix belongs here
        # where it covers every caller at once.
        #
        # experience_id is the canonical turn identity and its own docstring
        # says so: "any write site within the same turn calls get()". This is
        # a write site within the turn that never did.
        if not str(turn_id or "").strip():
            try:
                from runtime.experience_id import get as _xid_get
                turn_id = _xid_get() or ""
            except Exception:
                turn_id = ""

        entry = {
            "ts":           time.time(),
            "turn_id":      turn_id,
            "signal_type":  signal_type,
            "significance": significance or {},
            "memory_keys":  memory_keys or [],
            "context_tags": context_tags or [],
            "relationship": relationship,
            "embodiment":   embodiment,
            "edge_hint":    edge_hint,
        }

        try:
            with self._lock:
                self._rotate_if_needed()
                with self._path.open("a", encoding="utf-8") as _f:
                    _f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except Exception as _e:
            _log.warning("SPGCapture.log failed (non-blocking): %s", _e)

    def _rotate_if_needed(self) -> None:
        """Rotate spg_signals.jsonl when it exceeds _MAX_BYTES. Keeps last 30 days."""
        if not self._path.exists():
            return
        if self._path.stat().st_size < _MAX_BYTES:
            return

        _date_tag = time.strftime("%Y%m%d_%H%M%S")
        _rotated  = self._path.parent / f"spg_signals_{_date_tag}.jsonl.gz"
        try:
            with self._path.open("rb") as _src:
                with gzip.open(_rotated, "wb") as _dst:
                    _dst.write(_src.read())
            self._path.unlink()
            _log.info("SPGCapture: rotated to %s", _rotated.name)
            self._purge_old(keep_days=_KEEP_DAYS)
        except Exception as _e:
            _log.warning("SPGCapture: rotation failed: %s", _e)

    def _purge_old(self, keep_days: int) -> None:
        """Delete rotated files older than keep_days."""
        _cutoff = time.time() - (keep_days * 86400)
        for _f in self._path.parent.glob("spg_signals_*.jsonl.gz"):
            try:
                if _f.stat().st_mtime < _cutoff:
                    _f.unlink()
                    _log.info("SPGCapture: purged %s", _f.name)
            except Exception:
                pass


# ── Module-level singleton for convenience ───────────────────────────────────
_DEFAULT: SPGCapture | None = None


def get_capture() -> SPGCapture:
    """Return the module-level SPGCapture singleton (lazy-init)."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = SPGCapture()
    return _DEFAULT
