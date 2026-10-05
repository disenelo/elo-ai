"""
memory/unlearn_protocol.py — WO-MEMORY-UNLEARN-001

Four-stage unlearning pipeline: OLD → CONTRADICTED → RETIRED → NEW

Canonical ruling (David L3, 2026-09-27):
  "There should be a difference between forgetting and unlearning."

  Forgetting = memory becomes inaccessible (no longer readily retrievable).
  Unlearning = eLo actively changes an existing belief, association,
               procedure, or expectation.

Retire without deletion: every RETIRED item preserves the full retirement
record (original value, reason, date, replaced_by). No item is deleted.

Status vocabulary:
  CURRENT  — active canonical version (default retrieval target)
  RETIRED  — superseded; not served in normal retrieval; full record kept
  DRAFT    — candidate, not yet confirmed

Source: SOURCE_2026-09-27_DAVID_learning_people_relational_model.md
         SOURCE_2026-09-27_DAVID_unlearn_expanded_spec.md
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

_log = logging.getLogger(__name__)

# ── Status constants ───────────────────────────────────────────────────────────

STATUS_CURRENT  = "CURRENT"
STATUS_RETIRED  = "RETIRED"
STATUS_DRAFT    = "DRAFT"
STATUS_SUPERSEDED = "SUPERSEDED"   # alias for RETIRED in WO spec examples

# ── SPG instability threshold ──────────────────────────────────────────────────
# If the same item is retired and replaced more than this many times, SPG
# flags the entity/property as "unstable knowledge area — verify before using."

SPG_INSTABILITY_THRESHOLD = 3

# ── User-model belief confidence step ─────────────────────────────────────────
# Each contradicting data point from David reduces confidence by this amount.
# At or below CONFIDENCE_RETIREMENT_THRESHOLD the belief is RETIRED.

CONFIDENCE_DECREMENT = 0.25
CONFIDENCE_RETIREMENT_THRESHOLD = 0.25

# ── Storage path ──────────────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REGISTRY_PATH = os.path.join(_ROOT, "data", "unlearn_registry.json")


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class RetirementRecord:
    """
    The mandatory retirement record attached to every RETIRED item.
    Preserves: original value, reason, date, replaced_by, source.
    """
    retired_date:          str       # ISO timestamp
    reason:                str       # why it was retired
    contradicted_by:       str       # the evidence that triggered the retirement
    contradicted_by_source: str      # provenance of that evidence
    replaced_by_id:        Optional[str] = None   # ID of the new CURRENT item


@dataclass
class MemoryItem:
    """
    A single knowledge item in the unlearn registry.
    Works for semantic facts, user-model beliefs, project states, procedures.
    """
    id:                  str
    kind:                str                  # "fact", "association", "user_model", "project_state", "procedure"
    entity:              str                  # what this is about (entity, property key)
    property_key:        str
    value:               Any                  # the belief / fact / state / procedure
    status:              str                  # STATUS_CURRENT | STATUS_RETIRED | STATUS_DRAFT
    source:              str
    created_at:          str
    updated_at:          str
    retirement:          Optional[RetirementRecord] = None
    confidence:          float = 1.0          # user-model belief confidence (0.0–1.0)
    success_rate:        float = 1.0          # procedure success rate
    failure_count:       int   = 0            # procedure failure count
    state_history:       list  = field(default_factory=list)   # project-state sequence
    retirement_count:    int   = 0            # how many times this entity+property pair was RETIRED
    # contradiction tracking
    contradictions:      list  = field(default_factory=list)   # list of contradiction records


@dataclass
class ContradictionRecord:
    """Evidence that contradicted an existing belief."""
    date:      str
    evidence:  str
    source:    str


# ── Registry I/O ──────────────────────────────────────────────────────────────

def _load_registry() -> dict:
    try:
        with open(_REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"items": {}, "spg_unstable": []}
    except Exception as e:
        _log.warning("unlearn_protocol: registry load error: %s", e)
        return {"items": {}, "spg_unstable": []}


def _save_registry(registry: dict) -> None:
    os.makedirs(os.path.dirname(_REGISTRY_PATH), exist_ok=True)
    with open(_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _item_to_dict(item: MemoryItem) -> dict:
    d = asdict(item)
    if d.get("retirement") is None:
        d["retirement"] = None
    return d


def _dict_to_item(d: dict) -> MemoryItem:
    ret = d.pop("retirement", None)
    if ret:
        ret = RetirementRecord(**ret)
    return MemoryItem(**d, retirement=ret)


# ── Core API ──────────────────────────────────────────────────────────────────

def store(
    id: str,
    kind: str,
    entity: str,
    property_key: str,
    value: Any,
    source: str,
    status: str = STATUS_CURRENT,
    confidence: float = 1.0,
    replaces: Optional[str] = None,
) -> MemoryItem:
    """
    Store a new CURRENT knowledge item. Returns the stored MemoryItem.
    Does not check for contradictions — call detect_contradiction() first.
    """
    registry = _load_registry()
    now = _now_iso()
    item = MemoryItem(
        id=id,
        kind=kind,
        entity=entity,
        property_key=property_key,
        value=value,
        status=status,
        source=source,
        created_at=now,
        updated_at=now,
        confidence=confidence,
    )
    if replaces:
        item.state_history = [replaces]
    registry["items"][id] = _item_to_dict(item)
    _save_registry(registry)
    _log.debug("unlearn_protocol: stored %s (kind=%s status=%s)", id, kind, status)
    return item


def get(item_id: str) -> Optional[MemoryItem]:
    """Retrieve an item by ID regardless of status."""
    registry = _load_registry()
    d = registry["items"].get(item_id)
    if d is None:
        return None
    return _dict_to_item(dict(d))


def retrieve(
    entity: str,
    property_key: str,
    include_retired: bool = False,
) -> list[MemoryItem]:
    """
    Normal retrieval — returns only CURRENT items for entity+property_key.
    Set include_retired=True for historical queries.
    """
    registry = _load_registry()
    results = []
    for d in registry["items"].values():
        if d["entity"] != entity or d["property_key"] != property_key:
            continue
        if not include_retired and d["status"] != STATUS_CURRENT:
            continue
        results.append(_dict_to_item(dict(d)))
    return results


def detect_contradiction(
    entity: str,
    property_key: str,
    new_value: Any,
) -> Optional[MemoryItem]:
    """
    Check whether a new piece of information contradicts an existing CURRENT item.
    Returns the existing item if contradiction detected, None if no conflict.

    Detection: same entity + same property_key + different value.
    """
    current_items = retrieve(entity, property_key, include_retired=False)
    for item in current_items:
        if item.value != new_value:
            return item
    return None


def unlearn(
    old_item_id: str,
    new_value: Any,
    reason: str,
    contradicted_by: str,
    contradicted_by_source: str,
    new_item_id: Optional[str] = None,
    new_source: Optional[str] = None,
) -> tuple[MemoryItem, MemoryItem]:
    """
    Four-stage pipeline: OLD → CONTRADICTED → RETIRED → NEW.

    1. Load old item, set status=RETIRED, attach RetirementRecord.
    2. Store new CURRENT item referencing old.
    3. Check SPG instability threshold.
    4. Return (retired_item, new_item).

    Raises ValueError if old_item_id not found.
    """
    registry = _load_registry()
    old_dict = registry["items"].get(old_item_id)
    if old_dict is None:
        raise ValueError(f"unlearn: item {old_item_id!r} not found in registry")

    now = _now_iso()
    new_id = new_item_id or f"{old_item_id}__replacement_{now}"
    new_src = new_source or contradicted_by_source

    # ── Stage 1: RETIRE the old item ──────────────────────────────────────────
    retirement = RetirementRecord(
        retired_date=now,
        reason=reason,
        contradicted_by=contradicted_by,
        contradicted_by_source=contradicted_by_source,
        replaced_by_id=new_id,
    )
    old_dict["status"]     = STATUS_RETIRED
    old_dict["updated_at"] = now
    old_dict["retirement"] = asdict(retirement)
    old_dict["retirement_count"] = old_dict.get("retirement_count", 0) + 1
    registry["items"][old_item_id] = old_dict

    # ── Stage 2: Store the new CURRENT item ───────────────────────────────────
    new_item = MemoryItem(
        id=new_id,
        kind=old_dict["kind"],
        entity=old_dict["entity"],
        property_key=old_dict["property_key"],
        value=new_value,
        status=STATUS_CURRENT,
        source=new_src,
        created_at=now,
        updated_at=now,
        state_history=old_dict.get("state_history", []) + [old_item_id],
    )
    registry["items"][new_id] = _item_to_dict(new_item)

    # ── Stage 3: SPG instability check ────────────────────────────────────────
    total_retirements = _count_retirements(
        registry, old_dict["entity"], old_dict["property_key"]
    )
    if total_retirements >= SPG_INSTABILITY_THRESHOLD:
        unstable_key = f"{old_dict['entity']}::{old_dict['property_key']}"
        if unstable_key not in registry.get("spg_unstable", []):
            registry.setdefault("spg_unstable", []).append(unstable_key)
            _log.warning(
                "unlearn_protocol: SPG instability flag — %s (retired %d times)",
                unstable_key, total_retirements,
            )

    _save_registry(registry)

    retired_item = _dict_to_item(dict(old_dict))
    _log.info(
        "unlearn_protocol: %r RETIRED → %r CURRENT (reason=%s)",
        old_item_id, new_id, reason,
    )
    return retired_item, new_item


def _count_retirements(registry: dict, entity: str, property_key: str) -> int:
    """Count how many times entity+property has been retired."""
    count = 0
    for d in registry["items"].values():
        if (d["entity"] == entity and d["property_key"] == property_key
                and d["status"] == STATUS_RETIRED):
            count += 1
    return count


def unlearn_false_association(
    trigger: str,
    old_response: str,
    context_rule: str,
    reason: str,
    source: str,
) -> tuple[MemoryItem, MemoryItem]:
    """
    Retire a fixed trigger-response association and replace with a
    context-dependent rule.

    Example: "safe" → "farewell" (fixed) → "evaluate context" (context-dependent).
    """
    old_id = f"assoc__{trigger.replace(' ', '_')}"
    registry = _load_registry()

    if old_id not in registry["items"]:
        now = _now_iso()
        registry["items"][old_id] = _item_to_dict(MemoryItem(
            id=old_id,
            kind="association",
            entity=trigger,
            property_key="response",
            value=old_response,
            status=STATUS_CURRENT,
            source=source,
            created_at=now,
            updated_at=now,
        ))
        _save_registry(registry)

    new_id = f"assoc__{trigger.replace(' ', '_')}__context_rule"
    return unlearn(
        old_item_id=old_id,
        new_value=context_rule,
        reason=reason,
        contradicted_by=f"Context-dependent evaluation required; fixed mapping is wrong.",
        contradicted_by_source=source,
        new_item_id=new_id,
        new_source=source,
    )


def contradict_user_model(
    belief_id: str,
    contradiction_evidence: str,
    source: str,
) -> MemoryItem:
    """
    Reduce confidence weight on a user-model belief by CONFIDENCE_DECREMENT.
    If confidence falls to or below CONFIDENCE_RETIREMENT_THRESHOLD, RETIRE it.

    Returns the updated (or retired) item.
    """
    registry = _load_registry()
    d = registry["items"].get(belief_id)
    if d is None:
        raise ValueError(f"contradict_user_model: belief {belief_id!r} not found")

    now = _now_iso()
    contradiction = {
        "date": now,
        "evidence": contradiction_evidence,
        "source": source,
    }
    d.setdefault("contradictions", []).append(contradiction)
    new_confidence = round(d.get("confidence", 1.0) - CONFIDENCE_DECREMENT, 4)
    d["confidence"] = max(0.0, new_confidence)
    d["updated_at"] = now
    registry["items"][belief_id] = d
    _save_registry(registry)

    if d["confidence"] <= CONFIDENCE_RETIREMENT_THRESHOLD:
        retired, _ = unlearn(
            old_item_id=belief_id,
            new_value=None,
            reason=f"User-model belief confidence depleted by repeated contradictions (confidence={d['confidence']})",
            contradicted_by=contradiction_evidence,
            contradicted_by_source=source,
            new_item_id=f"{belief_id}__retired",
            new_source=source,
        )
        return retired

    return _dict_to_item(dict(d))


def update_project_state(
    entity: str,
    property_key: str,
    old_item_id: str,
    new_state: str,
    reason: str,
    source: str,
    new_item_id: Optional[str] = None,
) -> tuple[MemoryItem, MemoryItem]:
    """
    Transition a project-state entry: RETIRE old state, store new CURRENT.
    Preserves full state_history. Only the latest state is CURRENT.
    """
    return unlearn(
        old_item_id=old_item_id,
        new_value=new_state,
        reason=reason,
        contradicted_by=f"State changed: {new_state}",
        contradicted_by_source=source,
        new_item_id=new_item_id or f"{entity}__{property_key}__state_{_now_iso()}",
        new_source=source,
    )


def retire_failed_procedure(
    procedure_id: str,
    failure_reason: str,
    replacement_value: Any,
    source: str,
    new_procedure_id: Optional[str] = None,
) -> tuple[MemoryItem, MemoryItem]:
    """
    Retire a procedure that has repeatedly failed; store the replacement CURRENT.
    Increments failure_count on the old procedure before retiring it.
    """
    registry = _load_registry()
    d = registry["items"].get(procedure_id)
    if d is None:
        raise ValueError(f"retire_failed_procedure: procedure {procedure_id!r} not found")

    d["failure_count"] = d.get("failure_count", 0) + 1
    now = _now_iso()
    d["updated_at"] = now
    registry["items"][procedure_id] = d
    _save_registry(registry)

    return unlearn(
        old_item_id=procedure_id,
        new_value=replacement_value,
        reason=f"Procedure failed (failure_count={d['failure_count']}): {failure_reason}",
        contradicted_by=failure_reason,
        contradicted_by_source=source,
        new_item_id=new_procedure_id or f"{procedure_id}__replacement",
        new_source=source,
    )


def is_spg_unstable(entity: str, property_key: str) -> bool:
    """Return True if entity+property_key is flagged as SPG unstable."""
    registry = _load_registry()
    key = f"{entity}::{property_key}"
    return key in registry.get("spg_unstable", [])


def clear_registry_for_test() -> None:
    """Reset the registry. Test use only."""
    _save_registry({"items": {}, "spg_unstable": []})
