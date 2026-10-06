"""
tools/wkg_backfill.py — WKG historical backfill from interactions.json

Processes memory/interactions.json (3311 entries, June–Oct 2026) and writes
SOURCE_ATTRIBUTED WKG claims from David's explicitly stated facts.

Uses the same pattern set as runtime/wkg_fact_extractor, but:
- One fact per entry (not two) to avoid flooding
- Only possessive and working-on patterns (highest precision)
- Deduplicates: existing entity with same label is skipped
- Marks entities with provenance "interactions_backfill_YYYY-MM-DD"
- Reports counts at end

Run once:
  cd ~/elo-ai && python3 tools/wkg_backfill.py

This script is idempotent — safe to re-run (dedup gate prevents duplicates).
"""

from __future__ import annotations
import json
import logging
import os
import re
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_log = logging.getLogger("wkg_backfill")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

_INTERACTIONS_PATH = os.path.join(_ROOT, "memory", "interactions.json")
_BATCH_SIZE = 50   # log progress every N entries

# Patterns — same as wkg_fact_extractor, subset with highest precision
_PATTERNS = [
    (
        re.compile(
            r"\bmy\s+(?P<attr>[\w\s]{2,30}?)\s+is\s+(?P<val>[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "HAS_PROPERTY",
        0.72,
        "David's {attr} is {val}",
    ),
    (
        re.compile(
            # Val must start with a word that is NOT a conjunction/article
            r"\bi'?m\s+(?:working\s+on|building|shipping|coding|designing)\s+(?P<val>(?!(?:and|the|a|an|so|that|what|it|just)\b)[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "ASSOCIATED_WITH",
        0.65,
        "David is working on {val}",
    ),
    (
        re.compile(
            r"\bi\s+(?:finished|completed|shipped|released|published)\s+(?P<val>[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "ASSOCIATED_WITH",
        0.67,
        "David completed {val}",
    ),
]

_QUESTION_PREFIXES = re.compile(
    r"^\s*(?:what|how|why|when|where|who|does|do|can|could|should|would|is|are|was|were|will|if|maybe|perhaps|could you|can you)\b",
    re.I,
)
_MAX_UTT_LEN = 400
_MIN_FACT_LEN = 4

DAVID_ENTITY_ID = "6de402af-8b5a-4238-950f-79bb1a00ab58"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().rstrip(".,;:!?"))


def _extract_top_fact(text: str) -> tuple | None:
    """Return (rel_type, label, confidence) for the best fact match, or None."""
    text = (text or "").strip()
    if not text or len(text) > _MAX_UTT_LEN:
        return None
    # Skip enriched raw entries (WORLD_KNOWLEDGE injection leaked into interactions.json)
    if text.startswith("[WORLD_KNOWLEDGE") or text.startswith("[WEB_SEARCH"):
        return None
    if text.endswith("?") or _QUESTION_PREFIXES.match(text):
        return None
    for pattern, rel_type, conf, tmpl in _PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        groups = m.groupdict()
        val = _clean(groups.get("val", ""))
        attr = _clean(groups.get("attr", ""))
        if len(val) < _MIN_FACT_LEN:
            continue
        try:
            label = tmpl.format(val=val, attr=attr)[:80]
        except KeyError:
            label = val
        return rel_type, label, conf, text
    return None


def run():
    if not os.path.exists(_INTERACTIONS_PATH):
        _log.error("interactions.json not found at %s", _INTERACTIONS_PATH)
        sys.exit(1)

    with open(_INTERACTIONS_PATH) as f:
        interactions = json.load(f)
    _log.info("Loaded %d interactions from %s", len(interactions), _INTERACTIONS_PATH)

    from runtime.wkg_faculty import search_entities, create_entity, record_claim
    from runtime.memory_origin import MemoryOrigin

    # Ensure David entity exists
    david_hits = search_entities("David Charles")
    if david_hits:
        david_id = david_hits[0]["entity_id"]
    else:
        ent = create_entity("PERSON", "David Charles",
                            aliases=["David"],
                            description="Creator of eLo and DISENELO")
        david_id = ent["entity_id"]
    _log.info("David entity_id: %s", david_id)

    today = time.strftime("%Y-%m-%d")
    provenance = f"interactions_backfill_{today}"

    written = 0
    skipped_no_match = 0
    skipped_duplicate = 0
    errors = 0

    for i, entry in enumerate(interactions):
        user_text = (entry.get("user") or "").strip()
        if not user_text:
            skipped_no_match += 1
            continue

        result = _extract_top_fact(user_text)
        if not result:
            skipped_no_match += 1
            continue

        rel_type, label, conf, utterance = result

        try:
            # Dedup: check if entity with same label already exists
            hits = search_entities(label[:40])
            existing = [h for h in hits if h.get("label", "").lower() == label.lower()]
            if existing:
                skipped_duplicate += 1
                continue

            # Create entity with backfill provenance
            description = f'Stated in prior session. {provenance}. Excerpt: "{utterance[:180]}"'
            ent = create_entity(
                entity_type="CONCEPT",
                label=label,
                description=description,
                source_ids=[provenance],
            )
            obj_entity_id = ent["entity_id"]

            # Write claim
            record_claim(
                subject_entity_id=david_id,
                relationship_type=rel_type,
                object_entity_id=obj_entity_id,
                epistemic_class="SOURCE_ATTRIBUTED",
                source_id=provenance,
                confidence=conf,
                memory_type="semantic",
                memory_origin=MemoryOrigin.REAL_EXPERIENCE.value,
            )
            written += 1

            if written % _BATCH_SIZE == 0:
                _log.info(
                    "Progress: %d/%d interactions — %d written, %d no match, %d dup, %d errors",
                    i + 1, len(interactions), written, skipped_no_match, skipped_duplicate, errors,
                )

        except Exception as exc:
            errors += 1
            _log.debug("Entry %d error: %s", i, exc)

    _log.info(
        "Backfill complete: %d written, %d no_match, %d duplicate, %d errors",
        written, skipped_no_match, skipped_duplicate, errors,
    )
    _log.info("Run retrieve_wkg_context_items() to verify retrieval works.")


if __name__ == "__main__":
    run()
