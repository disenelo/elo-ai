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
    old_belief:          str = "",
) -> bool:
    """
    Store a reviewed correction in the ledger.

    old_belief: what eLo previously stated before the correction.
    Storing this preserves full provenance — eLo can acknowledge "I previously
    stated X, corrected to Y" without pretending he always knew the right answer.

    Red-tier corrections (voice/personality/routing) must have reviewed=True.
    Returns True on success, False if blocked by the review gate.
    """
    if tier is None:
        tier = _classify_tier(why)

    if tier == TIER_DAVID and not reviewed:
        return False  # blocked — David must review before this enters memory

    # A correction that cannot say what was corrected is a gap, and tens of
    # thousands of entries accumulated carrying none while nothing said so.
    # Silence is how it reached that number. Stored either way — the entry is
    # still evidence — but it will not reach the history block, because a
    # correction with no "before" lets eLo pretend he always knew.
    if not (old_belief or "").strip():
        _log.warning(
            "store_correction: no old_belief — this entry records a correction "
            "with no record of what was corrected, and will not appear in the "
            "correction history. why=%r", (why or "")[:80],
        )

    if _CHARLES_ADDRESS_RE.search(corrected_response):
        _log.warning("store_correction: rejected — 'Charles' used as address form in corrected_response")
        return False  # reject poisoned address form before it reaches the ledger

    if _CAMBERWELL_LOCATION_RE.search(corrected_response):
        _log.warning("store_correction: rejected — 'Camberwell' is wrong location (born Fulham, raised Brixton)")
        return False  # reject wrong location fact before it reaches the ledger

    entry: dict = {
        "id":                 f"CX-{int(time.time() * 1000) % 10_000_000:07d}",
        "input":              input_text,
        "corrected_response": corrected_response,
        "why":                why,
        "trace":              trace or {},
        "tier":               tier,
        "reviewed":           reviewed,
        "ts":                 time.time(),
    }
    if old_belief:
        entry["old_belief"] = old_belief  # preserved when non-empty; absent in legacy entries
    try:
        os.makedirs(os.path.dirname(_LEDGER_PATH), exist_ok=True)
        with open(_LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        # WO-AUTOBIOGRAPHY-CONV-001: a stored correction is a real lived experience.
        # Write a self_correction autobiography entry so eLo has a cognitive history
        # of what it has been corrected on, not just physical body events.
        try:
            from self.emergent_cognition import append_autobiography as _ab_corr
            _ab_corr(
                f"correction stored: {why[:80]}",
                kind="cognitive",
                verified=True,
                source="self_correction",
                episode_ref=entry["id"],
            )
        except Exception:
            pass
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
                # The prior belief, and it was being discarded. elo_raw_gen IS
                # what eLo said before the verify layer caught it; elo_final is
                # the correction. Both sit in this same record. Without it the
                # ledger holds a correction with no "before", which is the one
                # thing the correction history exists to preserve.
                old_belief=r["elo_raw_gen"],
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
        ]
        if c.get("old_belief"):
            entry_lines.append(f'  old belief:  "{c["old_belief"][:100]}"')
        entry_lines.append(f'  fixed reply: "{c["corrected_response"][:100]}"')
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


# ── Correction history provenance block ───────────────────────────────────────

_HISTORY_RECENT_N = 20  # scan at most this many recent ledger entries


def correction_history_prompt_block(max_entries: int = 20) -> str:
    """
    Build a prompt block from corrections_ledger.jsonl.

    WO-CORRECTIONS-SCHEMA-001: the previous filter required old_belief, which
    is only present when store_correction() was called with that optional arg.
    44,606 entries exist; zero were read back because the actual schema uses
    corrected_response + why + trace (not old_belief). Fixed: filter on
    corrected_response (present on all entries); old_belief shown when present.

    This answers IS ELO: — Self-Correcting Without Rewriting History?
      "can eLo avoid pretending he always knew the corrected answer?"
      "can eLo distinguish the old state from the corrected state?"
      "can eLo maintain provenance through multiple corrections?"

    THE CAUSAL CHAIN:
      store_correction(...) → corrections_ledger.jsonl
      → _load_ledger() → correction_history_prompt_block()
      → [CORRECTION HISTORY] block in system prompt
      → LLM can reference past corrections honestly.

    Never raises.
    """
    try:
        entries = _load_ledger()
        if not entries:
            return ""

        # Requires BOTH halves. WO-CORRECTIONS-SCHEMA-001 loosened this to
        # corrected_response alone, for a real reason — tens of thousands of
        # entries existed and none carried old_belief, so the block was always
        # empty. But the loosened filter renders "corrected to: X" with no
        # record of what eLo previously thought, which is correction with the
        # history removed: exactly what this block exists to prevent, and what
        # AT-4 and AT-12 of WO-ELO-CORRECTION-HISTORY-001 forbid.
        #
        # AT-12 is the causal test in David's own form — delete the old_belief
        # state and the influence must vanish. Under the loosened filter it did
        # not, so the block was uncaused by the thing it claimed to report.
        #
        # Neither filter was the fix. The DATA was: ingest_from_shadow_log was
        # discarding elo_raw_gen, the prior belief, at the one site where it
        # demonstrably exists. That is now captured, so this filter has real
        # entries to find instead of being loosened until it finds something.
        provenance = [e for e in entries
                      if e.get("corrected_response") and (e.get("old_belief") or "").strip()]
        if not provenance:
            return ""

        # Most recent first, up to max_entries
        recent = provenance[-_HISTORY_RECENT_N:][-max_entries:]
        recent = list(reversed(recent))

        lines = ["[CORRECTION HISTORY — what eLo has been corrected on, most recent first]"]
        lines.append(
            "  These are real corrections from experience. Do not pretend you always knew the right answer."
        )
        for c in recent:
            if c.get("input"):
                lines.append(f'  topic:        "{c["input"][:80]}"')
            if c.get("old_belief"):
                lines.append(f'  I stated:     "{c["old_belief"][:100]}"')
            lines.append(f'  corrected to: "{c["corrected_response"][:100]}"')
            if c.get("why"):
                lines.append(f'  why:          {c["why"][:80]}')
            lines.append("  ---")

        return "\n".join(lines)

    except Exception as exc:
        _log.warning("correction_history_prompt_block failed (non-fatal): %s", exc)
        return ""
