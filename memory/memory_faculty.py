"""
memory/memory_faculty.py — MemoryFaculty: single logical writer (WO-CANON-VIII)

Routes all durable memory writes through one decision owner.
Decides {write | reinforce | drop} for every incoming MemoryCandidate.
Physical writer stays vault_layer.write_memory — sole bytes writer, unchanged.

Spec: Volume VIII Ch.4 §4.1.2
Decision Log: D-F (Memory Faculty sole LTM writer, RATIFIED)
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── MemoryCandidate ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MemoryCandidate:
    """
    Carries everything a faculty wants to persist.
    proposed_weight is a REQUEST — MemoryFaculty sets the final weight.
    proposed_type: episodic | semantic | procedural | emotional
    significance:  0.0–1.0 normalised score (from significance_engine or weight/9)
    verified:      True if the caller has fact-checked the content
    """
    source_faculty:  str   = ""          # "reflection" | "music" | "consolidation" | ...
    content:         str   = ""          # full memory body (deep_text)
    proposed_type:   str   = "episodic"  # episodic | semantic | procedural | emotional
    proposed_weight: int   = 5           # 0–9, REQUEST only — clamped to [1, 9]
    significance:    float = 0.0         # 0.0–1.0 normalised significance
    verified:        bool  = False       # fact-checked by caller?
    project:         str   = "general"   # vault domain label
    summary:         str   = ""          # one-sentence summary (≤200 chars after compress)
    tags:            tuple = field(default_factory=tuple)   # frozen tag list
    experience_id:   str   = ""          # WO-XDNA-001: per-turn identity minted by spine
    # WO-VAULT-EPISTEMIC-CLASS-ENFORCE-001: callers must declare epistemic class.
    # Default "inference" for callers that don't know — never silently "verified".
    epistemic_class: str   = "inference"  # verified|inferred|generated|canonical|inference|...
    source_ref:      str   = ""           # non-empty required when epistemic_class="verified"


# ── Constants ────────────────────────────────────────────────────────────────

_DROP_THRESHOLD = 0.15   # significance below this → drop (no write, no reinforce)

_TYPE_TO_MEMORY_TYPE: dict[str, str] = {
    "episodic":   "conversation",
    "semantic":   "learn",
    "procedural": "build",
    "emotional":  "connect",
}


# ── MemoryFaculty ────────────────────────────────────────────────────────────

class MemoryFaculty:
    """
    Single logical writer for all durable memory.

    submit() receives a MemoryCandidate and decides:
      DROP     — significance below threshold or empty content
      REINFORCE — existing record with matching summary found → strengthen it
      WRITE     — new vault record via vault_layer.write_memory (sole bytes call)

    Errors in reinforce or lookup never block a write — the fallback is always WRITE.
    """

    def submit(self, candidate: MemoryCandidate) -> dict:
        """
        Decide {write | reinforce | drop} and act.

        Returns:
            {
              "action": "write" | "reinforce" | "drop",
              "spot":   str | None,   # spot code if written or reinforced
              "reason": str,
            }
        """
        # ── DROP gate ─────────────────────────────────────────────────────────
        if not candidate.content.strip():
            return {"action": "drop", "spot": None, "reason": "empty content"}

        if candidate.significance < _DROP_THRESHOLD:
            return {
                "action": "drop",
                "spot":   None,
                "reason": (
                    f"significance {candidate.significance:.2f} "
                    f"below threshold {_DROP_THRESHOLD}"
                ),
            }

        # ── REINFORCE gate: existing record with matching summary? ────────────
        # A duplicate candidate for the same memory strengthens the existing
        # record rather than creating a second copy.
        if candidate.summary:
            try:
                from memory.vault_layer import lookup
                hits = lookup(candidate.summary[:60], max_results=1)
                if hits:
                    existing_spot = hits[0].get("spot", "")
                    if existing_spot:
                        from memory.consolidation_faculty import reinforce
                        reinforced = reinforce(existing_spot)
                        if reinforced:
                            return {
                                "action": "reinforce",
                                "spot":   existing_spot,
                                "reason": "existing record reinforced (duplicate candidate)",
                            }
            except Exception:
                pass  # lookup/reinforce failure → fall through to WRITE

        # ── WRITE ─────────────────────────────────────────────────────────────
        try:
            from memory.vault_layer import write_memory
            memory_type = _TYPE_TO_MEMORY_TYPE.get(candidate.proposed_type, "conversation")
            spot = write_memory(
                project=candidate.project,
                memory_type=memory_type,
                summary=candidate.summary or candidate.content[:200],
                deep_text=candidate.content,
                weight=max(1, min(9, candidate.proposed_weight)),
                tags=list(candidate.tags),
                experience_id=candidate.experience_id,
                epistemic_class=candidate.epistemic_class,
                source_ref=candidate.source_ref,
            )
            # WO-WKG-AUTO-POPULATE-001: after successful vault write, grow the WKG
            # if this candidate meets the epistemic gate (VERIFIED or SOURCE_ATTRIBUTED,
            # significance ≥ 0.6, recognisable semantic type).
            _maybe_write_wkg_claim(candidate, source_ref=spot)
            return {"action": "write", "spot": spot, "reason": "new record written"}
        except Exception as exc:
            _mark_vault_offline(str(exc))
            return {"action": "drop", "spot": None, "reason": f"vault error: {exc}"}


# ── WO-MEMORY-QUERY-TYPE-001: typed retrieval ────────────────────────────────

def retrieve(
    query: str,
    type_filter: str | None = None,
    max_results: int = 5,
) -> list[dict]:
    """
    Query the vault, optionally restricted to one memory type.

    type_filter — one of:
        episodic | semantic | procedural | emotional   (proposed_type names)
        conversation | learn | build | connect | ...   (internal memory_type names)
    When None, all types are returned (backwards-compatible with vault_layer.lookup).

    Returns a list of vault result dicts ordered by weight desc.
    """
    from memory.vault_layer import lookup
    return lookup(query, max_results=max_results, type_filter=type_filter)


# ── WO-WKG-AUTO-POPULATE-001: automatic WKG growth from live turns ────────────

import os as _os
import re as _re
import time as _time

_VAULT_OFFLINE_PATH = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "data", "vault_offline.json",
)


def _mark_vault_offline(reason: str) -> None:
    """WO-MEMORY-OFFLINE-SIGNAL-001: write sentinel so next turn's prompt carries a warning."""
    try:
        import json as _json
        _os.makedirs(_os.path.dirname(_VAULT_OFFLINE_PATH), exist_ok=True)
        with open(_VAULT_OFFLINE_PATH, "w", encoding="utf-8") as _fh:
            _json.dump({"ts": _time.time(), "reason": reason[:200]}, _fh)
    except Exception:
        pass

