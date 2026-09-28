"""
WKG Phase 1 — Wisdom Knowledge Graph faculty.
Read-only query interface + MemoryFaculty write stub (D-6, D-7).
MemoryFaculty is the sole caller of record_claim(). No other writer.

Store layout (JSON, Phase 1):
  memory/wkg/entities.json
  memory/wkg/claims.json
  memory/wkg/sources.json
  memory/wkg/relationship_types.json

RTR: RTR-034, RTR-035, RTR-036, RTR-037
WO:  WO-WKG-001 — David L3 AUTHORISED 2026-08-24
"""

import json
import os
import threading
import time
import uuid

_WKG_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "wkg")

# Serialises concurrent read-modify-write operations — _save() atomic rename
# only protects the file write itself; the full RMW cycle needs a lock.
_wkg_lock = threading.Lock()

_EPISTEMIC_CLASSES = frozenset({
    "VERIFIED",
    "HISTORICAL",
    "SOURCE_ATTRIBUTED",
    "SYMBOLIC",
    "HYPOTHESIS",
    "SPECULATIVE",
    "DISPUTED",
    "UNKNOWN",
})

_ENTITY_TYPES = frozenset({
    "PERSON",
    "CONCEPT",
    "PLACE",
    "SYMBOLIC",
    "CULTURAL",
    "NUMERICAL",
    "ASTRONOMICAL",
    "BIOLOGICAL",
})


# ── internal store I/O ────────────────────────────────────────────────────────

def _path(name: str) -> str:
    return os.path.join(_WKG_DIR, f"{name}.json")


def _load(name: str) -> list:
    p = _path(name)
    if not os.path.exists(p):
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(name: str, data: list) -> None:
    os.makedirs(_WKG_DIR, exist_ok=True)
    target = _path(name)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, target)


# ── read interface (D-6) ──────────────────────────────────────────────────────

def get_entity(entity_id: str) -> dict | None:
    for e in _load("entities"):
        if e["entity_id"] == entity_id:
            return e
    return None


def get_claims_about(entity_id: str) -> list:
    return [
        c for c in _load("claims")
        if c["subject_entity_id"] == entity_id or c["object_entity_id"] == entity_id
    ]


def get_claims_by_type(entity_id: str, relationship_type: str) -> list:
    return [
        c for c in get_claims_about(entity_id)
        if c["relationship_type"] == relationship_type
    ]


def search_entities(label: str) -> list:
    target = label.lower()
    return [
        e for e in _load("entities")
        if e["label"].lower() == target
        or target in [a.lower() for a in e.get("aliases", [])]
    ]


def get_epistemic_class(claim_id: str) -> str | None:
    for c in _load("claims"):
        if c["claim_id"] == claim_id:
            return c["epistemic_class"]
    return None


def get_source(source_id: str) -> dict | None:
    for s in _load("sources"):
        if s["source_id"] == source_id:
            return s
    return None


# ── entity creation (needed by MemoryFaculty to establish subjects/objects) ───

def create_entity(
    entity_type: str,
    label: str,
    aliases: list | None = None,
    description: str = "",
    source_ids: list | None = None,
) -> dict:
    if entity_type not in _ENTITY_TYPES:
        raise ValueError(f"Unknown entity_type: {entity_type!r}")
    entity = {
        "entity_id": str(uuid.uuid4()),
        "entity_type": entity_type,
        "label": label,
        "aliases": aliases or [],
        "description": description,
        "created_at": time.time(),
        "source_ids": source_ids or [],
    }
    with _wkg_lock:
        entities = _load("entities")
        entities.append(entity)
        _save("entities", entities)
    return entity


# ── write stub — MemoryFaculty sole writer (D-7) ─────────────────────────────

