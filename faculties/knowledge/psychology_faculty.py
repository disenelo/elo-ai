"""
faculties/knowledge/psychology_faculty.py — WO-KNOWLEDGE-PSYCHOLOGY-001

Psychology domain knowledge faculty. Retrieves psychology WKG claims and
injects them into Executive context. Enforces David's hard lane:

  General knowledge. Not diagnosis. Not interpretation back at the person.
  eLo uses its understanding to be a better presence — not to run an analysis.

Source: SOURCE_2026-09-27_DAVID_psychology_knowledge_spec.md
"""

from __future__ import annotations

import logging
import os
import json
import re
from typing import Optional

_log = logging.getLogger(__name__)

# ── Hard lane (verbatim from David L3) ────────────────────────────────────────

HARD_LANE_NOTE: str = (
    "[PSYCHOLOGY KNOWLEDGE — hard lane: general knowledge only. "
    "Do NOT diagnose, label, or interpret David's behaviour back at him. "
    "Use this understanding to be a more attuned presence, not an analyst.]"
)

# ── Domain keywords ────────────────────────────────────────────────────────────

_PSYCHOLOGY_KEYWORDS: frozenset[str] = frozenset({
    "emotion", "emotions", "emotional", "motivation", "motivated", "motivate",
    "habit", "habits", "attention", "focus", "distracted", "perception", "perceive",
    "learning", "learn", "memory", "remember", "remember", "recall", "forget",
    "social", "behaviour", "behavior", "communication", "communicate",
    "attachment", "attachment style", "group", "dynamics", "cognitive bias",
    "bias", "heuristic", "decision", "decide", "creativity", "creative", "block",
    "stress", "stressed", "fight flight", "freeze", "pattern", "behavioural",
    "psychology", "psychological", "trauma", "anxiety", "burnout", "overwhelm",
    "flow state", "flow", "motivation", "intrinsic", "extrinsic",
    "confirmation bias", "sunk cost", "availability heuristic", "anchoring",
})

_PSYCH_DOMAIN_TAG = "domain: psychology"

# ── Graph path ─────────────────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_GRAPH_PATH = os.path.join(_ROOT, "relationships", "world_graph.json")


def _load_psychology_claims() -> list[dict]:
    """Load all psychology-domain WKG claims. Reloads from disk each call (live edits)."""
    try:
        with open(_GRAPH_PATH, encoding="utf-8") as f:
            g = json.load(f)
        return [
            c for c in g.get("wkg_claims", [])
            if _PSYCH_DOMAIN_TAG in (c.get("notes") or "")
        ]
    except Exception as e:
        _log.warning("psychology_faculty: could not load graph: %s", e)
        return []


def is_domain_trigger(text: str) -> bool:
    """Return True if text contains psychology-domain keywords."""
    lowered = text.lower()
    return any(kw in lowered for kw in _PSYCHOLOGY_KEYWORDS)


def query(
    text: str,
    max_results: int = 4,
    include_hard_lane: bool = True,
) -> list[dict]:
    """
    Query psychology WKG claims relevant to `text`.

    Returns a list of claim dicts with an added `_score` field. Hard-lane
    enforcement: caller must include HARD_LANE_NOTE in any context injection.
    """
    claims = _load_psychology_claims()
    if not claims:
        return []

    tokens = {t for t in re.findall(r"\w+", text.lower()) if len(t) >= 5}
    if not tokens:
        return []
    scored: list[tuple[int, dict]] = []
    for claim in claims:
        interp = (claim.get("interpretation") or "").lower()
        notes  = (claim.get("notes") or "").lower()
        score  = sum(1 for t in tokens if t in interp or t in notes)
        if score > 0:
            scored.append((score, claim))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, claim in scored[:max_results]:
        out = dict(claim)
        out["_score"] = score
        results.append(out)
    return results


def context_block(
    text: str,
    max_results: int = 3,
) -> str:
    """
    Return a context injection string for psychology knowledge relevant to `text`.
    Always includes the hard lane note. Empty string if no relevant claims found.
    """
    claims = query(text, max_results=max_results)
    if not claims:
        return ""

    lines = [HARD_LANE_NOTE]
    for c in claims:
        interp = c.get("interpretation") or c.get("notes") or ""
        lines.append(f"  [PSYCHOLOGY] {interp}")
    return "\n".join(lines)
