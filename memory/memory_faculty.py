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
            )
            return {"action": "write", "spot": spot, "reason": "new record written"}
        except Exception as exc:
            _mark_vault_offline(str(exc))
            return {"action": "drop", "spot": None, "reason": f"vault error: {exc}"}


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


def _extract_wkg_topics(text: str) -> list[str]:
    """Cheap noun-phrase heuristic — same family as curiosity_faculty._extract_topics."""
    candidates: list[str] = []
    # Multi-word capitalised runs: "Raspberry Pi", "NeoPixel ring"
    for m in _re.finditer(r"(?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+)+", text):
        candidates.append(m.group(0).strip())
    # Single CamelCase tokens: "TPU", "NLA", "eLo"
    for m in _re.finditer(r"\b[A-Z][a-zA-Z]{2,}\b", text):
        candidates.append(m.group(0).strip())
    # Quoted phrases: "forward kinematics"
    for m in _re.finditer(r'"([^"]{3,40})"', text):
        candidates.append(m.group(1).strip())
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
