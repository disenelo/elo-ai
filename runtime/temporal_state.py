"""
runtime/temporal_state.py — Temporal Awareness

eLo must distinguish:
  "I am doing"    vs  "I did"             (now vs past)
  "I want to do"  vs  "I did"             (plan vs execution)
  "we discussed"  vs  "we decided"        (conversation vs intention)
  "we decided"    vs  "we implemented"    (intention vs action)
  "implemented"   vs  "verified"          (action vs confirmed outcome)

Without temporal clarity, everything collapses into undifferentiated present.

This module reads:
  1. memory.intentions — ACTIVE / DEFERRED / RESUMED state machine
  2. data/spg_signals.jsonl — recent interaction record
  3. data/intentions.json — intentions history (if populated)

And provides a compact [TEMPORAL STATE] prompt block that makes the
distinction explicit to the LLM, grounded in actual stored state — not
generated from nowhere.

Answers from the extended question list:
  IS ELO: — Temporally Aware?
    - does eLo distinguish 'I did' from 'I am doing'?
    - does eLo distinguish 'we decided' from 'we implemented'?
    - can eLo recover an old thread without confusing it with the present?
  IS ELO: — Intentions & Continuity
    - can eLo maintain unfinished intentions?
    - can eLo remember why something was deferred?
  THE REALLY HARD TEST
    - show me where temporal state is stored → data/intentions.json + spg_signals.jsonl
    - show me where it is retrieved → temporal_state_prompt_block()
    - show me where it affects Executive → wired into server.py system prompt
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)

_ROOT    = Path(__file__).parent.parent
_SIGNALS = _ROOT / "data" / "spg_signals.jsonl"

RECENT_SIGNALS_N = 10  # look back this many SPG signals for "recent" context


@dataclass
class TemporalFrame:
    """
    A snapshot of eLo's temporal state.

    Distinguishes: active (now) / deferred (paused) / recently_completed (just done)
    / planned (not yet started) / in_discussion (conversational only, not decided).
    """
    active_intentions:   list[str] = field(default_factory=list)  # "I am doing"
    deferred_intentions: list[str] = field(default_factory=list)  # "I had planned but paused"
    deferred_reasons:    list[str] = field(default_factory=list)  # "I paused because"
    recent_signal_types: list[str] = field(default_factory=list)  # last N SPG signal types
    recent_edge_hints:   list[str] = field(default_factory=list)  # last N edge_hints
    total_signals:       int = 0
    has_active:          bool = False
    has_deferred:        bool = False

    @property
    def is_empty(self) -> bool:
        return not (self.active_intentions or self.deferred_intentions or self.recent_edge_hints)


def _read_recent_signals(n: int = RECENT_SIGNALS_N) -> tuple[list[str], list[str], int]:
    """Read the last n SPG signals. Returns (signal_types, edge_hints, total)."""
    if not _SIGNALS.exists():
        return [], [], 0

    all_signals: list[dict] = []
    try:
        with open(_SIGNALS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    all_signals.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as exc:
        _log.warning("temporal_state: read error: %s", exc)
        return [], [], 0

    recent = all_signals[-n:] if len(all_signals) >= n else all_signals
    signal_types = [s.get("signal_type", "") for s in recent if s.get("signal_type")]
    edge_hints   = [s.get("edge_hint", "")   for s in recent if s.get("edge_hint")]
    return signal_types, edge_hints, len(all_signals)


def _read_intentions() -> tuple[list[str], list[str], list[str]]:
    """
    Read open intentions from memory.intentions.
    Returns (active_texts, deferred_texts, deferred_reasons).
    Falls back gracefully if the intentions store is empty.
    """
    try:
        from memory.intentions import open_intentions, STATUS_ACTIVE, STATUS_DEFERRED, STATUS_RESUMED
        open_list = open_intentions()
        active   = [i.text[:80] for i in open_list if i.status in (STATUS_ACTIVE, STATUS_RESUMED)]
        deferred = [i.text[:80] for i in open_list if i.status == STATUS_DEFERRED]
        reasons  = []
        for i in open_list:
            if i.status == STATUS_DEFERRED:
                r = getattr(i, "deferred_reason", "") or ""
                reasons.append(r[:60] if r else "no reason recorded")
        return active, deferred, reasons
    except Exception as exc:
        _log.debug("temporal_state: intentions unavailable: %s", exc)
        return [], [], []


def read_temporal_frame() -> TemporalFrame:
    """
    Build the current temporal frame from available state.
    Always returns a valid TemporalFrame — never raises.
    """
    try:
        active, deferred, reasons = _read_intentions()
        sig_types, edge_hints, total = _read_recent_signals()
        return TemporalFrame(
            active_intentions   = active,
            deferred_intentions = deferred,
            deferred_reasons    = reasons,
            recent_signal_types = sig_types,
            recent_edge_hints   = edge_hints,
            total_signals       = total,
            has_active          = bool(active),
            has_deferred        = bool(deferred),
        )
    except Exception as exc:
        _log.warning("temporal_state: read_temporal_frame failed: %s", exc)
        return TemporalFrame()


def temporal_state_prompt_block() -> str:
    """
    Build a compact prompt block making eLo's temporal situation explicit.

    The block anchors eLo in what is currently happening, what is paused,
    and what the recent interaction record shows — enabling clear distinction
    between "I am doing" / "I did" / "I want to do" / "I deferred".

    Returns "" when there is nothing temporal to report (no active/deferred
    intentions, no signal history). Returns "" on any error (non-blocking).
    """
    try:
        frame = read_temporal_frame()
        if frame.is_empty:
            return ""

        lines = [
            "[TEMPORAL STATE — now vs past vs planned]",
            "  Use this to distinguish: 'I am doing' / 'I did' / 'I want to do' / 'I deferred'.",
        ]

        if frame.active_intentions:
            lines.append("  NOW (ACTIVE — I am holding these threads):")
            for text in frame.active_intentions[:3]:
                lines.append(f"    • {text}")

        if frame.deferred_intentions:
            lines.append("  PAUSED (DEFERRED — I planned this but paused):")
            for text, reason in zip(frame.deferred_intentions[:3], frame.deferred_reasons):
                lines.append(f"    • {text} [paused because: {reason}]")

        if frame.recent_edge_hints:
            unique_edges = list(dict.fromkeys(frame.recent_edge_hints))[:4]
            lines.append(f"  RECENT INTERACTION PATTERN: {' → '.join(unique_edges)}")

        if frame.total_signals:
            lines.append(f"  Total interaction record: {frame.total_signals} signals")

        lines.append(
            "  Do NOT confuse 'we discussed X' with 'we decided X' with 'X is implemented'."
        )
        return "\n".join(lines)

    except Exception as exc:
        _log.warning("temporal_state_prompt_block failed (non-fatal): %s", exc)
        return ""
