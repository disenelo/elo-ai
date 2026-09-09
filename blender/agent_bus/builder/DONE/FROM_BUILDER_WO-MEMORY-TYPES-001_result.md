# FROM_BUILDER — WO-MEMORY-TYPES-001
**Status:** DONE — memory_type enum already in record_claim(); AT-1 and AT-2 confirmed live
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Intent

Distinguish memory types in WKG claim records so eLo's memory is not a flat undifferentiated list.

---

## Implementation — already in place

`runtime/wkg_faculty.py:140-148`:
```python
_MEMORY_TYPES = frozenset({
    "relational",    # from relationship_faculty
    "episodic",      # from consolidation/reflection — a specific event or experience
    "lesson",        # from lesson_store — distilled actionable learning
    "semantic",      # entity facts, world knowledge
    "self_model",    # eLo's understanding of itself
    "emotional",     # significance-gated emotional memory
    "foundational",  # original intent / historical / identity-level
    "unclassified",  # existing claims, retroactively not reclassified
})
```

`record_claim()`:
```python
_mtype = "unclassified"
if memory_type is not None and memory_type in _MEMORY_TYPES:
    _mtype = memory_type
```

The `claim` dict includes: `"memory_type": _mtype` and `"significance_score": significance_score`.

---

## AT-1 — relational claim ✅

```python
record_claim(
    subject_entity_id=ELO_ID,
    relationship_type='RELATED_TO',
    object_entity_id=DAVID_ID,
    epistemic_class='VERIFIED',
    source_id='AT',
    memory_type='relational',
)
# → claim_id: acc73abb... memory_type: relational
```

---

## AT-2 — episodic claim ✅

```python
record_claim(
    subject_entity_id=ELO_ID,
    relationship_type='ASSOCIATED_WITH',
    object_entity_id=DAVID_ID,
    epistemic_class='VERIFIED',
    source_id='AT',
    memory_type='episodic',
    significance_score=0.75,
)
# → claim_id: 8882e8cf... memory_type: episodic significance_score: 0.75
```

---

## Backfill — existing claims

11 claims exist with `memory_type: "unclassified"` — per WO spec, existing claims are not retroactively reclassified (too risky). The `"unclassified"` type is a valid enum value for legacy claims.

All NEW claims written via `record_claim()` with an explicit `memory_type` argument will be classified at write time.
