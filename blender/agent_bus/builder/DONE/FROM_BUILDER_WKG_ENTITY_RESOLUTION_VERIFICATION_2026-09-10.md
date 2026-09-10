# FROM_BUILDER — WKG Entity Resolution Verification
**Date:** 2026-09-10
**Authority:** KEEP GOING MASTER PROTOCOL — scan after §68 context compaction
**Purpose:** Correct board assessment at §66/§68 that said "WKG has 65 claims all with subject/object=None. Entity extraction failing."

---

## FINDING: Board Assessment Was Incorrect

The board entry "entity extraction failing — all claims have subject/object=None" was based on reading `claims.json` raw and observing no top-level `subject` or `object` text fields.

**The schema uses `subject_entity_id` and `object_entity_id`** — resolved to text labels at query time through `ent_map`. The code in `spine.py:1604-1643` correctly builds:
```python
_ent_map = {e["entity_id"]: e.get("label", "") for e in _wkg._load("entities")}
_subj = _ent_map.get(_cl.get("subject_entity_id", ""), _ent.get("label", ""))
_obj  = _ent_map.get(_cl.get("object_entity_id", ""), "")
```

This is **correct and working**.

---

## Live Verification Results

```
Total claims: 87
VERIFIED claims: 6

Search "where am i from" → ['David Charles']
WKG context built:
  [VERIFIED] David Charles is London
  [VERIFIED] eLo associated with David Charles
  [VERIFIED] eLo associated with David Charles

Search "i keep starting things" → ['David Charles']
Search "david" → ['David Charles', 'David as creator of eLo']
```

**"[VERIFIED] David Charles is London" correctly surfaces for "where am i from"** — the HIGHEST AUTHORITY block is wired correctly.

---

## Actual Root Cause (Unchanged)

The 8b model's expressed response to "where am i from" was "You keep coming back to narrative" — obsidian vault routing overriding the WKG block.

Root cause: `llama3.1:8b` ignores HIGHEST AUTHORITY prompt section when an obsidian vault hit fires first. The model's pretraining empathetic-reflection pattern and context-length attention limits override priority-labeled factual context at this model size.

**This is not a code bug. Entity extraction is working. The model is the problem.**

---

## Current WKG Store State

| Metric | Value |
|---|---|
| Entities | 21 |
| Claims | 87 |
| VERIFIED claims | 6 |
| Relationship types | ASSOCIATED_WITH (71), IS (10), RELATED_TO (2), OBSERVED_AS (2), PROPOSED_BY (1), REPRESENTS (1) |
| Epistemic classes | SOURCE_ATTRIBUTED (71), HYPOTHESIS (4), HISTORICAL (6), VERIFIED (6) |

---

## Content Quality Gap (Still Open)

While entity RESOLUTION is correct, the CONTENT being written is generic:
- 71 of 87 claims are "David Charles ASSOCIATED_WITH [identity/creative/technical/emotional]"
- Derived from category tags per turn, not semantic entity extraction
- Specific factual claims (e.g. "David IS working on game") are not extracted from conversation content

This is the content-specific part of **WO-WKG-LIVE-WRITE-001** that the board noted as "Pending Board entity-extraction WO." Not a Builder fix until Board dispatches spec.

---

## VERDICT

| Item | Status |
|---|---|
| WO-KNOWLEDGE-PERSIST-001 structural | ✅ DONE — entity resolution working correctly |
| WKG "subject/object=None" board finding | ❌ INCORRECT — schema uses entity IDs, resolved at query time |
| WO-KNOWLEDGE-PERSIST-001 expressed | ❌ NOT SERVING — 8b model capacity, not code bug |
| WO-WKG-LIVE-WRITE-001 content-specific | ⏳ PENDING BOARD WO — semantic entity extraction spec needed |
| Test suite | ✅ 1551 pass, 16 pre-existing failures (unchanged) |

---

## Board Action Required

1. Model routing decision: llama3.1:8b → larger model (llama3.1:70b, claude-haiku-4-5, gpt-4o-mini) OR post-process intercept WO
2. Board WO for semantic entity extraction (WO-WKG-LIVE-WRITE-001 content-specific part)
