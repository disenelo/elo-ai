# RESULT — WO-RELATIONSHIPS-001: David relationship profile in g_ctx
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Commit:** 716d335
**Status:** DONE — 5 tests pass

---

## What was built

### `runtime/wkg_faculty.py` — `get_relationship_profile(entity_id, *, max_facts=12)`

Queries all SOURCE_ATTRIBUTED/VERIFIED claims where David is the SUBJECT entity. Filters out:
- UUID-only labels (orphaned object entity IDs where the entity was never created)
- Category-label stubs from the old extractor (`description.startswith("Topic from conversation:"` / `"Topic from interaction:"`)
- Known generic junk labels (`identity`, `projects`, `world`, `plans`, etc.)
- Duplicate labels

Returns formatted block:
```
[WHAT I KNOW ABOUT DAVID CHARLES]
- eLo robot design constraints
- David as creator of eLo
- David's favourite material to sew with is barkcloth from Uganda
- David works in Hackney Wick
...
```

### `server.py` — wired at g_ctx assembly (before turn-specific WKG retrieval)

```python
# WO-RELATIONSHIPS-001: David relationship profile — persistent facts from WKG
from runtime.wkg_faculty import get_relationship_profile as _get_rel_profile
_DAVID_WKG_ID = "6de402af-8b5a-4238-950f-79bb1a00ab58"
_rel_profile = _get_rel_profile(_DAVID_WKG_ID, max_facts=12)
if _rel_profile:
    g_ctx = f"{g_ctx}\n{_rel_profile}" if g_ctx else _rel_profile
```

This fires every turn. David's accumulated WKG facts are always in the system prompt regardless of
what the current turn is about. Previously: facts were only injected when the current turn's keywords
happened to match `retrieve_wkg_context_items(raw)`.

---

## Live state of David's profile (2026-10-06)

```
[WHAT I KNOW ABOUT DAVID CHARLES]
- eLo robot design constraints
- David as creator of eLo
- David's friend told me the project is stupid
- David's memory is a lot more foggy than yours
- David's favourite material to sew with is barkcloth from Uganda
- David works in Hackney Wick
- David is working on something tricky today
```

7 facts. Will grow as `wkg_fact_extractor` captures new statements from future sessions.

---

## Tests — 5 pass

| Test | Assertion |
|------|-----------|
| REL-1 | profile is non-empty for David's entity_id |
| REL-2 | barkcloth backfill fact is present |
| REL-3 | contaminated stubs ("identity", "projects", etc.) do NOT appear |
| REL-4 | UUID-only labels do NOT appear |
| REL-5 | fact written now appears in profile immediately (no cache lag) |

---

## Causal chain addition

Before this WO:
```
EXPERIENCE → wkg_fact_extractor → WKG claim → retrieve_wkg_context_items(raw)
   ↓ only fires if current turn query matches claim keywords ↓
```

After this WO:
```
EXPERIENCE → wkg_fact_extractor → WKG claim → get_relationship_profile()
   ↓ fires EVERY turn, independent of current turn keywords ↓
→ [WHAT I KNOW ABOUT DAVID CHARLES] in system prompt
→ MISSING-FACT rule checks [RELATIONSHIP & PERSPECTIVE] before refusing
→ eLo responds with David's known facts without being told again
```

---

## PERSON entity status

`entity_id: 6de402af-8b5a-4238-950f-79bb1a00ab58`
`entity_type: PERSON` — already existed with full description (Fulham/Brixton/Hackney Wick/dcharles@disenelo.com).
No new entity creation needed — the PERSON node was complete.

---

## Outstanding

WO-WKG-CONTAMINATION-CLEANUP-001 remains blocked on David authorization. The contamination filter
in `get_relationship_profile` works around the contaminated entries at read time. A cleanup pass
would remove them from claims.json and entities.json at write time.
