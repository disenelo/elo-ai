"""
faculties/knowledge/social_dynamics_faculty.py — WO-SOCIAL-DYNAMICS-001

Social dynamics knowledge faculty. Retrieves social dynamics WKG claims and
injects them into Executive context (feeds CCM). This is the social intelligence
layer — distinct from language understanding and distinct from psychology.
This is knowing how to BE in a conversation.

Hard lane: social norms vary by context — never impose a default norm as universal.
Power dynamics: observe without exploiting or being unconsciously shaped by them.

Source: SOURCE_2026-09-27_DAVID_social_dynamics_knowledge_spec.md
"""

from __future__ import annotations

import logging
import os
import json
import re

_log = logging.getLogger(__name__)

# ── Hard lane note ─────────────────────────────────────────────────────────────

HARD_LANE_NOTE: str = (
    "[SOCIAL DYNAMICS KNOWLEDGE — hard lane: social norms vary by context and culture; "
    "never impose a default norm as universal. "
    "Recognise power dynamics without exploiting them or being unconsciously shaped by them. "
    "Social knowledge feeds how eLo is present — not a script to follow.]"
)

# ── Domain keywords ────────────────────────────────────────────────────────────

_SOCIAL_KEYWORDS: frozenset[str] = frozenset({
    "conversation", "turn", "silence", "speak", "speaking", "listen", "listening",
    "challenge", "pushback", "push back", "celebrate", "celebration", "achievement",
    "ask", "question", "clarify", "boundary", "boundaries", "intimacy", "intimate",
    "professional", "casual", "formal", "informal", "register", "etiquette",
    "humour", "humor", "funny", "joke", "laugh", "appropriate", "inappropriate",
    "social", "dynamics", "context", "power", "hierarchy", "role", "relationship",
    "norms", "norm", "culture", "cultural", "politeness", "polite", "rude",
    "when to", "group", "community", "belonging", "exclusion",
    "communication style", "communication", "subtext", "what's appropriate",
    "vent", "venting", "thinking aloud", "thinking out loud", "space",
})

_SOCIAL_DOMAIN_TAG = "domain: social_dynamics"

# ── Graph path ─────────────────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_GRAPH_PATH = os.path.join(_ROOT, "relationships", "world_graph.json")


def _load_social_claims() -> list[dict]:
    """Load all social-dynamics WKG claims. Reloads from disk each call."""
    try:
        with open(_GRAPH_PATH, encoding="utf-8") as f:
            g = json.load(f)
        return [
            c for c in g.get("wkg_claims", [])
            if _SOCIAL_DOMAIN_TAG in (c.get("notes") or "")
        ]
    except Exception as e:
        _log.warning("social_dynamics_faculty: could not load graph: %s", e)
        return []


def is_domain_trigger(text: str) -> bool:
    """Return True if text contains social-dynamics-domain keywords."""
    lowered = text.lower()
    return any(kw in lowered for kw in _SOCIAL_KEYWORDS)


def query(
    text: str,
    max_results: int = 4,
) -> list[dict]:
    """
    Query social dynamics WKG claims relevant to `text`.

    Returns list of claim dicts with `_score` field.
    """
    claims = _load_social_claims()
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
    Return a context injection string for social dynamics knowledge relevant to `text`.
    Always includes the hard lane note. Empty string if no relevant claims found.
    """
    claims = query(text, max_results=max_results)
    if not claims:
        return ""

    lines = [HARD_LANE_NOTE]
    for c in claims:
        interp = c.get("interpretation") or c.get("notes") or ""
        lines.append(f"  [SOCIAL] {interp}")
    return "\n".join(lines)