_WKG_MIN_TOPIC_LEN = 3
_WKG_MAX_TOPICS    = 20   # cap per turn to avoid hammering the graph


# Function words. Capitalised at the start of a sentence, they are
# indistinguishable from a proper noun by SHAPE alone — which is exactly how
# "What" and "Tell" became CONCEPT entities in the live store, and how a
# question like "what is the weather in Lisbon tomorrow" started matching an
# entity during SPG retrieval.
_WKG_STOP: frozenset[str] = frozenset({
    "the", "this", "that", "these", "those", "there", "their", "then", "than",
    "what", "when", "where", "which", "while", "who", "whom", "whose", "why",
    "how", "can", "could", "should", "would", "will", "shall", "may", "might",
    "must", "did", "does", "doing", "done", "has", "have", "had", "was",
    "were", "are", "and", "but", "for", "from", "with", "without", "into",
    "onto", "over", "under", "about", "any", "all", "some", "each", "every",
    "its", "his", "her", "our", "your", "my", "you", "him", "she", "they",
    "them", "tell", "show", "give", "make", "let", "please", "thanks",
    "thank", "okay", "yes", "not", "just", "also", "only", "very", "really",
    "maybe", "sure", "well", "now", "one", "two", "three", "good", "great",
    "nice", "hey", "hello", "need", "want", "like", "get", "got", "put",
})


