"""
company_runtime/company_memory.py — durable company-level memory store (WO EA2-7).

The company's "what happened & why" — decisions, completions, milestones, notes —
distinct from eLo's personal vault (memory/). Pure store + retrieve: no board edits,
no LLM calls, no dependency on anything heavy.

ADDITIVE ONLY — never modifies the frozen cognitive kernel or company_state_writer.
Mirrors the atomic-write pattern of company_state_writer and the optional-embedding
fallback pattern of memory/embedding_store.

Storage: append-only JSONL at blender/company_memory.jsonl (default; overridable for tests).
Each line is one self-describing record — the file never rewrites, so history is durable
and a partial write can only ever affect the trailing line.

Canon:
  D-SESSIONS — recency is TIME-based (days), never counted in sessions.

Entry points:
  remember(kind, summary, detail="", wo=None, actor=None, tags=None) -> dict
  recall(query=None, kind=None, wo=None, since_days=None, limit=20)   -> list[dict]
  timeline(days=30)                                                    -> list[dict]
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import threading
import time

_logger = logging.getLogger(__name__)

_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STORE_PATH  = os.path.join(_ROOT, "blender", "company_memory.jsonl")

# valid company memory kinds — anything else is coerced to "note"
_KINDS: frozenset[str] = frozenset({"decision", "completion", "milestone", "note"})

# one lock per process guards the append so concurrent remember() calls never interleave
_write_lock = threading.Lock()

_SCHEMA = "company_memory/v1"


# ── Append-only writer (atomic per-line append + fsync) ───────────────────────

def _append(path: str, record: dict) -> bool:
    """
    Append one record as a single JSON line. Guarded by a lock and fsync'd so the
    store can never be left half-written mid-record. Returns True on success.
    """
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _write_lock:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception as exc:
            _logger.error("company_memory: append failed: %s", exc)
            return False


def _read_all(path: str) -> list[dict]:
    """Read every valid record. Malformed lines are skipped, never fatal."""
    records: list[dict] = []
    if not os.path.exists(path):
        return records
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if isinstance(rec, dict):
                        records.append(rec)
                except json.JSONDecodeError:
                    _logger.warning("company_memory: skipped malformed line")
                    continue
    except Exception as exc:
        _logger.error("company_memory: read failed: %s", exc)
    return records


# ── remember() ────────────────────────────────────────────────────────────────

def remember(
    kind: str,
    summary: str,
    detail: str = "",
    wo=None,
    actor=None,
    tags=None,
    store_path: str = _STORE_PATH,
) -> dict | None:
    """
    Record one company memory event and append it to the store.

    kinds: "decision" | "completion" | "milestone" | "note"
    Auto-stamps ts (epoch float) + iso (UTC ISO date-time). Returns the stored
    record, or None if the input is unusable (missing kind AND summary) or the
    write fails. Never raises — malformed input degrades gracefully.
    """
    try:
        summary = (summary or "").strip() if isinstance(summary, str) else ""
        kind_raw = (kind or "").strip().lower() if isinstance(kind, str) else ""

        # Graceful refusal: a memory with neither a kind nor a summary is meaningless.
        if not summary:
            _logger.warning("company_memory.remember: missing summary — refused")
            return None

        norm_kind = kind_raw if kind_raw in _KINDS else "note"
        if kind_raw and kind_raw not in _KINDS:
            _logger.info("company_memory.remember: unknown kind %r → coerced to 'note'", kind_raw)

        now = time.time()
        norm_tags: list[str] = []
        if isinstance(tags, (list, tuple)):
            norm_tags = [str(t).strip() for t in tags if str(t).strip()]
        elif isinstance(tags, str) and tags.strip():
            norm_tags = [tags.strip()]

        record = {
            "schema":  _SCHEMA,
            "ts":      round(now, 3),
            "iso":     datetime.datetime.utcfromtimestamp(now).isoformat() + "Z",
            "kind":    norm_kind,
            "summary": summary[:500],
            "detail":  (detail or "").strip()[:4000] if isinstance(detail, str) else "",
            "wo":      str(wo).strip() if wo else None,
            "actor":   str(actor).strip() if actor else None,
            "tags":    norm_tags,
        }

        if not _append(store_path, record):
            return None
        return record

    except Exception as exc:
        _logger.error("company_memory.remember: unexpected error: %s", exc)
        return None


# ── recall() ──────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]


def _relevance(record: dict, query_tokens: list[str]) -> int:
    """Count query-token hits across summary/detail/tags/wo — simple substring match."""
    if not query_tokens:
        return 0
    haystack = " ".join([
        str(record.get("summary", "")),
        str(record.get("detail", "")),
        " ".join(record.get("tags", []) or []),
        str(record.get("wo") or ""),
    ]).lower()
    return sum(haystack.count(tok) for tok in query_tokens)


def recall(
    query=None,
    kind=None,
    wo=None,
    since_days=None,
    limit: int = 20,
    store_path: str = _STORE_PATH,
) -> list[dict]:
    """
    Retrieve company memory records, filtered and ranked.

    Filters (all optional, AND-combined):
      kind        — only records of this kind
      wo          — only records tagged with this work order
      since_days  — only records within the last N days (TIME-based recency, canon D-SESSIONS)
    Ranking:
      query given — rank by keyword match count (desc), then recency (desc)
      no query    — most recent first
    limit caps the number of returned records.
    """
    try:
        records = _read_all(store_path)

        # kind filter
        if kind:
            k = str(kind).strip().lower()
            records = [r for r in records if r.get("kind") == k]

        # wo filter
        if wo:
            w = str(wo).strip().lower()
            records = [r for r in records if str(r.get("wo") or "").strip().lower() == w]

        # recency filter (real time, in days — NOT sessions)
        if since_days is not None:
            try:
                cutoff = time.time() - float(since_days) * 86400.0
                records = [r for r in records if float(r.get("ts", 0)) >= cutoff]
            except (TypeError, ValueError):
                pass

        # keyword relevance ranking
        if query:
            q_tokens = _tokenize(str(query))
            scored = [(_relevance(r, q_tokens), r) for r in records]
            # keep only records with at least one hit when a query is provided
            scored = [(s, r) for (s, r) in scored if s > 0]

            # optional semantic boost — ONLY if embeddings are trivially available (no LLM, no hard dep)
            try:
                scored = _semantic_boost(str(query), scored)
            except Exception as exc:
                _logger.debug("company_memory: semantic boost skipped: %s", exc)

            scored.sort(key=lambda sr: (sr[0], float(sr[1].get("ts", 0))), reverse=True)
            ordered = [r for (_s, r) in scored]
        else:
            ordered = sorted(records, key=lambda r: float(r.get("ts", 0)), reverse=True)

        lim = limit if isinstance(limit, int) and limit > 0 else 20
        return ordered[:lim]

    except Exception as exc:
        _logger.error("company_memory.recall: unexpected error: %s", exc)
        return []


def _semantic_boost(query: str, scored: list[tuple[int, dict]]) -> list[tuple[int, dict]]:
    """
    Optional: nudge scores using memory/embedding_store if it is present AND an
    OPENAI_API_KEY is set. Purely additive — returns the input unchanged when
    embeddings are unavailable. Never triggers an LLM or a hard dependency.
    """
    if not scored or not os.environ.get("OPENAI_API_KEY"):
        return scored
    try:
        from memory import embedding_store  # type: ignore
    except Exception:
        return scored

    candidates = [str(r.get("summary", "")) for (_s, r) in scored]
    ranked = embedding_store.search(query, candidates, top_k=len(candidates))
    if not ranked:
        return scored

    # map summary → similarity, fold a small integer bump into the keyword score
    sim = {text: score for (text, score) in ranked}
    boosted: list[tuple[int, dict]] = []
    for (s, r) in scored:
        bump = int(round(sim.get(str(r.get("summary", "")), 0.0) * 3))
        boosted.append((s + bump, r))
    return boosted


# ── timeline() ────────────────────────────────────────────────────────────────

def timeline(days: int = 30, store_path: str = _STORE_PATH) -> list[dict]:
    """
    Chronological digest of recent company events — oldest → newest within the
    window. Time-based (days). Each entry is a compact view of one record.
    """
    try:
        recent = recall(since_days=days, limit=10_000, store_path=store_path)
        recent.sort(key=lambda r: float(r.get("ts", 0)))  # chronological
        return [
            {
                "iso":     r.get("iso"),
                "kind":    r.get("kind"),
                "summary": r.get("summary"),
                "wo":      r.get("wo"),
                "actor":   r.get("actor"),
            }
            for r in recent
        ]
    except Exception as exc:
        _logger.error("company_memory.timeline: unexpected error: %s", exc)
        return []


# ── CLI one-shot ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    tl = timeline(days=90)
    print(f"company_memory store → {_STORE_PATH}")
    print(f"  {len(tl)} events in the last 90 days")
    for ev in tl[-10:]:
        print(f"  {ev['iso']}  [{ev['kind']}]  {ev['summary']}"
              + (f"  ({ev['wo']})" if ev.get("wo") else ""))
