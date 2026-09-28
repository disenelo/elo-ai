"""
self_improvement/correction_store.py — WO-027: reviewed correction-memory (ICL).

Stores (input, corrected_response, why, trace) pairs; retrieves semantically
similar ones on each turn; injects as few-shot examples into the system prompt.

Review tiers (David 2026-08-02 — corrections shape eLo's mind):
  TIER_AUTO  (green) — safe/mechanical fixes; can enter automatically after tests pass.
  TIER_DAVID (red)   — voice, personality, routing; requires David's explicit review.

WO-071: extends with shadow-log ingestion (auto-corrections from scrub deltas +
L3 overrides) and a bounded correction frame builder for per-turn injection.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Optional

import logging
_log = logging.getLogger(__name__)

# Board fix (2026-09-28): 204 ledger entries contain "you Charles" as the
# "correct" form of address after a scrub layer misgeneralized David's surname.
# Filter them on read so they never inject as few-shot examples.
# Guard also applied on write so new poisoned entries are rejected.
_CHARLES_ADDRESS_RE = re.compile(r"(?<!David )Charles\b")

# Location fix (2026-09-28): 73 ledger entries contain "Camberwell" as David's
# home origin — wrong fact. David was born in Fulham, raised in Brixton.
# Filter on read and reject on write.
_CAMBERWELL_LOCATION_RE = re.compile(r"\bCamberwell\b")

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

    if _CHARLES_ADDRESS_RE.search(corrected_response):
        _log.warning("store_correction: rejected — 'Charles' used as address form in corrected_response")
        return False  # reject poisoned address form before it reaches the ledger

    if _CAMBERWELL_LOCATION_RE.search(corrected_response):
        _log.warning("store_correction: rejected — 'Camberwell' is wrong location (born Fulham, raised Brixton)")
        return False  # reject wrong location fact before it reaches the ledger

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
                        cr = e.get("corrected_response", "")
                        if _CHARLES_ADDRESS_RE.search(cr):
                            continue  # poisoned — "Charles" used as address form
                        if _CAMBERWELL_LOCATION_RE.search(cr):
                            continue  # poisoned — wrong location (Camberwell)
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


# ── WO-071: Shadow-log ingestion + bounded correction frame ───────────────────

_SHADOW_LOG_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "self", "journals", "understudy_shadow.jsonl",
)

_last_ingest_ts: float = 0.0
_INGEST_INTERVAL = 60.0  # throttle: ingest at most once per 60s


def ingest_from_shadow_log(path: Optional[str] = None, limit: int = 50) -> int:
    """
    Read the WO-070 shadow log and store new auto-corrections into the ledger.

    Extracts two signal types:
      - Scrub deltas: rows where elo_raw_gen != elo_final (the verify layer caught a slip)
      - L3 overrides: l3_patch rows with l3_rating (paired with their original turn by trace_id)

    Throttled to once per 60s — safe to call every turn.
    Returns the count of new corrections stored this call.
    """
    global _last_ingest_ts
    now = time.time()
    if now - _last_ingest_ts < _INGEST_INTERVAL:
        return 0
    _last_ingest_ts = now

    shadow_path = path or _SHADOW_LOG_DEFAULT
    if not os.path.exists(shadow_path):
        return 0

    # Load existing ledger IDs to avoid duplicates
    existing = _load_ledger()
    seen_trace_ids: set = {e.get("trace", {}).get("trace_id", "") for e in existing}
    seen_trace_ids.discard("")

    try:
        rows: list[dict] = []
        with open(shadow_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except Exception as e:
        _log.debug("ingest_from_shadow_log: could not read shadow log: %s", e)
        return 0

    # Build trace_id → original-turn index for L3 correlation
    turn_by_trace: dict[str, dict] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if r.get("_type") != "l3_patch" and r.get("trace_id"):
            turn_by_trace[r["trace_id"]] = r

    stored = 0
    processed_ids: set = set()

    for r in rows[-limit:]:  # only recent rows
        if not isinstance(r, dict):
            continue

        # A. Scrub delta — raw_gen differs from final
        if (r.get("_type") != "l3_patch"
                and r.get("raw_input")
                and r.get("elo_raw_gen") and r.get("elo_final")
                and r["elo_raw_gen"] != r["elo_final"]):
            tid = r.get("trace_id", "")
            if tid and tid in seen_trace_ids:
                continue
            if tid in processed_ids:
                continue
            ok = store_correction(
                input_text=r["raw_input"],
                corrected_response=r["elo_final"],
                why="scrub: raw generation differed from final output (verify layer caught a slip)",
                trace={"trace_id": tid, "backend": r.get("backend_used", "")},
                reviewed=True,
                tier=TIER_AUTO,
            )
            if ok:
                stored += 1
                if tid:
                    processed_ids.add(tid)

        # B. L3 override — David approved/rejected a turn
        elif r.get("_type") == "l3_patch" and r.get("trace_id"):
            tid = r["trace_id"]
            original = turn_by_trace.get(tid)
            if not original or tid in seen_trace_ids or tid in processed_ids:
                continue
            rating = r.get("l3_rating", "")
            if rating not in ("approved", "rejected", "override"):
                continue
            ok = store_correction(
                input_text=original.get("raw_input", ""),
                corrected_response=original.get("elo_final", ""),
                why=f"L3 {rating} by David (trace {tid})",
                trace={"trace_id": tid, "l3_rating": rating},
                reviewed=True,
                tier=TIER_AUTO if rating == "approved" else TIER_DAVID,
            )
            if ok:
                stored += 1
                processed_ids.add(tid)

    return stored


def build_correction_frame(input_text: str, top_k: int = 3, max_chars: int = 600) -> str:
    """
    Retrieve relevant past corrections and build a bounded frame for the system prompt.

    Returns "" if no relevant corrections exist (no filler — ADR-Exec-005).
    The frame is capped at max_chars to avoid crowding the prompt.
    This is a HINT only — never overrides the Executive or honesty guards.
    """
    try:
        ingest_from_shadow_log()  # throttled — usually a no-op
    except Exception:
        pass

    try:
        corrections = search_corrections(input_text, top_k=top_k)
    except Exception:
        return ""

    if not corrections:
        return ""

    lines = [
        "[RECENT CORRECTIONS — past slips and fixes; treat as hints only, not authority]"
    ]
    for c in corrections:
        entry_lines = [
            f'  slip input:  "{c["input"][:80]}"',
            f'  fixed reply: "{c["corrected_response"][:100]}"',
        ]
        if c.get("why"):
            entry_lines.append(f'  why: {c["why"][:80]}')
        if c.get("trace", {}).get("l3_rating"):
            entry_lines.append(f'  l3: {c["trace"]["l3_rating"]}')
        lines.extend(entry_lines)
        lines.append("  ---")

    frame = "\n".join(lines)
    if len(frame) > max_chars:
        frame = frame[:max_chars] + "\n  [... capped]"
    return frame
