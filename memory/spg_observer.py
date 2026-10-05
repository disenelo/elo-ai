"""
memory/spg_observer.py — WO-SPG-PATTERN-001

SPG Pattern Observer: reads spg_signals.jsonl and produces SPGObservation objects
that describe recurring behavioural patterns across turns.

David L3 ruling (2026-09-27):
  "SPG is multi-role. Its job is: notice what is significant, recurring, or changing.
   It is an observer — it does not interpret, diagnose, or decide. It reports patterns.
   The Executive decides whether they matter now."

SPG outputs are observations: "David switches projects when blocked"
NOT interpretations: "David has commitment issues."

Significance restraint (David L3 — 2026-09-27):
  - Minimum 3 distinct-context occurrences before CANDIDATE → EMERGING
  - Single-session co-occurrence noted, not flagged
  - Status: CANDIDATE → EMERGING → ESTABLISHED (never skip)

What is currently observable from spg_signals.jsonl:
  - edge_hint (executive action per turn): reflect/answer/build/ground/celebrate/connect
  - signal_type: relationship_shift / memory_write / continuity_link
  - context_tags: sparse but present (social_reflex, tier0, tier1)
  - significance.overall: currently all 0.3 (backfill) — waiting for live enrichment
"""
from __future__ import annotations

import json
import logging
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterator

_log = logging.getLogger(__name__)

_ROOT        = Path(__file__).parent.parent
_SIGNALS     = _ROOT / "data" / "spg_signals.jsonl"
_MAX_SIGNALS = 5_000   # read only the most recent N for performance

# ── Schema ────────────────────────────────────────────────────────────────────

STATUS_CANDIDATE  = "CANDIDATE"
STATUS_EMERGING   = "EMERGING"
STATUS_ESTABLISHED = "ESTABLISHED"
STATUS_DECLINING  = "DECLINING"

# Minimum occurrences per status tier
_MIN_EMERGING    = 3
_MIN_ESTABLISHED = 20

PATTERN_TYPE_ACTION      = "action"        # recurring executive actions
PATTERN_TYPE_RELATIONAL  = "relational"    # relationship-shift patterns
PATTERN_TYPE_CONTINUITY  = "continuity"    # cross-session continuity links
PATTERN_TYPE_CONTEXT     = "context_tag"   # recurring topic/context tags


@dataclass
class SPGObservation:
    pattern_id:       str
    pattern_type:     str
    observation:      str
    evidence_keys:    list[str]   = field(default_factory=list)
    first_seen:       float       = 0.0
    last_seen:        float       = 0.0
    recurrence_count: int         = 0
    significance_score: float     = 0.0
    status:           str         = STATUS_CANDIDATE

    def as_dict(self) -> dict:
        return asdict(self)

    def as_prompt_line(self) -> str:
        age_days = (time.time() - self.first_seen) / 86400
        return (
            f"[{self.status}] {self.observation} "
            f"(seen {self.recurrence_count}×, over ~{age_days:.0f} days)"
        )


# ── Signal loader ─────────────────────────────────────────────────────────────

def _load_recent_signals(max_n: int = _MAX_SIGNALS) -> list[dict]:
    """Load the most recent N signals from spg_signals.jsonl."""
    if not _SIGNALS.exists():
        return []
    signals: list[dict] = []
    try:
        with _SIGNALS.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    signals.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return signals[-max_n:]
    except Exception as exc:
        _log.warning("SPG: failed to load signals: %s", exc)
        return []


# ── Pattern detectors ─────────────────────────────────────────────────────────

def _action_patterns(signals: list[dict]) -> list[SPGObservation]:
    """
    Detect recurring executive action patterns from edge_hint values.

    edge_hint tracks the executive action chosen per turn (reflect / answer /
    build / ground / celebrate / connect / challenge). Patterns here tell eLo
    which modes it gravitates toward across its history.
    """
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in signals:
        # str(... or "") rather than .get(key, ""): the default only applies
        # when the key is ABSENT, and 43 of the 14707 live signal rows carry
        # edge_hint: null, where .get returns None and .strip() raises.
        # The identical line took habit_tracker out entirely — it read the
        # whole file, the AttributeError escaped a JSONDecodeError-only
        # handler, and 7070 observations reported as zero. This survives only
        # because the live caller reads a recent window and every null sits
        # 11556+ rows from the end. Latent, not live — until one lands in the
        # window.
        hint = str(s.get("edge_hint") or "").strip()
        if hint:
            buckets[hint].append(s)

    total = sum(len(v) for v in buckets.values()) or 1
    observations: list[SPGObservation] = []

    for action, entries in sorted(buckets.items(), key=lambda x: -len(x[1])):
        count = len(entries)
        if count < _MIN_EMERGING:
            continue
        pct  = round(count / total * 100)
        ts_s = entries[0].get("ts", 0.0)
        ts_e = entries[-1].get("ts", 0.0)

        if count >= _MIN_ESTABLISHED:
            status = STATUS_ESTABLISHED
        else:
            status = STATUS_EMERGING

        sig = round(min(1.0, count / max(total, 1) * 2), 3)

        obs = SPGObservation(
            pattern_id=f"action:{action}",
            pattern_type=PATTERN_TYPE_ACTION,
            observation=f"Across {total} logged turns, '{action}' was the dominant mode {pct}% of the time",
            evidence_keys=[f"edge_hint:{action}"],
            first_seen=ts_s,
            last_seen=ts_e,
            recurrence_count=count,
            significance_score=sig,
            status=status,
        )
        observations.append(obs)

    return observations


