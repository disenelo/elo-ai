"""
memory/vault_layer.py — Tiered memory vault writer and lookup.

Three tiers written to obsidian_vault/09 Memory/:

    SPOT_CODES.md           — master scannable index (one row per record)
    summary/<code>.md       — summary note: one sentence + link to deep
    deep/<code>-deep.md     — full compressed memory block

All summary and deep notes carry YAML frontmatter with type: memory-summary /
memory-deep so obsidian_loader.py picks them up automatically.

Public API:
    write_memory(...)          — write all three tiers, return spot code
    compress_session(...)      — compress a session string into a tiered record
    lookup(query)              — search summaries, return matching records
    load_deep(spot_code)       — return full deep note text for a spot code
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime

from memory.vault_codec import (
    encode,
    decode,
    spot_to_filename,
    compress_text,
    weight_label,
)
from memory import obsidian_loader

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VAULT      = os.environ.get("ELO_VAULT_PATH", os.path.join(_ROOT, "obsidian_vault"))
_MEM_DIR    = os.path.join(_VAULT, "09 Memory")
_SUM_DIR    = os.path.join(_MEM_DIR, "summary")
_DEEP_DIR   = os.path.join(_MEM_DIR, "deep")
_SPOT_FILE  = os.path.join(_MEM_DIR, "SPOT_CODES.md")

# Tracks the overall significance score of the most recent vault write this session.
# Memory Faculty in spine.py reads this to decide whether to refresh the memory pack.
_last_write_significance: float | None = None


def last_write_significance() -> float | None:
    """
    Return and clear the significance of the most recent vault write.
    Returns None if no write has occurred since the last call.
    One-shot: clears on read so _memory_faculty() only refreshes once per write.
    """
    global _last_write_significance
    sig = _last_write_significance
    _last_write_significance = None
    return sig


def _ensure_dirs() -> None:
    for d in (_MEM_DIR, _SUM_DIR, _DEEP_DIR):
        os.makedirs(d, exist_ok=True)


# ── Write — all three tiers ───────────────────────────────────────────────────

_VALID_EPISTEMIC_CLASSES = frozenset({
    "verified", "inferred", "generated", "canonical",
    "dream_simulation", "inference", "hypothesis", "conversation",
})

# WO-PROVENANCE-001: source_type values — where did this vault entry originate?
_VALID_SOURCE_TYPES = frozenset({
    "CONVERSATION",      # direct user-eLo exchange
    "TOOL_RESULT",       # tool execution result (Spotify, web search, etc.)
    "WORLD_INTERACTION", # Unity game event or world-state change
    "PERCEPTION",        # blender_state / environment observation
    "INTERNAL",          # eLo's own internal processing (dream, ambient thought)
    "WKG",               # WKG retrieval result
    "UNKNOWN",           # provenance not specified (fallback)
})


def write_memory(
    *,
    project: str,
    memory_type: str,
    summary: str,
    deep_text: str,
    weight: int = 5,
    tags: list[str] | None = None,
    date: datetime | None = None,
    epistemic_class: str,
    source_ref: str = "",
    experience_id: str = "",
    source_type: str = "CONVERSATION",
    active_topic: str = "",
    referents: dict | None = None,
    author: str = "elo",
    thread_history: list | None = None,
) -> str:
    """
    Write a complete tiered memory record.

    Args:
        project         — domain: "elo-os" | "elo-game" | "elo-robot" | "elo-book"
                                   | "disenelo" | "david" | "general"
        memory_type     — "build" | "fix" | "decision" | "learn" | "connect"
                                   | "design" | "conversation"
        summary         — one-sentence description (max 200 chars after compress)
        deep_text       — full memory content (compressed to 2000 chars)
        weight          — 0-9 importance (9=core identity, 7+=important, 4-6=useful)
        tags            — Obsidian tag list e.g. ["architecture", "routing"]
        date            — defaults to datetime.now()
        epistemic_class — REQUIRED. EpistemicClass value (WO-VAULT-EPISTEMIC-CLASS-ENFORCE-001):
                          "verified" | "inferred" | "generated" | "canonical" |
                          "dream_simulation" | "inference" | "hypothesis" | "conversation".
                          "verified" requires a non-empty source_ref — raises ValueError otherwise.
        source_ref      — for "verified" claims: file path, turn_id, or session id that
                          proves the fact. Required when epistemic_class="verified".
        source_type     — WO-PROVENANCE-001: origin of this vault entry. One of
                          "CONVERSATION" | "TOOL_RESULT" | "WORLD_INTERACTION" |
                          "PERCEPTION" | "INTERNAL" | "WKG" | "UNKNOWN".
                          Defaults to "CONVERSATION". Unknown values are stored as-is.

    Returns:
        Spot code string e.g. "EO·BL·2607·9"
    """
    if epistemic_class == "verified" and not source_ref:
        raise ValueError(
            "write_memory: epistemic_class='verified' requires a non-empty source_ref "
            "(file path, turn_id, or session id). Pass source_ref=... or use a less "
            "certain class like 'inference' or 'conversation'."
        )
    _ensure_dirs()
    date = date or datetime.now()
    tags = tags or []

    coded  = encode(project=project, memory_type=memory_type, date=date, weight=weight)
    # WO-VAULT-UNIQUE: append a 5-char hex suffix derived from nanosecond clock so
    # every write gets a unique spot code and its own file.  Without this, all writes
    # sharing the same (project, type, month, weight) resolve to the same filename and
    # overwrite each other — confirmed bug: 6743 SPOT_CODES rows → only 29 files.
    _unique = f"{time.time_ns() % 0x100000:05x}"
    spot   = f"{coded['spot']}·{_unique}"
    bits   = coded["bits"]
    fname  = spot_to_filename(spot)

    summary_short   = compress_text(summary,   max_chars=200)
    deep_compressed = compress_text(deep_text, max_chars=2000)

    _append_spot_index(spot, bits, summary_short, date, experience_id=experience_id)
    _write_summary_note(fname, spot, bits, summary_short, date, tags, weight, coded,
                        epistemic_class=epistemic_class, source_ref=source_ref,
                        experience_id=experience_id, source_type=source_type,
                        active_topic=active_topic, referents=referents,
                        author=author, thread_history=thread_history)
    _write_deep_note(fname, spot, bits, deep_compressed, date, tags, weight,
                     epistemic_class=epistemic_class, source_ref=source_ref,
                     experience_id=experience_id, source_type=source_type,
                     active_topic=active_topic, referents=referents,
                     author=author, thread_history=thread_history)

    # Invalidate cache so next obsidian_loader.load() picks up the new notes
    obsidian_loader.invalidate_cache()

    # Signal memory faculty: a write occurred; store normalised significance (weight/9)
    global _last_write_significance
    _last_write_significance = round(weight / 9.0, 3)

    return spot


def _append_spot_index(spot: str, bits: str, summary: str, date: datetime,
                        experience_id: str = "") -> None:
    date_str = date.strftime("%Y-%m-%d")
    xid_col = f" {experience_id}" if experience_id else ""
    line = f"| `{spot}` | `{bits}` | {summary} | {date_str} |{xid_col}\n"

    if not os.path.exists(_SPOT_FILE):
        header = (
            "---\ntype: memory-index\ndomain: memory\n---\n\n"
            "# eLo Memory — Spot Code Index\n\n"
            "| Spot | Bits | Summary | Date | Experience ID |\n"
            "|------|------|---------|------|---------------|\n"
        )
        with open(_SPOT_FILE, "w", encoding="utf-8") as f:
            f.write(header)

    with open(_SPOT_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def _write_summary_note(
    fname: str, spot: str, bits: str, summary: str,
    date: datetime, tags: list, weight: int, coded: dict,
    epistemic_class: str = "inference",
    source_ref: str = "",
    experience_id: str = "",
    source_type: str = "CONVERSATION",
    active_topic: str = "",
    referents: dict | None = None,
    author: str = "elo",
    thread_history: list | None = None,
) -> None:
    import json as _json
    tag_str  = ", ".join(f'"{t}"' for t in tags) if tags else ""
    date_str = date.strftime("%Y-%m-%d")
    xid_line   = f"experience_id: {experience_id}\n" if experience_id else ""
    src_line   = f"source_ref: {source_ref}\n" if source_ref else ""
    topic_line = f"active_topic: {active_topic}\n" if active_topic else ""
    auth_line  = f"author: {author}\n" if author else ""
    ref_line   = (f"referents: {_json.dumps(referents)}\n"
                  if referents else "")
    thr_line   = (f"thread_history: {_json.dumps(thread_history)}\n"
                  if thread_history else "")
    content  = (
        f"---\n"
        f"type: memory-summary\n"
        f"domain: memory\n"
        f"spot: {spot}\n"
        f"bits: {bits}\n"
        f"project: {coded['p_code']}\n"
        f"memory-type: {coded['t_code']}\n"
        f"date: {date_str}\n"
        f"weight: {weight}\n"
        f"epistemic_class: {epistemic_class}\n"
        f"source_type: {source_type}\n"
        f"{src_line}"
        f"{xid_line}"
        f"{topic_line}"
        f"{ref_line}"
        f"{thr_line}"
        f"{auth_line}"
        f"tags: [{tag_str}]\n"
        f"deep: [[deep/{fname}-deep]]\n"
        f"---\n\n"
        f"> {summary}\n\n"
        f"**Code:** `{spot}`  \n"
        f"**Bits:** `{bits}`  \n"
        f"**Weight:** {weight}/9 ({weight_label(weight)})  \n"
        f"**Date:** {date_str}\n\n"
        f"→ [[deep/{fname}-deep|Load full context]]\n"
    )
    path = os.path.join(_SUM_DIR, f"{fname}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_deep_note(
    fname: str, spot: str, bits: str, deep_text: str,
    date: datetime, tags: list, weight: int,
    epistemic_class: str = "inference",
    source_ref: str = "",
    experience_id: str = "",
    source_type: str = "CONVERSATION",
    active_topic: str = "",
    referents: dict | None = None,
    author: str = "elo",
    thread_history: list | None = None,
) -> None:
    import json as _json
    tag_str  = ", ".join(f'"{t}"' for t in tags) if tags else ""
    date_str = date.strftime("%Y-%m-%d")
    xid_line   = f"experience_id: {experience_id}\n" if experience_id else ""
    src_line   = f"source_ref: {source_ref}\n" if source_ref else ""
    topic_line = f"active_topic: {active_topic}\n" if active_topic else ""
    auth_line  = f"author: {author}\n" if author else ""
    ref_line   = (f"referents: {_json.dumps(referents)}\n"
                  if referents else "")
    thr_line   = (f"thread_history: {_json.dumps(thread_history)}\n"
                  if thread_history else "")
    content  = (
        f"---\n"
        f"type: memory-deep\n"
        f"domain: memory\n"
        f"spot: {spot}\n"
        f"bits: {bits}\n"
        f"date: {date_str}\n"
        f"weight: {weight}\n"
        f"epistemic_class: {epistemic_class}\n"
        f"source_type: {source_type}\n"
        f"{src_line}"
        f"{xid_line}"
        f"{topic_line}"
        f"{ref_line}"
        f"{thr_line}"
        f"{auth_line}"
        f"tags: [{tag_str}]\n"
        f"summary: [[summary/{fname}]]\n"
        f"---\n\n"
        f"# {spot}\n\n"
        f"{deep_text}\n"
    )
    path = os.path.join(_DEEP_DIR, f"{fname}-deep.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ── Session compression ───────────────────────────────────────────────────────

def compress_session(
    session_summary: str,
    *,
    project: str = "general",
    weight: int = 5,
    tags: list[str] | None = None,
) -> str:
    """
    DEPRECATED — route through MemoryFaculty.submit() (Vol VIII §4 Invariant 7).
    Compress a session string into a tiered memory record.

    Call from offline_engine.integrate_session() at session end.
    Extracts the first sentence as summary; full text goes to deep tier.

    Returns the spot code of the created record.
    """
    first = re.split(r"(?<=[.!?])\s", session_summary.strip(), maxsplit=1)[0]
    return write_memory(
        project=project,
        memory_type="conversation",
        summary=first,
        deep_text=session_summary,
        weight=weight,
        tags=(tags or []) + ["session"],
        epistemic_class="conversation",
    )


# ── Lookup ────────────────────────────────────────────────────────────────────

_PROPOSED_TO_TCODE: dict[str, str] = {
    # proposed_type names (as used by MemoryCandidate)
    "episodic":   "CV",
    "semantic":   "LN",
    "procedural": "BL",
    "emotional":  "CN",
    # memory_type names (as stored by vault_layer.write_memory)
    "conversation": "CV",
    "learn":        "LN",
    "build":        "BL",
    "connect":      "CN",
    "fix":          "FX",
    "decision":     "DC",
    "design":       "DS",
}


def lookup(
    query: str,
    max_results: int = 5,
    type_filter: str | None = None,
    epistemic_filter: list[str] | None = None,
) -> list[dict]:
    """
    Search memory for records matching the query.

    type_filter — optional proposed_type or memory_type name to restrict results.
        Accepts: episodic | semantic | procedural | emotional
                 conversation | learn | build | connect | fix | decision | design
        When set, only records whose spot t_code matches are returned.

    epistemic_filter — WO-DREAM-EPISTEMIC-TAG-001. When set, only records
        whose epistemic_class is in the list are returned, so factual
        recall can exclude dream-derived material. Matching is
        case-insensitive: the vault writes lower case ("conversation",
        "verified") while WKG and dream_review use upper ("VERIFIED",
        "HYPOTHESIS"), and a filter that silently matched nothing because
        of case would be worse than no filter.

        A record with NO recorded class is excluded when a filter is set —
        18 of 682 deep records predate the field. Unknown provenance is
        not a pass; the caller asked for specific classes.

    Searches two sources:
        1. Summary .md files (structured, weighted)
        2. SPOT_CODES.md index rows (full conversation log, unweighted)

    Args:
        query       — free text or partial spot code (e.g. "routing", "EO·FX")
        max_results — cap on results returned

    Returns:
        List of dicts ordered by weight desc:
        {spot, bits, summary, date, weight, deep_link}
    """
    q       = query.lower().strip()
    # Split into individual search terms — any term match counts for broad recall
    _terms  = [t for t in re.split(r'\W+', q) if len(t) >= 3]
    results = []
    seen_summaries: set[str] = set()

    def _matches(text: str) -> bool:
        """True if any search term (or the full phrase) appears in text."""
        t = text.lower()
        if q in t:
            return True
        return any(term in t for term in _terms)

    # ── 1. Summary .md files (structured records with weight) ────────────────
    if os.path.exists(_SUM_DIR):
        for fname in os.listdir(_SUM_DIR):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(_SUM_DIR, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    raw = f.read()
            except Exception:
                continue

            if not _matches(fname) and not _matches(raw):
                continue

            meta = _parse_fm(raw)
            summary_text = ""
            for line in raw.splitlines():
                if line.startswith("> "):
                    summary_text = line[2:].strip()
                    break

            base = fname[:-3]
            seen_summaries.add(base)
            _w = int(meta.get("weight", 5))
            _spot_id = meta.get("spot", base)
            results.append({
                "spot":          _spot_id,
                "bits":          meta.get("bits", ""),
                "summary":       summary_text,
                "date":          meta.get("date", ""),
                "weight":        _w,
                "deep_link":     f"09 Memory/deep/{base}-deep",
                # WO-053: confidence+source+timestamp (LiveWorldState pattern)
                "memory":        summary_text,
                "confidence":    round(_w / 9.0, 3),
                "timestamp":     meta.get("date", ""),
                "source":        "vault_summary",
                # WO-109 Row 8: provenance set — experience_id, event, outcome
                "experience_id": _spot_id,
                "event":         summary_text,
                "outcome":       meta.get("outcome", None),
            })

    # ── 2. SPOT_CODES.md index rows (flat conversation log — high recall) ────
    # Each row: | `spot` | `bits` | summary text | date |
    # Weight = 3 (below structured records) unless the text is highly relevant.
    _spot_re = re.compile(
        r'\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|'
    )
    if os.path.exists(_SPOT_FILE):
        try:
            with open(_SPOT_FILE, encoding="utf-8") as f:
                for line in f:
                    if not _matches(line):
                        continue
                    m = _spot_re.search(line)
                    if not m:
                        continue
                    spot, bits, summary, date = m.group(1), m.group(2), m.group(3).strip(), m.group(4)
                    # Skip if already covered by a summary file
                    base = spot.replace("·", "-")
                    if base in seen_summaries:
                        continue
                    results.append({
                        "spot":          spot,
                        "bits":          bits,
                        "summary":       summary[:200],
                        "date":          date,
                        "weight":        3,
                        "deep_link":     f"09 Memory/deep/{base}-deep",
                        # WO-053: confidence+source+timestamp
                        "memory":        summary[:200],
                        "confidence":    0.333,
                        "timestamp":     date,
                        "source":        "spot_index",
                        # WO-109 Row 8: provenance set
                        "experience_id": spot,
                        "event":         summary[:200],
                        "outcome":       None,
                    })
        except Exception:
            pass

    results.sort(key=lambda x: x["weight"], reverse=True)

    # WO-MEMORY-QUERY-TYPE-001: filter by type if requested
    if type_filter:
        _want_tcode = _PROPOSED_TO_TCODE.get(type_filter.lower())
        if _want_tcode:
            results = [
                r for r in results
                if len(r.get("spot", "").split("·")) > 1
                and r["spot"].split("·")[1] == _want_tcode
            ]

    # WO-DREAM-EPISTEMIC-TAG-001: exclude dream-derived material from
    # factual recall. The class is written to the DEEP record's
    # frontmatter (664 of 682 carry it) and lookup never read it back, so
    # a dream entry and a conversation entry were indistinguishable here.
    # Resolved per candidate rather than up front — the read only happens
    # for rows that already matched the query.
    if epistemic_filter:
        _want = {str(c).strip().lower() for c in epistemic_filter}
        results = [r for r in results
                   if _epistemic_class_of(r).lower() in _want]

    _truncated = results[:max_results]
    # P0-3 fix: reinforce() removed from lookup() — library must not do durable writes.
    # Vol VIII §4.70 / §4.03: "retrieval runs in the response path … reading only; durable
    # writes never happen in the hot loop." Reinforce fires in the integration window
    # (server.py, post-response daemon thread) keyed on vault hits that were actually used.
    return _truncated


def _epistemic_class_of(record: dict) -> str:
    """
    The epistemic class on a lookup row, read from its deep record.

    Returns "" when the record has none — 18 of 682 deep files predate the
    field. Callers treat "" as excluded rather than as a pass: unknown
    provenance is not evidence of good provenance.
    """
    cached = record.get("epistemic_class")
    if cached:
        return str(cached)

    # Built from _DEEP_DIR, like every other path in this module. The first
    # version joined _VAULT with the deep_link, which LOOKS equivalent — but
    # _MEM_DIR/_DEEP_DIR are derived from _VAULT at import, so anything that
    # repoints the vault leaves the two reading different directories. The
    # resolver then found nothing, returned "", and every row failed the
    # filter: a filter that quietly excludes everything.
    spot = str(record.get("spot", "") or "")
    if not spot:
        return ""
    try:
        path = os.path.join(_DEEP_DIR, f"{spot.replace(chr(183), '-')}-deep.md")
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8", errors="replace") as _f:
            klass = str(_parse_fm(_f.read()).get("epistemic_class", "") or "")
    except Exception:
        return ""
    record["epistemic_class"] = klass        # surfaced for the caller too
    return klass


def recall_context(query: str, max_results: int = 5) -> dict:
    """
    WO-053: Structured recall with LiveWorldState-style confidence+source+status.

    Returns one of:
        {"status": "live",   "results": [...], "count": N, "source": "vault"}
        {"status": "absent", "results": [],    "count": 0, "source": "absent",
         "message": "memory offline — vault unreachable"}

    Each result in 'results' carries:
        {memory, confidence (0.0–1.0), timestamp, source ("vault_summary"|"spot_index")}

    eLo can surface the confidence directly: "I recorded this on [date], high confidence."
    Never a vague 'I think…' — the caller always knows how certain the recall is.
    """
    if not os.path.exists(_MEM_DIR):
        return {
            "status":  "absent",
            "results": [],
            "count":   0,
            "source":  "absent",
            "message": "memory offline — vault directory unreachable",
        }
    try:
        results = lookup(query, max_results=max_results)
        return {
            "status":  "live" if results else "absent",
            "results": results,
            "count":   len(results),
            "source":  "vault",
        }
    except Exception as e:
        return {
            "status":  "absent",
            "results": [],
            "count":   0,
            "source":  "absent",
            "message": f"memory offline — {e}",
        }


def load_deep(spot_code: str) -> str | None:
    """
    Load the full deep memory text for a spot code.

    Args:
        spot_code — e.g. "EO·BL·2607·9"

    Returns:
        Body text (frontmatter stripped), or None if not found.
    """
    fname = spot_to_filename(spot_code)
    path  = os.path.join(_DEEP_DIR, f"{fname}-deep.md")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                return content[end + 4:].strip()
        return content.strip()
    except Exception:
        return None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_fm(content: str) -> dict:
    meta: dict = {}
    if not content.startswith("---"):
        return meta
    end = content.find("\n---", 3)
    if end == -1:
        return meta
    for line in content[3:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip("\"'")
    return meta


# ── CLI (test / demo) ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    spot = write_memory(
        project="elo-os",
        memory_type="build",
        summary="Built tiered memory vault — spot code → summary → deep — in obsidian_vault/09 Memory/.",
        deep_text=(
            "Session 2026-07-06. Built vault_codec.py (encode/decode spot codes + bit strings) "
            "and vault_layer.py (three-tier writer: SPOT_CODES index + summary note + deep record). "
            "SPOT_CODES.md in 09 Memory/ is the scannable lookup. Each summary note links to its "
            "deep record via [[wikilink]]. obsidian_loader.py picks up memory-summary and "
            "memory-deep domain notes. compress_session() wired for offline_engine integration."
        ),
        weight=8,
        tags=["architecture", "memory", "vault"],
        epistemic_class="verified",
        source_ref="build_session_2026-07-06",
    )
    print(f"Written: {spot}")
    print()

    hits = lookup("vault")
    for h in hits:
        print(f"  {h['spot']}  {h['summary']}")
        print(f"  → {h['deep_link']}")
