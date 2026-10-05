# WO-MEMORY-UNLEARN-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Commit:** de6dfc8  
**Status:** COMPLETE — 28/28 tests pass

---

## Gap closed

Without an unlearning protocol, eLo accumulated contradictory knowledge with no mechanism to distinguish current from deprecated. Both the deprecated API method and the current one would live in the store with no status distinction. Retrieval was unreliable.

---

## What was built

### `memory/unlearn_protocol.py`

**Four-stage pipeline**: OLD → CONTRADICTED → RETIRED → NEW

**Status constants**: `CURRENT`, `RETIRED`, `DRAFT`, `SUPERSEDED`

**Core functions:**
- `store(id, kind, entity, property_key, value, source)` — creates CURRENT item
- `get(item_id)` — retrieve by ID regardless of status
- `retrieve(entity, property_key, include_retired=False)` — CURRENT-only default (AC-1)
- `detect_contradiction(entity, property_key, new_value)` — same entity+property+different value (AC-2)
- `unlearn(old_item_id, new_value, reason, contradicted_by, source)` → (retired_item, new_item) — writes mandatory RetirementRecord; SPG instability check (AC-2, AC-4, AC-5, AC-10)

**Specialised unlearning:**
- `unlearn_false_association(trigger, old_response, context_rule, reason, source)` — retires fixed trigger→response; stores context-dependent rule (AC-6)
- `contradict_user_model(belief_id, contradiction_evidence, source)` — reduces confidence by `CONFIDENCE_DECREMENT`; RETIRES at `CONFIDENCE_RETIREMENT_THRESHOLD` (AC-7)
- `update_project_state(entity, property_key, old_item_id, new_state, reason, source)` — preserves `state_history`; only latest CURRENT (AC-8)
- `retire_failed_procedure(procedure_id, failure_reason, replacement_value, source)` — increments `failure_count`; RETIRES old; stores replacement CURRENT (AC-9)
- `is_spg_unstable(entity, property_key)` — True when retirement_count ≥ `SPG_INSTABILITY_THRESHOLD` (default 3) (AC-5)

**Storage**: `data/unlearn_registry.json` — JSON registry of all items; `spg_unstable` list.

**RetirementRecord** (attached to every RETIRED item):
```
retired_date, reason, contradicted_by, contradicted_by_source, replaced_by_id
```
No item is RETIRED without this record (AC-10).

---

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC-1 | RETIRED items not served in normal retrieval | ✅ |
| AC-2 | Contradiction → old RETIRED, new CURRENT (not both CURRENT) | ✅ |
| AC-3 | RETIRED items retrievable via include_retired=True | ✅ |
| AC-4 | Contradiction record (contradicted_by, source, retired_date) on every RETIRED item | ✅ |
| AC-5 | SPG instability flag at threshold | ✅ |
| AC-6 | Fixed trigger-response RETIRED; context-dependent rule CURRENT; fixed mapping not served | ✅ |
| AC-7 | User-model confidence reduced per contradiction; RETIRED at threshold; not in future retrieval | ✅ |
| AC-8 | Project-state history maintained; only latest CURRENT | ✅ |
| AC-9 | Failed procedure RETIRED; replacement CURRENT; normal retrieval returns CURRENT only | ✅ |
| AC-10 | Every RETIRED item carries full retirement record | ✅ |

---

## Tests

`tests/test_wo_memory_unlearn_001.py` — 28/28:
- TestStatusConstants (3): constants, thresholds
- TestStoreAndRetrieve (4): store, get, CURRENT-only retrieval, historical retrieval
- TestContradictionDetection (3): detect, no-conflict same-value, no-conflict no-existing
- TestUnlearn (5): RETIRED+CURRENT pipeline, record stored, get by ID, full record fields, raises on missing
- TestSPGInstability (2): flag at threshold, not below threshold
- TestFalseAssociation (2): retires fixed mapping, not served after retirement
- TestUserModelBelief (3): confidence reduced, RETIRED at threshold, not in normal retrieval
- TestProjectState (3): state_history, old RETIRED, only one CURRENT
- TestProcedureRetirement (3): RETIRED+CURRENT, normal retrieval, failure record on retired
