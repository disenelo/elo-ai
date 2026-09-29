"""
memory/novelty_detector.py — Novelty and prediction-error detector.

eLo as a system capable of:
  - recognising novel situations it hasn't encountered before
  - detecting when its predictions about the world are wrong (prediction error)
  - expressing genuine surprise, not performed reactions

Answers from the 315 questions:
  "a system capable of recognising novel situations it hasn't encountered before?"
  "a system capable of detecting when its predictions about the world are wrong?"
  "a system capable of expressing genuine surprise?"
  "a system that knows when something is new vs familiar?"

How it works
============
1. Reads data/spg_signals.jsonl at first call (lazy load, cached).
2. Builds a base-rate model: how often does each edge_hint / context_tag appear?
3. Scores a new signal: rare edge_hints or unseen context_tags → high novelty.
4. Above threshold → inject a prompt block so eLo can honestly acknowledge novelty.

This module observes — it does NOT diagnose or interpret.
The prompt block states facts (rarity scores), not judgements.
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

_log = logging.getLogger(__name__)

_ROOT      = Path(__file__).parent.parent
_SIGNALS   = _ROOT / "data" / "spg_signals.jsonl"

# Score threshold above which we inject a prompt block.
# 0.4 means at least a rare edge_hint or two unseen context_tags.
_NOVELTY_THRESHOLD = 0.40

# Weights for each novelty signal dimension
_W_EDGE_UNSEEN   = 0.90   # edge_hint never seen before
_W_EDGE_RARE     = 0.60   # edge_hint seen < 1% of signals
_W_EDGE_UNCOMMON = 0.30   # edge_hint seen 1–5% of signals
_W_TAG_UNSEEN    = 0.35   # context_tag never seen
_W_TAG_RARE      = 0.20   # context_tag < 5 occurrences


@dataclass
class NoveltyScore:
    score: float
    edge_hint: str
    edge_rate: float               # historical frequency of this edge_hint
    unseen_tags: list[str] = field(default_factory=list)
    rare_tags:   list[str] = field(default_factory=list)

    @property
    def is_novel(self) -> bool:
        return self.score >= _NOVELTY_THRESHOLD


class _FrequencyModel:
    """
    Frequency model built from historical SPG signals.
    Thread-safe, loaded once.
    """

    def __init__(self) -> None:
        self._edge_counts:   Counter[str] = Counter()
        self._tag_counts:    Counter[str] = Counter()
        self._total_signals: int = 0
        self._loaded = False
        self._lock = Lock()

    def load(self, path: Path) -> None:
        with self._lock:
            if self._loaded:
                return
            try:
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            sig = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        hint = sig.get("edge_hint") or ""
                        if hint:
                            self._edge_counts[hint] += 1
                        for tag in (sig.get("context_tags") or []):
                            if tag:
                                self._tag_counts[tag] += 1
                        self._total_signals += 1
                self._loaded = True
                _log.debug(
                    "novelty_detector: loaded %d signals, %d edge types, %d tag types",
                    self._total_signals,
                    len(self._edge_counts),
                    len(self._tag_counts),
                )
            except Exception as exc:
                _log.warning("novelty_detector: could not load signals: %s", exc)
                self._loaded = True   # don't retry on failure

    def edge_rate(self, hint: str) -> float:
        """Fraction of signals that had this edge_hint (0.0 if unseen)."""
        if self._total_signals == 0 or not hint:
            return 0.0
        return self._edge_counts.get(hint, 0) / self._total_signals

    def tag_count(self, tag: str) -> int:
        return self._tag_counts.get(tag, 0)

    def known_edge_hints(self) -> frozenset[str]:
        return frozenset(self._edge_counts.keys())

    def known_tags(self) -> frozenset[str]:
        return frozenset(self._tag_counts.keys())

    @property
    def loaded(self) -> bool:
        return self._loaded


_MODEL = _FrequencyModel()


def _ensure_loaded(path: Path | None = None) -> None:
    if not _MODEL.loaded:
        _MODEL.load(path or _SIGNALS)


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_novelty(
    edge_hint:    str        = "",
    context_tags: list[str] = None,
    *,
    signals_path: Path | None = None,
) -> NoveltyScore:
    """
    Score the novelty of a single turn's signal properties.

    Args:
        edge_hint:    The edge_hint from the current SPG signal (or predicted).
        context_tags: Context tags from the current turn.
        signals_path: Override path to spg_signals.jsonl (for testing).

    Returns:
        NoveltyScore with score 0.0–1.0 and supporting detail.
    """
    _ensure_loaded(signals_path)
    context_tags = context_tags or []

    score = 0.0
    edge_rate = _MODEL.edge_rate(edge_hint)
    known_edges = _MODEL.known_edge_hints()

    # ── Edge hint contribution ─────────────────────────────────────────────────
    if edge_hint:
        if edge_hint not in known_edges:
            score += _W_EDGE_UNSEEN
        elif edge_rate < 0.01:
            score += _W_EDGE_RARE
        elif edge_rate < 0.05:
            score += _W_EDGE_UNCOMMON

    # ── Context tag contributions ──────────────────────────────────────────────
    known_tags = _MODEL.known_tags()
    unseen_tags: list[str] = []
    rare_tags:   list[str] = []

    for tag in context_tags:
        if tag not in known_tags:
            score += _W_TAG_UNSEEN
            unseen_tags.append(tag)
        elif _MODEL.tag_count(tag) < 5:
            score += _W_TAG_RARE
            rare_tags.append(tag)

    score = min(score, 1.0)

    return NoveltyScore(
        score=score,
        edge_hint=edge_hint,
        edge_rate=edge_rate,
        unseen_tags=unseen_tags,
        rare_tags=rare_tags,
    )


# ── Prompt block ──────────────────────────────────────────────────────────────

def novelty_prompt_block(
    edge_hint:    str       = "",
    context_tags: list[str] = None,
    *,
    threshold:    float     = _NOVELTY_THRESHOLD,
    signals_path: Path | None = None,
) -> str:
    """
    Build a compact prompt block if this turn scores as genuinely novel.

    Returns "" if the turn is familiar — never adds filler.
    Returns "" on any error (non-blocking).
    """
    try:
        ns = score_novelty(edge_hint, context_tags, signals_path=signals_path)
        if not ns.is_novel or ns.score < threshold:
            return ""

        lines = [
            f"[NOVELTY DETECTION — score {ns.score:.2f} / 1.0]",
            "This turn contains elements that are statistically rare in prior experience.",
        ]

        if ns.edge_hint:
            known = _MODEL.known_edge_hints()
            if ns.edge_hint not in known:
                lines.append(f"  Edge hint '{ns.edge_hint}' has never occurred before.")
            else:
                pct = ns.edge_rate * 100
                lines.append(f"  Edge hint '{ns.edge_hint}' is rare ({pct:.2f}% of prior turns).")

        if ns.unseen_tags:
            lines.append(f"  Context tags not previously seen: {', '.join(ns.unseen_tags)}")
        if ns.rare_tags:
            lines.append(f"  Rarely-seen context tags: {', '.join(ns.rare_tags)}")

        lines.append(
            "Acknowledge novelty honestly if it's relevant — do not pretend familiarity."
        )
        return "\n".join(lines)

    except Exception as exc:
        _log.warning("novelty_prompt_block failed (non-fatal): %s", exc)
        return ""
