"""
tools/web_search.py — Web search for eLo OS via SerpAPI.

One key, multiple engines. eLo picks the right engine automatically
based on what's being asked:

  "find that video"       → YouTube
  "latest news on X"      → Google News
  "find an image of X"    → Google Images
  "look up X"             → Google Web (default)
  "find X on Amazon"      → Amazon
  "where is X"            → Google Maps

Falls back to DuckDuckGo if no key is set.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

_SERPAPI_KEY = lambda: os.environ.get("SERPAPI_KEY", "")

# WO-051: track which provider last served results so callers can surface fallback.
last_source: str = ""  # "serpapi" | "ddg" | ""


@dataclass
class SearchResult:
    title:   str
    url:     str
    snippet: str


# ── Engine routing ────────────────────────────────────────────────────────────

_ENGINE_TRIGGERS: dict[str, list[str]] = {
    "youtube": [
        "youtube", "find that video", "search youtube", "that video",
        "watch", "find a video", "video of", "video about", "clip of",
        "show me the video", "find the video",
    ],
    "google_news": [
        "latest news", "news on", "news about", "what's happening",
        "recent news", "in the news", "latest on", "breaking",
        "what happened with", "update on",
    ],
    "google_images": [
        "image of", "images of", "picture of", "pictures of",
        "what does it look like", "show me what", "find a photo",
        "find an image", "photo of",
    ],
    "amazon": [
        "amazon", "buy", "how much is", "price of", "find on amazon",
        "where to buy", "purchase",
    ],
    "google_maps": [
        "where is", "directions to", "find near", "near me",
        "address of", "location of", "how far is",
    ],
}


def _detect_engine(text: str) -> str:
    """Return the best SerpAPI engine for this query."""
    t = text.lower()
    for engine, triggers in _ENGINE_TRIGGERS.items():
        if any(tr in t for tr in triggers):
            return engine
    return "google"


def search(query: str, max_results: int = 5, engine: str = "") -> list[SearchResult]:
    """
    Search using the appropriate engine for this query.
    Auto-detects engine from query intent if not specified.
    Falls back to DuckDuckGo if no key or SerpAPI fails.
    Sets last_source to "serpapi" or "ddg" so callers can surface the fallback.
    """
    global last_source
    key = _SERPAPI_KEY()
    if key:
        chosen = engine or _detect_engine(query)
        results = _serp_search(query, key, max_results, engine=chosen)
        if results:
            last_source = "serpapi"
            return results
    last_source = "ddg"
    return _ddg_search(query, max_results)


def _serp_search(query: str, key: str, max_results: int, engine: str = "google") -> list[SearchResult]:
    try:
        import httpx
        params: dict = {
            "q":       query,
            "api_key": key,
            "engine":  engine,
            "hl":      "en",
            "gl":      "gb",
        }
        if engine == "google":
            params["num"] = max_results
        elif engine == "youtube":
            params["search_query"] = query
            del params["q"]
        elif engine == "amazon":
            params["amazon_domain"] = "amazon.co.uk"

        resp = httpx.get("https://serpapi.com/search.json", params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

        # Each engine returns results under a different key
        items = (
            data.get("organic_results")          # google
            or data.get("video_results")         # youtube
            or data.get("news_results")          # google_news
            or data.get("images_results")        # google_images
            or data.get("organic_results", [])   # amazon, maps
        ) or []

        results: list[SearchResult] = []
        for r in items[:max_results]:
            title   = r.get("title", "") or r.get("name", "")
            url     = r.get("link", "") or r.get("url", "") or r.get("thumbnail", "")
            snippet = (
                r.get("snippet", "")
                or r.get("description", "")
                or r.get("published_date", "")
                or r.get("duration", "")
            )
            if title:
                results.append(SearchResult(title=title, url=url, snippet=snippet))
        return results

    except Exception as e:
        import sys
        print(f"[web_search] SerpAPI ({engine}) failed: {e}", file=sys.stderr)
        return []


def _ddg_search(query: str, max_results: int) -> list[SearchResult]:
    """DuckDuckGo instant answers — no API key, limited but always available."""
    try:
        import httpx
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8.0,
        )
        resp.raise_for_status()
        data    = resp.json()
        results: list[SearchResult] = []

        # Abstract (main answer)
        if data.get("AbstractText"):
            results.append(SearchResult(
                title=   data.get("Heading", query),
                url=     data.get("AbstractURL", ""),
                snippet= data["AbstractText"][:300],
            ))

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(SearchResult(
                    title=   topic.get("Text", "")[:60],
                    url=     topic.get("FirstURL", ""),
                    snippet= topic.get("Text", "")[:200],
                ))
            if len(results) >= max_results:
                break

        return results
    except Exception as e:
        import sys
        print(f"[web_search] DDG failed: {e}", file=sys.stderr)
        return []


def format_for_context(results: list[SearchResult], max_chars: int = 800) -> str:
    """Format results as a compact context block for injection into system prompt."""
    if not results:
        return ""
    lines = ["[WEB_SEARCH_RESULTS]"]
    total = 0
    for r in results:
        entry = f"• {r.title}: {r.snippet}"
        if total + len(entry) > max_chars:
            break
        lines.append(entry)
        total += len(entry)
    return "\n".join(lines)


# ── Intent detection ──────────────────────────────────────────────────────────

_SEARCH_TRIGGERS = (
    "search for",
    "look that up",
    "look up",
    "find out",
    "what is ",
    "who is ",
    "when did ",
    "how does ",
    "can you search",
    "google that",
    "research that",
    "research ",
    "find me info",
    "find info",
    "what's the latest",
    "latest on ",
    "news on ",
    "find out about",
    "find that video",
    "search youtube",
    "find a video",
    "latest news",
    "find an image",
    "find a photo",
    "where to buy",
    "how much is",
    "where is ",
)


def is_search_intent(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in _SEARCH_TRIGGERS)


def extract_query(text: str) -> str:
    """Pull the search term out of a natural language request."""
    t = text.strip()
    for trigger in sorted(_SEARCH_TRIGGERS, key=len, reverse=True):
        if trigger in t.lower():
            idx = t.lower().index(trigger) + len(trigger)
            q = t[idx:].strip().strip("?.,!")
            if q:
                return q
    return t
