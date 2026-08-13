"""
memory/embedding_store.py — semantic memory search via OpenAI embeddings.

Embeds memory pack items once at session start, caches to disk.
Each turn: embed user input (1 API call) → cosine similarity → top-k memories.

Falls back silently to empty results when OPENAI_API_KEY is absent or API fails.
The attention layer treats empty results as "no boost" — keyword scoring takes over.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Optional

_CACHE_PATH  = os.path.join(os.path.dirname(__file__), "embedding_cache.json")
_EMBED_URL   = "https://api.openai.com/v1/embeddings"
_EMBED_MODEL = "text-embedding-3-small"

_cache:      dict[str, list[float]] = {}
_cache_hash: str = ""


# ── OpenAI embedding call ─────────────────────────────────────────────────────

def _embed(text: str) -> Optional[list[float]]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or not text.strip():
        return None
    try:
        import httpx
        resp = httpx.post(
            _EMBED_URL,
            json={"model": _EMBED_MODEL, "input": text[:8000]},
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
    except Exception:
        return None


# ── Cosine similarity ─────────────────────────────────────────────────────────

def _cosine(a: list[float], b: list[float]) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0


# ── Cache management ──────────────────────────────────────────────────────────

def _pack_hash(items: list[str]) -> str:
    return hashlib.md5(" ".join(items).encode()).hexdigest()[:12]


def warm(items: list[str]) -> None:
    """
    Pre-embed a list of memory items and cache them to disk.
    Safe to call at session start — no-ops when cache is fresh.
    """
    global _cache, _cache_hash

    if not os.environ.get("OPENAI_API_KEY"):
        return

    new_hash = _pack_hash([i for i in items if i])

    # Load from disk if hash matches
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("hash") == new_hash:
                _cache      = data.get("embeddings", {})
                _cache_hash = new_hash
                return
        except Exception:
            pass

    # Embed anything missing
    for item in items:
        if item and item.strip() and item not in _cache:
            vec = _embed(item)
            if vec:
                _cache[item] = vec

    _cache_hash = new_hash
    _flush()


def _flush() -> None:
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"hash": _cache_hash, "embeddings": _cache}, f)
    except Exception:
        pass


# ── Semantic search ───────────────────────────────────────────────────────────

def search(query: str, candidates: list[str], top_k: int = 8) -> list[tuple[str, float]]:
    """
    Rank candidates by semantic similarity to query.

    Returns list of (text, similarity_score) sorted descending.
    Returns [] if embeddings are unavailable — callers treat this as no boost.
    """
    if not os.environ.get("OPENAI_API_KEY") or not candidates:
        return []

    query_vec = _embed(query)
    if not query_vec:
        return []

    results: list[tuple[str, float]] = []
    for text in candidates:
        if not text or not text.strip():
            continue
        if text not in _cache:
            vec = _embed(text)
            if vec:
                _cache[text] = vec
        if text in _cache:
            results.append((text, _cosine(query_vec, _cache[text])))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
