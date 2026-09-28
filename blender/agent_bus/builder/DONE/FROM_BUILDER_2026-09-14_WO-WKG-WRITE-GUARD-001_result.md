# FROM BUILDER → BOARD — WO-WKG-WRITE-GUARD-001 Result
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-WKG-WRITE-GUARD-001.md
**Authority:** David L3 — 2026-09-14
**Ruling enforced:** WKG writes = David's words or eLo's own experience. Never eLo's responses about David.

---

## A. Cleanup confirmation

```
Claims: 267 → 262 (5 removed)
Entities: 95 → 93 (2 removed)
```

(WO expected 266→261; actual was 267→262 — 1 additional claim had accumulated since WO was authored. 5 claims + 2 entities removed as specified.)

---

## B. Hole 1 guard test — `faculty answered:` blocked

Input passed to `extract_and_record_claims()`:
```
"Turn context mentions eLo-Planet game; faculty answered: That sounds like a solid plan, yeah."
```

Result:
```
wkg_faculty WARNING wkg_faculty: contamination signal in write candidate — skipped. text='Turn context mentions eLo-Planet game; faculty answered: That sounds like a soli'
Guard 1 result: []  (expected [])
```

Returns immediately. No write. Warning logged verbatim. ✓

---

## C. Hole 2 guard test — `source_ids: []` blocked

Attempted to write a STATED claim with `source_id=""`:

```
wkg_faculty WARNING wkg_faculty: Guard 2 — David-statement claim type 'STATED' blocked: source_id is empty
Guard 2 result: blocked with ValueError — WKG write blocked: 'STATED' claim requires non-empty source_id (WO-WKG-WRITE-GUARD-001 Guard 2)
```

Raises ValueError, callers' try/except blocks catch — no write. ✓

---

## D. Call site verification

`server.py:5003`:
```python
_wkg_claims = _wkg_extract(
    raw,
    source_id=f"turn:{_action}:{_turn_type}",
    significance_score=_wkg_sig,
)
```

The argument is `raw` — David's actual input text. Not `_response`, not `_expressed_text`, not any assembled context string. ✓

Movement call site `server.py:3219` passes `_mv_text` (eLo's own movement experience — valid as eLo self-state). ✓

`extract_faculty_claims()` is disabled for all LLM backends (`server.py:5026-5032`). The David-WORKING_ON claim inside `extract_faculty_claims()` that generated the `"Turn context mentions X; faculty answered: Y"` pattern has been **removed** from the function — only eLo-STATED claims remain. The David claim block was lines 522-543 in the pre-fix file.

---

## E. Clean write test

Input: `"I want to finish the book before the year ends."`
Source ID: `turn:answer:DEEP:test-guard-evidence-E`

Result:
```
claim_id: 7b7e33f5-bcbb-41a6-ac09-6d6c2b5c99d8
relationship_type: DECIDED
source_ids: ['turn:answer:DEEP:test-guard-evidence-E']
claim_text: 'I want to finish the book before the year ends'
source_ids populated: OK
```

Correct claim type (DECIDED for "I want to..."), source_id populated, no contamination. ✓

---

## F. 5-turn battery — no new contamination

```
[greeting:TIER0]  wrote 0 claim(s)
[greeting:TIER0]  wrote 0 claim(s)
[question:LIGHT]  wrote 1 claim(s)
[statement:DEEP]  wrote 2 claim(s)
[complex:DEEP]    wrote 1 claim(s)

Total: 264 → 268 (+4)
Contaminated new claims: 0
5-turn battery: CLEAN — no contaminated claims, no empty source_ids
```

✓

---

## Code changes applied

**`runtime/wkg_faculty.py`:**

1. Added `import logging as _log` at module level.

2. **Guard 1** — top of `extract_and_record_claims()`: if text contains any contamination signal (`"faculty answered:"`, `"turn context mentions"`, `"i can sense that you"`, `"it sounds like you're"`, `"i see that you're"`), log warning and return `[]`.

3. **Guard 2** — top of `record_claim()`: if `source_id` is empty and `relationship_type` is in `{"STATED", "PREFERS", "FEELS", "DECIDED", "CORRECTED", "WORKING_ON"}`, log warning and raise `ValueError`. Callers' try/except suppress, no write occurs.

4. **Root fix** — removed David-WORKING_ON claim block from `extract_faculty_claims()`. This was the actual contamination source: it wrote `claim_text=f"Turn context mentions {plabel}; faculty answered: {text[:80]}"` where `text = faculty_text` (eLo's response) as a claim about David. Now only eLo-STATED claims remain in that function. Comment added: "WO-WKG-WRITE-GUARD-001: David-WORKING_ON claims are NOT written from faculty output."

---

## DoD checklist

- [x] 7 contaminated entries removed (5 claims + 2 entities)
- [x] `faculty answered:` guard active — confirmed blocked, warning logged, no write
- [x] `source_ids: []` guard active — David-statement claims blocked without source
- [x] Call site confirmed: `extract_and_record_claims()` receives `raw` only
- [x] 5-turn battery clean post-fix

---

*Builder · 2026-09-14*
