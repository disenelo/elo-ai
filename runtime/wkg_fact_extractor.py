"""
runtime/wkg_fact_extractor.py — ROOT-1 fix (WKG-AUTO-POPULATE-001)

Extracts specific, content-bearing facts from David's raw utterance and writes
them to the WKG as SOURCE_ATTRIBUTED claims.

Problem with the existing approach (server.py:6659):
  All live turn claims are "David ASSOCIATED_WITH projects/creative/world" —
  generic category labels with no specific content. They cannot answer the
  question "what did David say about X?" because the actual utterance is lost.

This module preserves the specific text so retrieval can score on it.

Design:
  - Pattern-based extraction on _original_raw (before any enrichment)
  - Each match creates a CONCEPT entity whose label + description carry the
    actual fact text (not just a category name)
  - Claim relationship: HAS_PROPERTY (David possesses this stated property/fact)
  - epistemic_class: SOURCE_ATTRIBUTED (David explicitly stated this)
  - Rate-limited: _MAX_FACTS_PER_TURN facts per turn, total cap via wkg_faculty

Called from server.py once per turn, after populate_wkg_from_turn().
Never raises — always fails silently so the main response path is unaffected.
"""

from __future__ import annotations
import re
import logging

_log = logging.getLogger("wkg_fact_extractor")

_MAX_FACTS_PER_TURN = 2   # write at most 2 specific facts per turn
_MIN_FACT_LEN       = 4   # object phrase must be at least 4 chars
_MAX_UTTERANCE_LEN  = 500 # skip very long utterances (likely code/paste)

# David's fixed entity ID in the WKG (same constant used by memory_faculty)
_DAVID_ENTITY_ID = "6de402af-8b5a-4238-950f-79bb1a00ab58"


# ── Patterns ────────────────────────────────────────────────────────────────────
# Each pattern is (regex, relationship_type, significance, fact_template)
# fact_template receives named groups from the match; label is the entity label.

_PATTERNS: list[tuple] = [
    # "my X is Y" — possessive assignment, high specificity
    (
        re.compile(
            r"\bmy\s+(?P<attr>[\w\s]{2,30}?)\s+is\s+(?P<val>[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "HAS_PROPERTY",
        0.72,
        "David's {attr} is {val}",
    ),
    # "I'm working on / building / shipping X"
    (
        re.compile(
            r"\bi'?m\s+(?:working\s+on|building|shipping|coding|designing|writing)\s+(?P<val>[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "ASSOCIATED_WITH",
        0.65,
        "David is working on {val}",
    ),
    # "I finished / completed / shipped X"
    (
        re.compile(
            r"\bi\s+(?:finished|completed|shipped|released|published)\s+(?P<val>[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "ASSOCIATED_WITH",
        0.67,
        "David completed {val}",
    ),
    # "the [deadline/release/version/project/goal] is Y"
    (
        re.compile(
            r"\bthe\s+(?P<attr>deadline|release|version|project|goal|plan|target|date|milestone)\s+is\s+(?P<val>[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "HAS_PROPERTY",
        0.70,
        "Project {attr} is {val}",
    ),
    # "eLo [has/is/does] X" — character property
    (
        re.compile(
            r"\beLo\s+(?:has|is|does|can|will|must)\s+(?P<val>[\w][\w\s,'-]{2,60}?)(?=[.!?,]|$)",
            re.I,
        ),
        "HAS_PROPERTY",
        0.68,
        "eLo {val}",
    ),
]

# Terms that indicate the match is a question or hypothetical, not a stated fact
_QUESTION_PREFIXES = re.compile(
    r"^\s*(?:what|how|why|when|where|who|does|do|can|could|should|would|is|are|was|were|will|if|maybe|perhaps|could you|can you)\b",
    re.I,
)


def _clean(text: str) -> str:
    """Strip trailing noise from a captured phrase."""
    # Remove trailing articles / prepositions / filler
    text = text.strip().rstrip(".,;:!?")
    text = re.sub(r"\s+", " ", text)
    return text


def extract_and_write(
    raw: str,
    experience_id: str = "",
    project: str = "general",
) -> list[str]:
    """
    Extract specific facts from David's utterance and write them to the WKG.

    Returns list of claim_ids written. Returns [] on any error.
    Always fails silently — never raises.
    """
    try:
        return _extract_and_write_inner(raw, experience_id, project)
    except Exception as exc:
        _log.debug("wkg_fact_extractor silent fail: %s", exc)
        return []


def _extract_and_write_inner(
    raw: str,
    experience_id: str,
    project: str,
) -> list[str]:
    text = (raw or "").strip()
    if not text or len(text) > _MAX_UTTERANCE_LEN:
        return []

    # Skip questions and hypotheticals — we only record explicitly stated facts
    if _QUESTION_PREFIXES.match(text):
        return []
    if text.endswith("?"):
        return []

    from runtime.wkg_faculty import search_entities, create_entity, record_claim
    from runtime.memory_origin import MemoryOrigin

    # Ensure David entity exists
    david_id = _ensure_david(search_entities, create_entity)
    if not david_id:
        return []

    written: list[str] = []

    for pattern, rel_type, sig, fact_template in _PATTERNS:
        if len(written) >= _MAX_FACTS_PER_TURN:
            break
        m = pattern.search(text)
        if not m:
            continue

        groups = m.groupdict()
        val = _clean(groups.get("val", ""))
        attr = _clean(groups.get("attr", ""))
        if len(val) < _MIN_FACT_LEN:
            continue

        # Build label and description for the fact entity
        try:
            label = fact_template.format(val=val, attr=attr)
        except KeyError:
            label = val
        label = label[:80]

        # Full utterance excerpt in description so graph_loader can score on it
        excerpt = text[:200]
        description = f'Stated: "{excerpt}"'

        # Look up or create the fact entity
        hits = search_entities(label[:40])
        if hits and hits[0].get("label", "").lower() == label.lower():
            obj_entity_id = hits[0]["entity_id"]
        else:
            ent = create_entity(
                entity_type="CONCEPT",
                label=label,
                description=description,
                source_ids=[experience_id] if experience_id else [],
            )
            obj_entity_id = ent["entity_id"]

        # Write the claim
        claim = record_claim(
            subject_entity_id=david_id,
            relationship_type=rel_type,
            object_entity_id=obj_entity_id,
            epistemic_class="SOURCE_ATTRIBUTED",
            source_id=f"fact_extractor:{project}",
            experience_id=experience_id or None,
            confidence=sig,
            memory_type="semantic",
            memory_origin=MemoryOrigin.REAL_EXPERIENCE.value,
        )
        written.append(claim.get("claim_id", ""))
        _log.info(
            "ROOT-1 fact written: %r → %s → %r (sig=%.2f)",
            "David Charles", rel_type, label[:50], sig,
        )

    return [c for c in written if c]


def _ensure_david(search_entities, create_entity) -> str:
    """Return David's WKG entity_id, creating it if absent."""
    hits = search_entities("David Charles")
    if hits:
        return hits[0]["entity_id"]
    try:
        ent = create_entity(
            "PERSON",
            "David Charles",
            aliases=["David"],
            description="Creator of eLo and DISENELO",
        )
        return ent["entity_id"]
    except Exception:
        return _DAVID_ENTITY_ID  # fallback to known ID