def _context_tag_patterns(signals: list[dict]) -> list[SPGObservation]:
    """
    Detect recurring context tags — topics that appear across multiple signals.
    """
    all_tags: Counter = Counter()
    tag_signals: dict[str, list[dict]] = defaultdict(list)
    for s in signals:
        for tag in s.get("context_tags", []):
            if tag:
                all_tags[tag] += 1
                tag_signals[tag].append(s)

    observations: list[SPGObservation] = []
    for tag, count in all_tags.most_common(10):
        if count < _MIN_EMERGING:
            continue
        entries = tag_signals[tag]
        ts_s = entries[0].get("ts", 0.0)
        ts_e = entries[-1].get("ts", 0.0)
        status = STATUS_ESTABLISHED if count >= _MIN_ESTABLISHED else STATUS_EMERGING
        obs = SPGObservation(
            pattern_id=f"context:{tag}",
            pattern_type=PATTERN_TYPE_CONTEXT,
            observation=f"Context tag '{tag}' appeared {count} times across recorded turns",
            evidence_keys=[f"context_tag:{tag}"],
            first_seen=ts_s,
            last_seen=ts_e,
            recurrence_count=count,
            significance_score=round(min(1.0, count / 100), 3),
            status=status,
        )
        observations.append(obs)

    return observations


def _continuity_patterns(signals: list[dict]) -> list[SPGObservation]:
    """
    Detect continuity_link signals — cross-session thread resumptions.
    Each continuity_link means eLo returned to an earlier thread.
    """
    clinks = [s for s in signals if s.get("signal_type") == "continuity_link"]
    if len(clinks) < _MIN_EMERGING:
        return []
    ts_s = clinks[0].get("ts", 0.0)
    ts_e = clinks[-1].get("ts", 0.0)
    status = STATUS_ESTABLISHED if len(clinks) >= _MIN_ESTABLISHED else STATUS_EMERGING
    return [
        SPGObservation(
            pattern_id="continuity:cross_session",
            pattern_type=PATTERN_TYPE_CONTINUITY,
            observation=f"Cross-session thread resumptions recorded: {len(clinks)} continuity links",
            evidence_keys=["signal_type:continuity_link"],
            first_seen=ts_s,
            last_seen=ts_e,
            recurrence_count=len(clinks),
            significance_score=0.7,
            status=status,
        )
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def detect_patterns(max_signals: int = _MAX_SIGNALS) -> list[SPGObservation]:
    """
    Read spg_signals.jsonl and return a list of SPGObservation objects.

    SPG never routes its own output. The caller (Executive / prompt builder)
    decides which observations to surface and how.

    Returns observations sorted by significance_score descending.
    Raises nothing — on any failure returns empty list.
    """
    try:
        signals = _load_recent_signals(max_signals)
        if not signals:
            return []

        observations: list[SPGObservation] = []
        observations.extend(_action_patterns(signals))
        observations.extend(_context_tag_patterns(signals))
        observations.extend(_continuity_patterns(signals))

        return sorted(observations, key=lambda o: -o.significance_score)
    except Exception as exc:
        _log.warning("SPG detect_patterns failed (non-fatal): %s", exc)
        return []


def top_observations(n: int = 3, max_signals: int = _MAX_SIGNALS) -> list[SPGObservation]:
    """Return the top N SPGObservations by significance."""
    return detect_patterns(max_signals)[:n]


def spg_prompt_block(n: int = 3) -> str:
    """
    Build a prompt block from the top N SPGObservations.

    Returns "" if no patterns found (never blocks the turn).
    Format mirrors habit emergent_block so prompt_builder can inject consistently.
    """
    try:
        obs = top_observations(n)
        if not obs:
            return ""
        lines = ["[SPG — OBSERVED PATTERNS: candidate significance, not declared meaning]"]
        for o in obs:
            lines.append(f"  • {o.as_prompt_line()}")
        return "\n".join(lines)
    except Exception as exc:
        _log.warning("SPG prompt block failed (non-fatal): %s", exc)
        return ""