# Characters that mean "this is code, not a concept". Found 2026-10-04 by
# auditing entities the running server created after the sentence-opener fix:
# 'Hello, {name}!', 'Hello, World!\n', '...', 'x = y;'. The quoted-phrase
# rule takes whatever sits between quotes, and a code sample is mostly
# quotes.
_CODE_CHARS = set("{}[]()<>;=\\|`$")


def _looks_like_code(text: str) -> bool:
    """True for a candidate that is a code fragment rather than a concept."""
    t = (text or "").strip()
    if not any(ch.isalpha() for ch in t):
        return True                       # '...' and friends — no letters at all
    if _CODE_CHARS & set(t):
        return True
    if "\\n" in t or "\\t" in t:      # escape sequences as literal characters
        return True
    return False


def _trim_stopwords(phrase: str) -> list[str]:
    """Drop leading and trailing function words from a capitalised run."""
    words = phrase.split()
    while words and words[0].lower() in _WKG_STOP:
        words.pop(0)
    while words and words[-1].lower() in _WKG_STOP:
        words.pop()
    return words


def _extract_wkg_topics(text: str) -> list[str]:
    """
    Cheap noun-phrase heuristic — same family as curiosity_faculty._extract_topics.

    Two defects fixed here on 2026-10-03, both visible in the live store:

      1. The single-token rule matched ANY capitalised word, so the first word
         of a sentence became an entity. "What is eLo?" created What; "Tell me
         about Chunk" created Tell.
      2. A word already inside a captured multi-word run was captured AGAIN on
         its own, so "Raspberry Pi" created both "Raspberry Pi" and
         "Raspberry" — a fragment competing with the thing it came from.

    Fixed at the writer. Filtering these out at retrieval instead would leave
    the store growing junk forever and hide it from whoever reads next.
    """
    candidates: list[str] = []
    # Words already carried by a multi-word phrase — not entities in their own
    # right. "Raspberry" is a fruit; "Raspberry Pi" is the thing being named.
    covered: set[str] = set()

    # Multi-word capitalised runs: "Raspberry Pi", "DISENELO Seams".
    # [A-Z][a-zA-Z]+ rather than [A-Z][a-z]+ so an all-caps brand token is
    # part of its own phrase — the old pattern dropped "DISENELO Seams".
    for m in _re.finditer(r"(?:[A-Z][a-zA-Z]+)(?:\s+[A-Z][a-zA-Z]+)+", text):
        words = _trim_stopwords(m.group(0).strip())
        if len(words) >= 2:
            candidates.append(" ".join(words))
            covered.update(w.lower() for w in words)
        # One survivor is left to the single-token rule below, and is
        # deliberately NOT marked covered, or it would vanish entirely.

    # Single CamelCase tokens: "TPU", "NLA", "eLo"
    for m in _re.finditer(r"\b[A-Z][a-zA-Z]{2,}\b", text):
        word = m.group(0).strip()
        low = word.lower()
        if low in _WKG_STOP or low in covered:
            continue
        # Console.WriteLine is one identifier, not two concepts. A dot with
        # no space beside it joins them; "Blender. Then Unity" has a space
        # and is two sentences, so both still get through.
        before = text[m.start() - 1] if m.start() > 0 else ""
        after  = text[m.end()] if m.end() < len(text) else ""
        if before == "." or after == ".":
            nxt = text[m.end() + 1: m.end() + 2]
            if before == "." or (after == "." and nxt and not nxt.isspace()):
                continue
        candidates.append(word)

    # Quoted phrases: "forward kinematics" — but a code sample is mostly
    # quotes, so a code-shaped quote is not a concept.
    for m in _re.finditer(r'"([^"]{3,40})"', text):
        phrase = m.group(1).strip()
        if not _looks_like_code(phrase):
            candidates.append(phrase)
    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        lc = c.lower()
        if lc not in seen and len(c) >= _WKG_MIN_TOPIC_LEN:
            seen.add(lc)
            result.append(c)
    return result[:_WKG_MAX_TOPICS]


