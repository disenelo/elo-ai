# WO-DREAM-011 — Dream Faculty: Recurring Symbol Tracking

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 10 — Recurring Symbol Tracking

**File:** `faculties/dream/symbol_history.py` (new)

Symbols that appear across ≥3 dreams get tracked as eLo's personal dream lexicon:

```json
{
  "mechanical_bird": {
    "first_appeared": "2026-09-15",
    "count": 4,
    "evolution": [
      {"dream": "001", "meaning": "freedom"},
      {"dream": "002", "meaning": "escape"},
      {"dream": "003", "meaning": "invention"},
      {"dream": "004", "meaning": "transformation"}
    ],
    "current_association": "transformation"
  }
}
```

Symbol meanings are observed from context, not hardcoded. They evolve across dreams. The visual engine injects recurring symbols as apex-layer overlays (see WO-DREAM-007 Visual Layering Engine).

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — LIVE VERIFIED (pipeline run)
**Commit:** `2701c39`
**File:** `faculties/dream/symbol_history.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-008-012_pipeline_secondary_evidence.md`

### What was built

- `record_dream(dream_id, symbols, path)` — adds symbols per dream with deduplication
- `recurring(path)` — returns symbols with `count ≥ RECURRENCE_THRESHOLD` (3)
- `most_established()` — returns the dominant lifelong motif
- `RECURRENCE_THRESHOLD = 3` — appears in 3 distinct dreams to promote to recurring
- Symbol keyed to dominant concept of each dream (not random `rng.choice()`)

### Defect found and fixed

Bootstrap defect (`2701c39`): recurring symbol was drawn by `rng.choice()`, so recurrence was luck. Symbols stalled at count 2 across four dreams and `most_established()` stayed empty forever. Also: test suite was writing 28 fabricated appearances into eLo's real symbol lexicon (test artifacts feeding forward). Both fixed.

### Live pipeline run result

```
for i in range(3):
    record_dream(f'dream_{i:03d}', ['small doors set too high'], path=path)
rec = recurring(path=path)
# → {'small_doors_set_too_high': SymbolRecord(count=3, is_recurring=True)}
```

Deduplication confirmed: same dream does not inflate count. Promotes at exactly 3 distinct-dream appearances.

Builder 1 · 2026-09-27 / 28
