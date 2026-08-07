"""
tools/grocery_agent.py — UK grocery price estimator for eLo OS.

Detects a shopping list + UK store name in natural language, estimates
current prices per item using GPT-4o-mini, and returns an itemised
breakdown with total.

Reuses OPENAI_API_KEY already in .env — no new key needed.

Examples it handles:
    "eggs potatoes chorizo parma ham sausages total cost at sainsburys hackney wick"
    "milk bread butter how much at tesco?"
    "chicken thighs onions garlic ginger what would that cost at waitrose"
"""
from __future__ import annotations

import os
import re
try:
    import httpx as _httpx
except ImportError:
    _httpx = None

_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

# ── Store detection ───────────────────────────────────────────────────────────

_STORE_NAMES = (
    "sainsbury", "tesco", "waitrose", "asda", "morrisons", "lidl", "aldi",
    "co-op", "coop", "m&s", "marks and spencer", "marks & spencer",
    "iceland", "ocado", "booths", "budgens", "spar",
)

_STORE_RE = re.compile(
    r'\b(?:sainsbury[\'s]*(?:\s+local)?|tesco(?:\s+express|metro|extra)?'
    r'|waitrose(?:\s+&\s+partners)?|asda|morrisons|lidl|aldi'
    r'|co[\-\s]?op|m\s*&?\s*s|marks\s+(?:and|&)\s+spencer'
    r'|iceland|ocado|budgens|spar|booths)'
    r'(?:\s+[\w\s]{0,30})?',   # capture trailing location e.g. "hackney wick"
    re.IGNORECASE,
)

# ── Price/cost question detection ─────────────────────────────────────────────

_PRICE_RE = re.compile(
    r'\b(?:total\s+(?:cost|price)|how\s+much|what\s+(?:would|will|does|is)\s*(?:that|this|it)?\s*cost'
    r'|what(?:\'s|\s+is)\s+the\s+(?:total|cost|price)|price|cost)\b',
    re.IGNORECASE,
)


def is_grocery_intent(text: str) -> bool:
    """Return True when text looks like a grocery price query."""
    t = text.lower()
    return bool(_PRICE_RE.search(t)) and any(s in t for s in _STORE_NAMES)


# ── LLM pricing call ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a UK grocery pricing assistant. Given a shopping list and a specific UK supermarket, \
provide a realistic itemised price breakdown and total.

Rules:
- Use current approximate UK retail prices (2024-2025) for the named store's price tier.
- Pick the most common / standard product variant for each item (e.g. medium free-range eggs 12-pack).
- Format your response EXACTLY like this — no preamble, no extra text:

STORE: {store name and location if given}
ITEMS:
- {Item name} ({size/variant}): £{price}
- {Item name} ({size/variant}): £{price}
TOTAL: £{total}
NOTE: {one-line note about price variability, loyalty card deals, etc.}

If a specific store location is mentioned, note the store address if you know it. \
If you don't know the exact location, omit the address. \
Keep prices realistic — do not invent implausible prices."""


def _call_llm(query: str) -> str:
    if not _OPENAI_KEY:
        raise ValueError("OPENAI_API_KEY not set — grocery pricing requires GPT-4o-mini")

    if _httpx is None:
        raise RuntimeError("grocery_agent requires httpx — pip install httpx")
    resp = _httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {_OPENAI_KEY}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": query},
            ],
            "max_tokens": 400,
            "temperature": 0.2,
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


# ── main entry ────────────────────────────────────────────────────────────────

def agent(query: str) -> str:
    """
    Main entry point for tool_router.
    Returns a GROCERY context string for eLo to relay.
    """
    raw = _call_llm(query)
    return f"GROCERY ESTIMATE:\n{raw}"
