"""
self_improvement/correction_store.py — WO-027: reviewed correction-memory (ICL).

Stores (input, corrected_response, why, trace) pairs; retrieves semantically
similar ones on each turn; injects as few-shot examples into the system prompt.

Review tiers (David 2026-08-02 — corrections shape eLo's mind):
  TIER_AUTO  (green) — safe/mechanical fixes; can enter automatically after tests pass.
  TIER_DAVID (red)   — voice, personality, routing; requires David's explicit review.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

TIER_AUTO  = "green"
TIER_DAVID = "red"

_RED_KEYWORDS = ("voice", "personality", "routing", "register", "tone", "identity",
                 "character", "style", "persona", "emotion", "warmth", "slang")

_LEDGER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "self", "corrections_ledger.jsonl",
)


def _classify_tier(why: str) -> str:
    """Auto-classify tier from the reason text. Red if it touches personality/routing."""
    lower = why.lower()
    for kw in _RED_KEYWORDS:
        if kw in lower:
            return TIER_DAVID
    return TIER_AUTO


def store_correction(
    input_text:          str,
    corrected_response:  str,
    why:                 str,
    trace:               Optional[dict] = None,
    reviewed:            bool = False,
    tier:                Optional[str]  = None,
) -> bool:
    """
    Store a reviewed correction in the ledger.

    Red-tier corrections (voice/personality/routing) must have reviewed=True.
    Returns True on success, False if blocked by the review gate.
    """
    if tier is None:
        tier = _classify_tier(why)

    if tier == TIER_DAVID and not reviewed:
        return False  # blocked — David must review before this enters memory

    entry = {
        "id":                 f"CX-{int(time.time() * 1000) % 10_000_000:07d}",
        "input":              input_text,
        "corrected_response": corrected_response,
        "why":                why,
        "trace":              trace or {},
        "tier":               tier,
        "reviewed":           reviewed,
        "ts":                 time.time(),
    }
    try:
        os.makedirs(os.path.dirname(_LEDGER_PATH), exist_ok=True)
        with open(_LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception:
        return False


def _load_ledger() -> list[dict]:
    """Load all reviewed corrections from the ledger."""
    entries: list[dict] = []
    try:
        with open(_LEDGER_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("reviewed") or e.get("tier") == TIER_AUTO:
                        entries.append(e)
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return entries


def search_corrections(input_text: str, top_k: int = 3) -> list[dict]:
    """
    Semantic search for past corrections relevant to this input.
    Falls back to exact-prefix match if embeddings are unavailable.
    Returns a list of up to top_k correction dicts, most relevant first.
    """
    entries = _load_ledger()
    if not entries:
        return []

    candidates = [e["input"] for e in entries]

    try:
        from memory.embedding_store import search as embed_search
        ranked = embed_search(input_text, candidates, top_k=top_k)
        if ranked:
            scored = {text: score for text, score in ranked}
            return sorted(
                [e for e in entries if e["input"] in scored],
                key=lambda e: scored.get(e["input"], 0.0),
                reverse=True,
            )[:top_k]
    except Exception:
        pass

    # Fallback: substring match on the first 30 chars
    prefix = input_text[:30].lower()
    matches = [e for e in entries if prefix[:10] in e["input"].lower()]
    return matches[:top_k]


def inject_corrections(corrections: list[dict], system_prompt: str) -> str:
    """
    Prepend relevant past corrections as few-shot examples into the system prompt.
    Returns the enriched system prompt. Pure — does not modify system_prompt in place.
    """
    if not corrections:
        return system_prompt

    lines = ["[PAST CORRECTIONS — examples of how to handle similar inputs correctly]"]
    for c in corrections:
        lines.append(f'Input: "{c["input"]}"')
        lines.append(f'Correct response: "{c["corrected_response"]}"')
        if c.get("why"):
            lines.append(f'Why: {c["why"]}')
        lines.append("---")

    block = "\n".join(lines)
    return block + "\n\n" + system_prompt
