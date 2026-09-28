# FROM BUILDER — WO-WKG-LIVE-WRITE-001 — DONE

**Date:** 2026-09-12 (§91 continued)
**Status:** DONE
**Files changed:** `main.py` (line 395-403)

---

## Problem

219 WKG claims, 87 with empty `claim_text`. 80 of these were high-confidence (conf=0.7) ASSOCIATED_WITH stubs. These stubs triggered the false-SUFFICIENT path in `coverage_check()` that returned "I know something's there — not enough to say it right yet." as if eLo had knowledge on the topic.

---

## Root Cause

`main.py:396` — `_wkg_record_claim()` called with NO `claim_text` argument:

```python
_wkg_record_claim(
    subject_entity_id=_wkg_david_id,
    relationship_type="ASSOCIATED_WITH",
    object_entity_id=_wkg_topic_id,
    epistemic_class="SOURCE_ATTRIBUTED",
    source_id="main_loop",
    confidence=0.7,
    # ← claim_text missing
)
```

This writes a structural edge (David → ASSOCIATED_WITH → topic) with no narrative content. Every main.py conversation turn that matched a memory category was writing one of these stubs. Source: `source_ids: ["main_loop"]`. 71 stubs accumulated from prior sessions.

---

## Fix

Added `claim_text` to the write:

```python
claim_text=f"David discussed {_wkg_label}: {raw[:120]}",
```

Future ASSOCIATED_WITH writes now carry the first 120 chars of the user's turn as the claim summary — enough for `coverage_check()` to build a real response if it fires SUFFICIENT.

---

## Impact

- Future WKG writes are no longer empty stubs.
- The 71 existing stubs remain in claims.json — they're harmless (excluded from hc_with_text SUFFICIENT gate) but not cleaned (WO-WKG-CONTAMINATION-CLEANUP-001, David L3 required).
- `coverage_check()` `hc_with_text` fix (same session) ensures stubs can't trigger SUFFICIENT even if they remain.

*Builder · 2026-09-12 · §91*
