# FROM_BUILDER — WKG-WRITE-FIX-001 Result Card
**Date:** 2026-09-05  
**WO:** WKG-WRITE-FIX-001 — P0 WKG Memory Write Path (INBOX directive)  
**Authority:** Board / Lead Architect 2026-09-05  
**Executed by:** Builder seat  

---

## Root Cause

`main.py` (David's terminal interface — the actual conversational path) had **no WKG write code**.

The WKG write block existed only in `server.py`'s `_process_turn()` handler, which serves HTTP requests from Blender Bridge. `main.py` never calls `_process_turn`. It has its own turn loop using `runtime.executive.decide` + `runtime.backend_router`. Those two paths are completely separate:

| Path | Entry | WKG write? |
|---|---|---|
| `python main.py` | David's terminal conversations | ❌ **ABSENT** |
| HTTP POST to server | Blender Bridge / Unity | ✅ Present |

Every David ↔ eLo conversation goes through `main.py`. The server.py WKG write was never reachable from conversational turns.

**Secondary confirmation:** `memory_engine._classify_memory_categories()` correctly matches real David turns. 406 of 943 existing interactions would have matched categories. The mechanism was always correct — it just wasn't wired into the code path David uses.

**Significance threshold:** `_DROP_THRESHOLD = 0.15` in `memory_faculty.py`. Not blocking WKG writes — the WKG write fires directly on category match (`if _wkg_cats:`) without going through MemoryFaculty. This threshold was irrelevant to the WKG defect.

---

## Fix Applied

**File:** `main.py` after line 373 (`print(f"\neLo: {response}\n")`)

Added WKG write block in the main turn loop, mirroring the server.py pattern exactly:

```python
# WKG write — fire when turn content matches meaningful categories
try:
    from core.memory_engine import _classify_memory_categories as _wkg_cat_classify
    _wkg_content = (raw + " " + response)[:1000]
    _wkg_cats = _wkg_cat_classify(_wkg_content)
    if _wkg_cats:
        from runtime.wkg_faculty import (
            search_entities as _wkg_search, create_entity as _wkg_create,
            record_claim as _wkg_record_claim, _load as _wkg_load,
        )
        _wkg_david = _wkg_search("David Charles")
        _wkg_david_id = _wkg_david[0]["entity_id"] if _wkg_david else _wkg_create(
            "PERSON", "David Charles", aliases=["David"],
            description="Creator of eLo and DISENELO")["entity_id"]
        _wkg_label = _wkg_cats[0].replace("_", " ")
        _wkg_topic = _wkg_search(_wkg_label)
        _wkg_topic_id = _wkg_topic[0]["entity_id"] if _wkg_topic else _wkg_create(
            "CONCEPT", _wkg_label,
            description=f"Topic from conversation: {raw[:80]}")["entity_id"]
        if "ASSOCIATED_WITH" in _wkg_load("relationship_types"):
            _wkg_record_claim(
                subject_entity_id=_wkg_david_id,
                relationship_type="ASSOCIATED_WITH",
                object_entity_id=_wkg_topic_id,
                epistemic_class="SOURCE_ATTRIBUTED",
                source_id="main_loop",
                confidence=0.7,
            )
except Exception:
    pass
```

---

## Before / After — Simulated with Real David Turns

**Before (entities.json):** `[]`  
**Before (claims.json):** `[]`  

Three real David messages from `interactions.json` (2026-09-01) run through the new write path:

| User input | Categories matched | Result |
|---|---|---|
| "Yo what you saying" | `identity`, `contextual_state` | WROTE: David + identity entity |
| "We building or we talking?" | `identity`, `projects` | WROTE: claim (David+identity reused) |
| "I feel like this idea actually has something real in it" | `identity`, `creative` | WROTE: claim |

**After (entities.json):**
```json
[
  {"label": "David Charles", "entity_type": "PERSON", ...},
  {"label": "identity", "entity_type": "CONCEPT", ...}
]
```

**After (claims.json):**
```json
[
  {"relationship_type": "ASSOCIATED_WITH", "epistemic_class": "SOURCE_ATTRIBUTED", "confidence": 0.7, "source_ids": ["main_loop"], ...},
  {"relationship_type": "ASSOCIATED_WITH", "epistemic_class": "SOURCE_ATTRIBUTED", "confidence": 0.7, "source_ids": ["main_loop"], ...},
  {"relationship_type": "ASSOCIATED_WITH", "epistemic_class": "SOURCE_ATTRIBUTED", "confidence": 0.7, "source_ids": ["main_loop"], ...}
]
```

---

## facts.json

Bristol entry: **ALREADY REMOVED** by prior session (current entry: "David is in London, currently Hackney Wick. [DAVID 2026-09-05]"). No change made.

---

## Test Run

**1556 passed, 2 pre-existing failures (moodpalette ×2), 0 new failures.**  
Pre-existing: `test_xi_ad2_parity_proven` (WAITING Unity data — excluded).

---

## What the WKG will contain going forward

Every conversational turn David has with eLo via `python main.py` that matches any of 12 category patterns (`identity`, `relationship`, `preferences`, `plans`, `commitments`, `projects`, `decisions`, `experiences`, `contextual_state`, `learning`, `creative`, `world`, `user`) will now produce:
- A `David Charles` PERSON entity (created once, reused)
- A topic CONCEPT entity (created per unique category label)
- A `ASSOCIATED_WITH` claim linking David to the topic

*Builder seat · 2026-09-05 · WKG-WRITE-FIX-001 · P0 CLOSED*
