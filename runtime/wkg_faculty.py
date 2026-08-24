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
import time
import uuid

_WKG_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "wkg")

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
    with open(_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


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
    entities = _load("entities")
    entities.append(entity)
    _save("entities", entities)
    return entity


# ── write stub — MemoryFaculty sole writer (D-7) ─────────────────────────────

def record_claim(
    subject_entity_id: str,
    relationship_type: str,
    object_entity_id: str,
    epistemic_class: str,
    source_id: str,
    experience_id: str | None = None,
    confidence: float | None = None,
    contradicted_by: list | None = None,
) -> dict:
    """
    MemoryFaculty sole entry point for WKG claim creation.
    SOURCE_ATTRIBUTED != VERIFIED — enforced at this boundary.
    """
    if epistemic_class not in _EPISTEMIC_CLASSES:
        raise ValueError(f"Invalid epistemic_class: {epistemic_class!r}")
    rel_types = _load("relationship_types")
    if relationship_type not in rel_types:
        raise ValueError(f"Unknown relationship_type: {relationship_type!r}")
    if confidence is None:
        confidence = 1.0 if epistemic_class == "VERIFIED" else 0.5
    claim = {
        "claim_id": str(uuid.uuid4()),
        "subject_entity_id": subject_entity_id,
        "relationship_type": relationship_type,
        "object_entity_id": object_entity_id,
        "epistemic_class": epistemic_class,
        "source_ids": [source_id] if source_id else [],
        "confidence": confidence,
        "created_at": time.time(),
        "experience_id": experience_id,
        "contradicted_by": contradicted_by or [],
    }
    claims = _load("claims")
    claims.append(claim)
    _save("claims", claims)
    return claim


def mark_contradicted(claim_id: str, contradicting_claim_id: str) -> None:
    claims = _load("claims")
    for c in claims:
        if c["claim_id"] == claim_id:
            if contradicting_claim_id not in c["contradicted_by"]:
                c["contradicted_by"].append(contradicting_claim_id)
    _save("claims", claims)