def populate_wkg_from_turn(
    raw: str,
    response: str = "",
    project: str = "general",
    experience_id: str = "",
) -> list[str]:
    """
    WO-WKG-AUTO-POPULATE-001: grow the WKG from a live conversation turn.

    Extracts candidate entities from user message (raw) and eLo response,
    creates any that are absent from the WKG as "concept" entities.
    Does NOT record claims — entity creation is the minimum needed to give
    curiosity_faculty.detect_gap() something to find on the next turn.

    Returns list of entity_ids created this call. Fails quietly — never
    raises, never blocks the main response path.
    """
    created: list[str] = []
    try:
        from runtime.wkg_faculty import search_entities, create_entity

        # Combine user + eLo text; user message is more topically dense
        combined = (raw or "")[:400] + " " + (response or "")[:200]
        topics = _extract_wkg_topics(combined)

        for topic in topics:
            try:
                hits = search_entities(topic)
                if hits:
                    continue  # already known
                entity = create_entity(
                    entity_type="CONCEPT",
                    label=topic,
                    description=f"Mentioned in conversation (project: {project})",
                    source_ids=[experience_id] if experience_id else [],
                )
                created.append(entity["entity_id"])
            except Exception:
                continue  # single entity failure → skip, don't abort loop
    except Exception:
        pass
    return created


# ── WO-WKG-AUTO-POPULATE-001: vault→WKG claim writer ─────────────────────────

_WKG_SESSION_WRITES = 0
_WKG_MAX_SESSION_WRITES = 3
_WKG_GATE_EPISTEMIC = frozenset({"VERIFIED", "SOURCE_ATTRIBUTED"})
_WKG_GATE_SIGNIFICANCE = 0.6
_WKG_GATE_TYPES = frozenset({"semantic", "episodic", "emotional", "procedural"})

_DAVID_ENTITY_ID = "6de402af-8b5a-4238-950f-79bb1a00ab58"


def _maybe_write_wkg_claim(candidate: "MemoryCandidate", source_ref: str = "") -> None:
    """
    After a successful vault write, optionally write a WKG claim.
    Rate-limited to _WKG_MAX_SESSION_WRITES per session to avoid noise.
    Fails silently — never raises, never blocks.
    """
    global _WKG_SESSION_WRITES
    if _WKG_SESSION_WRITES >= _WKG_MAX_SESSION_WRITES:
        return
    if candidate.epistemic_class not in _WKG_GATE_EPISTEMIC:
        return
    if candidate.significance < _WKG_GATE_SIGNIFICANCE:
        return
    if candidate.proposed_type not in _WKG_GATE_TYPES:
        return
    try:
        import logging as _wkg_log
        from runtime.wkg_faculty import search_entities, create_entity, record_claim
        label = (candidate.summary or candidate.content[:80]).strip()
        if not label:
            return
        hits = search_entities(label[:60])
        if hits:
            obj_id = hits[0]["entity_id"]
        else:
            obj_entity = create_entity(
                entity_type="CONCEPT",
                label=label[:80],
                description=(
                    f"Auto-populated from vault write ({candidate.proposed_type}). "
                    f"Project: {candidate.project}."
                ),
                source_ids=[source_ref] if source_ref else [],
            )
            obj_id = obj_entity["entity_id"]
        record_claim(
            subject_entity_id=_DAVID_ENTITY_ID,
            relationship_type="ASSOCIATED_WITH",
            object_entity_id=obj_id,
            epistemic_class=candidate.epistemic_class,
            source_id=source_ref or candidate.source_faculty or "memory_faculty",
            experience_id=candidate.experience_id or None,
            confidence=min(1.0, candidate.significance + 0.1),
        )
        _WKG_SESSION_WRITES += 1
        _wkg_log.getLogger("wkg_auto").info(
            "WKG-AUTO-POPULATE: wrote claim (%d/%d) label=%r sig=%.2f",
            _WKG_SESSION_WRITES, _WKG_MAX_SESSION_WRITES,
            label[:50], candidate.significance,
        )
    except Exception:
        pass  # silent — never block vault write path
