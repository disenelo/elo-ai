# FROM BUILDER — WO-067-WRITE-PATH Memory Category Tagging

**WO:** WO-067-WRITE-PATH — Memory category tagging  
**Priority:** P1 · **Authority:** David L3, 2026-08-30  
**Date:** 2026-08-30  
**Commit:** `cf28758`

---

## Result

**6/6 AT PASS**

```
✅ AT-1: 'What should I wear for the weather?' → categories=['contextual_state'] (includes contextual_state)
✅ AT-2: 'I've decided to go with the pneumatic joint design for the robot.' → categories=['projects', 'decisions']
✅ AT-3: 'I prefer direct replies, no padding' → categories=['preferences']
✅ AT-4: 'How are you? I'm doing well.' → categories=[] (no meaningful categories — correct)
✅ AT-5: interactions.json record has memory_categories=['contextual_state']
✅ AT-6: vault_layer.lookup('wear') → found clothing turn in vault
```

---

## Root cause fixed (critical bug)

`server.py` was passing `experience_id=_mem_xid` to `MemoryCandidate()`, which has no such field.
This caused `TypeError` on every turn → caught by `except Exception: pass` → **nothing was being written to vault from the server.py write path.** This is why the vault had only 20 records despite many sessions.

---

## What shipped

**`core/memory_engine.py`:**
- Extended `_CATEGORY_SIGNALS` from 5 categories to 10: `identity · relationship · preferences · plans · commitments · projects · decisions · experiences · contextual_state · learning` (David L3 governing principle: "meaningful continuity, not a transcript database")
- Added `write_interaction(user, response, categories, ...)` — appends tagged turns to `interactions.json` for categorised recall

**`server.py`:**
- Removed `experience_id=_mem_xid` from `_MemCand()` call (bug fix)
- Added `_cat_classify()` call per turn
- Non-empty categories → significance 0.25 → 0.55 (above `_OBS_THRESHOLD=0.42`), summary prefixed with `[category]`
- Tagged turns also written to `interactions.json` (AT-5)

**`tests/test_wo067_write_path_memory_tagging.py`** — 6 ATs as specified.

---

## Vault write path now active

Every turn goes through `MemoryFaculty.submit()` successfully (bug removed). Contextual turns (clothing, decisions, preferences) hit significance=0.55 — above the obsidian threshold (0.42). Generic turns stay at 0.25 (written but lower weight).

*Builder / Board — 2026-08-30*
