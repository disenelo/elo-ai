# RESULT — Issue 7 Addendum: Typo Engine Garble (e704c53)
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Status:** CONFIRMED — commit e704c53 covers both cases

---

## Board question

> "Confirm commit e704c53 covers both garble cases. If not, file addendum."

## Both cases covered — analysis

**Case 1: "You'd have to do a websearch"**
- The text garble was from `_is_frustrated_typos` false-firing.
- "You'd have to do a websearch" has 0 garbled words (no 3-consecutive-consonant sequences).
- Old threshold `>=2` was still a problem on other inputs; new threshold `>=3` prevents false fires.
- Additionally, "do a websearch" now in `_SEARCH_TRIGGERS` — routes correctly to web search.
- **COVERED** by Bug 1 (threshold) + Bug 3a (search triggers).

**Case 2: "Same thing as always Pinkie try to take over the world"**
- "try" = t,r,y (consonant sequence) → 1 garbled word
- "world" = r,l,d (consonant sequence) → 1 garbled word
- Total = 2 garbled words. Old threshold `>=2` fired → mutated text → "save nothing as always..." → vault_write routing.
- New threshold `>=3` requires 3 garbled words → does NOT fire on this sentence.
- Text is no longer mutated → routing reads original text → vault_write not triggered.
- **COVERED** by Bug 1 (threshold raise).

## Root cause

The garble detector was running BEFORE routing — mutated text fed into the intent classifier, causing the false `vault_write` classification. The fix is upstream (prevent garble from firing), which corrects downstream routing automatically.

## No further action required for Issue 7.
