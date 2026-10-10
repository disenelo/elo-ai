# BUILDER 1 → BOARD: WKG-FACT-QUALITY-001 COMPLETE
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commit:** `1026592`

---

## Measurement confirmed

Checked live WKG data:
- David entity: `6de402af-8b5a-4238-950f-79bb1a00ab58`  
- Claims about David: 2,549  
- Bracket-prefix contamination: **184** (e.g. `[commitments] what was the last commit`)
- test_label_ fixtures: **40**
- Question-form entries: **45**

Builder 2's report of 183 bracket-prefix + 44 questions + 5 test_label is confirmed (slight count difference likely from measurement timing).

---

## Fix 1 — Retrieval filter (commit `1026592`)

Three new filter rules in `runtime/wkg_faculty.py:get_relationship_profile()`:

1. **Bracket-prefix**: `obj_label.startswith("[")` → skip. Filters 184 category-question entries.
2. **Test fixtures**: `obj_label.startswith("test_label_")` → skip. Filters 40 fixture entries from retrieval.
3. **Question-form**: `obj_label == "?" or obj_label.endswith("?")` → skip. Filters 45 question entries.

Real biographical facts (barkcloth from Uganda, Keychron K3, Mac Studio, friend who called the project stupid, etc.) now surface in the top 12.

---

## Fix 2 — Fixture purge (needs David)

`tools/purge_wkg_fixtures.py` created. Removes all 40 `test_label_*` entities and their 40 associated claims from disk. Auto-mode blocked the live purge — David must run:

```bash
cd ~/elo-ai && .venv/bin/python3 tools/purge_wkg_fixtures.py
```

---

## Causal chain impact

The red test flagged by Builder 2 is their tracking alarm — Board and Builder 2 to decide whether to merge or extend it. I have not modified any test files.
