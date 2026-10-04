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


def search_entities(label: str, *, include_deprecated: bool = False) -> list:
    """
    Entities matching `label`, by label or alias.

    Deprecated entities are skipped. Retirement affects DISCOVERY only —
    get_entity() and get_claims_about() still resolve them, because a claim
    recorded against an entity really was recorded and dropping it would be
    rewriting history to tidy the index.
    """
    target = label.lower()
    return [
        e for e in _load("entities")
        if (include_deprecated or not e.get("deprecated"))
        and (e["label"].lower() == target
             or target in [a.lower() for a in e.get("aliases", [])])
    ]


def deprecate_entity(
    entity_id: str,
    reason: str,
    *,
    superseded_by: str | None = None,
    undo: bool = False,
) -> bool:
    """
    Retire an entity WITHOUT deleting it. Returns True if a row changed.

    Four entities in the live store are artefacts of the extractor defect
    fixed in WO-WKG-JUNK-001 — "Tell", "What", "You" (sentence openers
    matched as capitalised words) and "Raspberry" (a fragment of "Raspberry
    Pi" captured again on its own). They are not knowledge; "What" matched
    the question "what is the weather in Lisbon tomorrow" during SPG
    retrieval, which is how they were found.

    The writer no longer produces them, and deleting rows from eLo's memory
    is not how this project corrects things — information is superseded, not
    removed. The row stays, with a reason, a timestamp, and for a fragment
    the id of the entity that supersedes it.

    Reversible: a wrong call must not be a one-way door.
    """
    changed = False
    with _wkg_lock:
        entities = _load("entities")
        for e in entities:
            if e.get("entity_id") != entity_id:
                continue
            if undo:
                for k in ("deprecated", "deprecated_reason", "deprecated_at",
                          "superseded_by"):
                    e.pop(k, None)
            else:
                e["deprecated"] = True
                e["deprecated_reason"] = reason
                e["deprecated_at"] = time.time()
                if superseded_by:
                    e["superseded_by"] = superseded_by
            changed = True
            break
        if changed:
            _save("entities", entities)
    return changed


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

    # Outside the lock deliberately: SPG does its own file I/O, and holding
    # the WKG lock across it would serialise every claim write behind a graph
    # save for no benefit. The claim is already durable by this point.
    _link_claim_to_spg(claim)
    return claim


def all_claims() -> list:
    """
    Every claim. The accessor memory/spg_faculty.py needs.

    It was reopening memory/wkg/claims.json by a path of its own, which meant
    two modules holding independent ideas of where the claims live — and the
    reader silently missing anything the writer put somewhere else. One
    accessor, one answer.
    """
    return _load("claims")


def _link_claim_to_spg(claim: dict) -> None:
    """
    Give every claim an SPG node under its OWN claim_id.

    spg_faculty.query_spg_entities() ranks entities by the SPG significance of
    their claims, joining node.id to claim["claim_id"]. On the live store that
    join returned ZERO for 225 nodes against 2226 claims, so the sort was a
    no-op and retrieval ordering was text relevance pretending to be
    significance.

    Nothing had ever created a node under a real claim_id. record_claim() —
    the sole claim writer — never touched SPG; update_spg_from_claims() was
    built for this and has no callers; and the one producer that did run mints
    `turn-<ms>` ids that are not claim_ids and never could be.

    So the hook goes HERE, at the single point every claim passes through.
    Per-call-site wiring would cover one writer and leave the next one
    orphaning nodes again.

    Significance comes from significance_score when the caller scored the
    claim, otherwise from confidence — VERIFIED defaults to 1.0 and
    SOURCE_ATTRIBUTED to 0.5, which is a real ordering. Defaulting to 0.0
    would make an unscored claim indistinguishable from an unranked one.

    The content hash is built from the triple because claims.json stores no
    claim text — which is exactly why the 214 orphaned legacy nodes can never
    be re-linked by hash, only abandoned.

    Fire and forget: a broken graph must never cost a memory.
    """
    try:
        from memory.spg_faculty import add_node_for_claim

        significance = claim.get("significance_score")
        if significance is None:
            significance = claim.get("confidence")
        triple = " ".join((
            str(claim.get("subject_entity_id") or ""),
            str(claim.get("relationship_type") or ""),
            str(claim.get("object_entity_id") or ""),
        ))
        add_node_for_claim(
            claim_id=claim["claim_id"],
            claim_text=triple,
            significance=float(significance if significance is not None else 0.5),
        )
    except Exception:
        pass


def mark_contradicted(claim_id: str, contradicting_claim_id: str) -> None:
    with _wkg_lock:
        claims = _load("claims")
        for c in claims:
            if c["claim_id"] == claim_id:
                if contradicting_claim_id not in c["contradicted_by"]:
                    c["contradicted_by"].append(contradicting_claim_id)
        _save("claims", claims)
