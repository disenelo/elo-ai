"""
tools/web_agent.py — web page fetch and summarise for eLo OS.

Extracts a URL from the query, fetches the page, strips HTML,
and summarises with GPT-4o-mini (falls back to a raw extract if no key).

No extra API key — reuses OPENAI_API_KEY already in .env.
"""
from __future__ import annotations

import os
import re
try:
    import httpx as _httpx
except ImportError:
    _httpx = None

_MAX_CHARS = 3500
_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}


# ── HTML stripping ────────────────────────────────────────────────────────────

def _strip_html(html: str) -> str:
    # Remove script + style blocks entirely
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>',  ' ', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all remaining tags
    html = re.sub(r'<[^>]+>', ' ', html)
    # Common HTML entities
    for ent, ch in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'),
                    ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'")]:
        html = html.replace(ent, ch)
    # Collapse whitespace
    return re.sub(r'\s+', ' ', html).strip()


# ── LLM summarise ─────────────────────────────────────────────────────────────

def _summarise(url: str, content: str) -> str:
    if not _OPENAI_KEY:
        # Raw extract — first 400 chars of stripped text
        return f"Page at {url}: {content[:400]}..."

    try:
        resp = _httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {_OPENAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Summarise the following web page content in 2-3 sentences. "
                            "Be direct and factual. No preamble or meta-commentary. "
                            "If it's a product, say what it is. If it's an article, say what it's about."
                        ),
                    },
                    {"role": "user", "content": f"URL: {url}\n\nContent:\n{content[:_MAX_CHARS]}"},
                ],
                "max_tokens": 220,
                "temperature": 0.2,
            },
            timeout=15.0,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return f"Page at {url}: {content[:400]}..."


# ── fetch ─────────────────────────────────────────────────────────────────────

def fetch_and_summarise(url: str) -> str:
    resp = _httpx.get(url, headers=_HEADERS, timeout=12.0, follow_redirects=True)
    resp.raise_for_status()
    raw     = _strip_html(resp.text)
    summary = _summarise(url, raw)
    return f"WEB ({url}): {summary}"


# ── intent detection ──────────────────────────────────────────────────────────

def is_web_intent(text: str) -> bool:
    has_url = bool(re.search(r'https?://', text))
    t = text.lower()
    has_trigger = bool(re.search(
        r'\b(?:summarise|summarize|read|open|check|what\s+does)\s+(?:this\s+)?(?:page|link|url|site|article)\b',
        t,
    ))
    return has_url or has_trigger


# ── main entry ────────────────────────────────────────────────────────────────

def agent(query: str) -> str:
    m = re.search(r'https?://[\w\-\._~:/?#\[\]@!$&\'()*+,;=%]+', query)
    if not m:
        raise ValueError("No URL found in query")
    return fetch_and_summarise(m.group(0))