_MEMORY_TYPES = frozenset({
    "relational",    # from relationship_faculty — how eLo relates to a person/concept
    "episodic",      # from consolidation/reflection — a specific event or experience
    "lesson",        # from lesson_store — distilled actionable learning
    "semantic",      # entity facts, world knowledge
    "self_model",    # eLo's understanding of itself
    "emotional",     # significance-gated emotional memory
    "foundational",  # original intent / historical / identity-level
    "unclassified",  # existing claims, retroactively not reclassified
})


def record_claim(
    subject_entity_id: str,
    relationship_type: str,
    object_entity_id: str,
    epistemic_class: str,
    source_id: str,
    experience_id: str | None = None,
    confidence: float | None = None,
    contradicted_by: list | None = None,
    memory_origin: str | None = None,
    memory_type: str | None = None,
    significance_score: float | None = None,
    affective_snapshot: "dict | None" = None,
    cognitive_snapshot: "dict | None" = None,
    context_action: "str | None" = None,
) -> dict:
    """
    MemoryFaculty sole entry point for WKG claim creation.
    SOURCE_ATTRIBUTED != VERIFIED — enforced at this boundary.
    WO-DREAM-VERIFY-001: DREAM_SIMULATION origin blocked at write gate.
    """
    # WO-DREAM-VERIFY-001: enforce dream boundary — DREAM_SIMULATION must never auto-enter WKG
    if memory_origin is not None:
        try:
            from runtime.memory_origin import MemoryOrigin, is_auto_storable as _ias
            _origin_enum = MemoryOrigin(memory_origin)
            if not _ias(_origin_enum):
                import logging as _wkg_log
                _wkg_log.getLogger("wkg_faculty").warning(
                    "WKG write blocked: memory_origin=%r is not auto-storable (DREAM_SIMULATION boundary enforced)",
                    memory_origin,
                )
                raise ValueError(
                    f"WKG write blocked: origin {memory_origin!r} is not eligible for automatic storage. "
                    "DREAM_SIMULATION must pass significance gate (≥0.72) before entering the vault."
                )
        except ImportError:
            pass  # memory_origin module unavailable — fail open, log only

    if epistemic_class not in _EPISTEMIC_CLASSES:
        raise ValueError(f"Invalid epistemic_class: {epistemic_class!r}")
    rel_types = _load("relationship_types")
    if relationship_type not in rel_types:
        raise ValueError(f"Unknown relationship_type: {relationship_type!r}")
    if confidence is None:
        confidence = 1.0 if epistemic_class == "VERIFIED" else 0.5
    # WO-MEMORY-TYPES-001: classify claim at write time
    _mtype = "unclassified"
    if memory_type is not None and memory_type in _MEMORY_TYPES:
        _mtype = memory_type
    elif memory_type is not None:
        import logging as _mt_log
        _mt_log.getLogger("wkg_faculty").warning("Unknown memory_type %r — using 'unclassified'", memory_type)

    claim = {
        "claim_id": str(uuid.uuid4()),
        "subject_entity_id": subject_entity_id,
        "relationship_type": relationship_type,
        "object_entity_id": object_entity_id,
        "epistemic_class": epistemic_class,
        "source_ids": [source_id] if source_id else [],
        "confidence": confidence,
        "created_at": time.time(),
        "memory_type": _mtype,
        "significance_score": significance_score,
        "experience_id": experience_id,
        "contradicted_by": contradicted_by or [],
        # WO-MEMORY-TRACE-001: multidimensional episodic trace fields (optional, backward-compatible)
        "affective_snapshot": affective_snapshot or None,
        "cognitive_snapshot": cognitive_snapshot or None,
        "context_action":     context_action or None,
    }
    with _wkg_lock:
        claims = _load("claims")
        claims.append(claim)
        _save("claims", claims)
    return claim


def mark_contradicted(claim_id: str, contradicting_claim_id: str) -> None:
    with _wkg_lock:
        claims = _load("claims")
        for c in claims:
            if c["claim_id"] == claim_id:
                if contradicting_claim_id not in c["contradicted_by"]:
                    c["contradicted_by"].append(contradicting_claim_id)
        _save("claims", claims)
